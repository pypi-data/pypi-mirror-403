from peegy.processing.pipe.definitions import InputOutputProcess
from peegy.processing.tools.epoch_tools.transform import de_epoch
from peegy.processing.tools.epochs_processing_tools import et_mean, et_frequency_mean2, et_snr_in_rois
from peegy.processing.tools.detection.definitions import TimeROI, TimeROIValue
from peegy.definitions.eeg_definitions import EegPeak
from peegy.definitions.channel_definitions import Domain
from peegy.processing.statistics.definitions import FmpTest, TestType
from peegy.definitions.tables import Tables
from peegy.processing.statistics.eeg_statistic_tools import hotelling_t_square_test, f_test
from peegy.processing.tools.eeg_epoch_operators import w_mean, effective_sampling_size
import numpy as np
import pandas as pd
import os
import pyfftw
from typing import List
import astropy.units as u
from peegy.tools.units.unit_tools import set_default_unit
from PyQt5.QtCore import QLibraryInfo
from numba import njit
from scipy.signal import windows
os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = QLibraryInfo.location(QLibraryInfo.PluginsPath)


class EpochData(InputOutputProcess):
    def __init__(self, input_process=InputOutputProcess,
                 pre_stimulus_interval: u.quantity.Quantity | None = None,
                 post_stimulus_interval: u.quantity.Quantity | None = None,
                 baseline_correction_ini_time: u.quantity.Quantity | None = None,
                 baseline_correction_end_time: u.quantity.Quantity | None = None,
                 event_code: List[float] | None = None,
                 base_line_correction: bool = False,
                 at: type(u.Quantity) | None = None,
                 demean: bool = True,
                 events_mask: int | None = None,
                 use_window: bool = False,
                 window_type: str = 'tukey',
                 window_arguments: tuple = (0.1, ),
                 **kwargs):
        """
        This class will take a n*m matrix into a k*m*p, where p (number of trials) is determined by the number of
        triggers used to split the data
        :param input_process: InputOutputProcess Class
        :param pre_stimulus_interval: the length (in sec) of the data to be read before the trigger
        :param post_stimulus_interval: the length (in sec) of the data to be read after the trigger
        :param event_code: list of floats indicating the event codes to be used to epoch the data
        :param base_line_correction: whether to perform baseline correction or not. The initial and final time points
        used to compute the baseline correction are given by baseline_correction_ini_time and
        baseline_correction_end_time
        :param baseline_correction_ini_time: initial time (relative to trigger) to compute the mean for baseline
        correction. For example, if trigger is at zero, and you want to compute the baseline correction from -200 ms you
        can set baseline_correction_ini_time = -200 * u.ms
        :param baseline_correction_end_time: end time (relative to trigger) to compute the mean for baseline
        correction. For example, if trigger is at zero, and you want to compute the baseline correction
        between -200 * ms and -50 ms, you can set baseline_correction_ini_time = -200 * u.ms and
        baseline_correction_end_time = -50 * u.ms
        :param at: an array of with times to use as event marks. When at is not empty, these time stamps will be used
        to epoch the data. Event codes from the input_process will be ignored.
        :param demean: whether to remove the mean from each epoch
        :param events_mask: integer value used to masker triggers codes. This is useful to ignore triggers inputs above
        a particular value. For example, if only the first 8 trigger inputs were used (max decimal value is 255), in a
        system with 16 trigger inputs, then the masker could be set to 255 to ignore any trigger from trigger inputs 9
        to 16
        :param use_window: If True a scipy window will be used.
        :param window_type: string indicating the window that will be applied
        :param window_arguments: a tuple with additional parameters to be passed to windows.get_window function
        :param kwargs: extra parameters to be passed to the superclass
        """
        super(EpochData, self).__init__(input_process=input_process, **kwargs)
        self.pre_stimulus_interval = set_default_unit(pre_stimulus_interval, u.s)
        self.post_stimulus_interval = set_default_unit(post_stimulus_interval, u.s)
        self.event_code = event_code
        self.base_line_correction = base_line_correction
        self.demean = demean
        self.events_mask = events_mask
        self.baseline_correction_ini_time = baseline_correction_ini_time
        self.baseline_correction_end_time = baseline_correction_end_time
        self.at = at
        self.use_window = use_window
        self.window_type = window_type
        self.window_arguments = window_arguments

    def transform_data(self):
        if self.event_code is None:
            print('no event code was provided')
            return
        data = self.input_node.data
        baseline_correction_ini_time = 0.0 * u.s if self.baseline_correction_ini_time is None else \
            self.baseline_correction_ini_time
        pre_stimulus_interval = 0.0 * u.s if self.pre_stimulus_interval is None else self.pre_stimulus_interval
        self.input_node.events.mask = self.events_mask
        if self.at is None:
            events_index = self.input_node.events.get_events_index(code=self.event_code,
                                                                   fs=self.input_node.fs)
        else:
            events_index = self.input_node.x_to_samples(self.at)
        post_stimulus_interval = self.post_stimulus_interval
        baseline_correction_end_time = 0.0 * u.s if self.baseline_correction_end_time is None else \
            self.baseline_correction_end_time
        if self.post_stimulus_interval is None:
            post_stimulus_interval = np.percentile(np.diff(events_index), 90) / self.input_node.fs

        # ensure sufficient data for baseline-correction
        if baseline_correction_ini_time < 0:
            pre_stimulus_interval = np.maximum(pre_stimulus_interval, np.abs(baseline_correction_ini_time))
        if baseline_correction_end_time > 0:
            post_stimulus_interval = np.maximum(post_stimulus_interval, baseline_correction_end_time)

        buffer_size = int((post_stimulus_interval + pre_stimulus_interval) * self.input_node.fs)
        events_index = events_index - int((pre_stimulus_interval - self.input_node.x_offset) * self.input_node.fs)
        total_indexes = events_index.size
        # ensure positive index
        _idx_to_keep = np.logical_and(events_index >= 0,
                                      events_index + buffer_size <= self.input_node.data.shape[0])
        events_index = events_index[_idx_to_keep]
        possible_indexes = events_index.size
        if possible_indexes < total_indexes:
            print("{:} events ignored as data length won't fit epoch length".format(
                total_indexes - possible_indexes))
        print('There are {:} events with code {:}'.format(events_index.shape[0], self.event_code))
        epochs = extract_epochs(data=data, buffer_size=buffer_size, events_index=events_index)
        epochs = epochs * data.unit
        print('A total of {:} epochs were obtained using event code {:}, each with a duration of {:.3f}'.format(
            epochs.shape[2],
            self.event_code,
            (buffer_size / self.input_node.fs).to(u.s)))
        if self.demean:
            epochs = epochs - np.mean(epochs, axis=0)
        if self.base_line_correction:
            _ini_sample = max(0, int((pre_stimulus_interval + baseline_correction_ini_time) * self.input_node.fs))
            _end_sample = max(_ini_sample + 1,
                              int((baseline_correction_end_time - baseline_correction_ini_time) * self.input_node.fs) +
                              _ini_sample)
            epochs = epochs - np.mean(epochs[_ini_sample:_end_sample, :, :], axis=0)
        if self.use_window:
            window = windows.get_window((self.window_type, *self.window_arguments), epochs.shape[0])[:, None, None]
            epochs = epochs * window
        self.output_node.data = epochs
        self.output_node.x_offset = pre_stimulus_interval
        self.output_node.events = None


@njit
def extract_epochs(data: type(np.array) | None = None,
                   events_index: type(np.array) | None = None,
                   buffer_size: int | None = None):
    epochs = np.zeros((buffer_size, data.shape[1], events_index.size), dtype=np.float32)
    for i, _event in enumerate(events_index):
        epochs[:, :, i] = data[_event:_event + buffer_size, :]
    return epochs


class RejectEpochs(InputOutputProcess):
    def __init__(self, input_process=InputOutputProcess,
                 std_threshold: float | None = None,
                 rejection_percentage: float | None = None,
                 rejection_threshold: u.quantity.Quantity | None = None,
                 max_percentage_epochs_above_threshold: float = 1.0,
                 **kwargs):
        """
        This class will epochs where a given threshold has been exceeded. If any channel exceeds the threshold at a
        given trial, that particular epoch will be removed from all channels. This is done to keep the data in a single
        matrix.
        :param input_process: InputOutputProcess Class
        :param std_threshold: float indicating the threshold in terms of standard deviations to remove epochs
        :param max_percentage_epochs_above_threshold: if a single channel has more than max_epochs_above_threshold
        (percentage) epochs, the channel will be removed.
        :param rejection_percentage indicates the percentage of epochs to remove.
        above the threshold, the channel will be removed.
        :param rejection_threshold: indicates level above which epochs will be rejected
        :param kwargs: extra parameters to be passed to the superclass
        """
        super(RejectEpochs, self).__init__(input_process=input_process, **kwargs)
        self.std_threshold = set_default_unit(std_threshold, u.dimensionless_unscaled)
        self.rejection_threshold = set_default_unit(rejection_threshold, u.uV)
        self.max_percentage_epochs_above_threshold = max_percentage_epochs_above_threshold
        self.rejection_percentage = rejection_percentage

    def transform_data(self):
        _data = self.input_node.data
        _idx_to_keep = np.ones((_data.shape[2], ), dtype=bool)
        # first we check if a channel needs to be removed  based on max_percentage_epochs_above_threshold
        if self.max_percentage_epochs_above_threshold < 1.0:
            _max_amp = np.max(np.abs(_data), axis=0)
            _epoch_limit = int(self.max_percentage_epochs_above_threshold * _data.shape[2])
            _n_noisy_epochs_per_channel = np.sum(_max_amp > self.rejection_threshold, axis=1)
            _ch_to_remove = np.argwhere(_n_noisy_epochs_per_channel > _epoch_limit).flatten()
            print('Removing a total of {:} channels with more than {:} epochs above the threshold {:}'.format(
                np.sum(_ch_to_remove.size), _epoch_limit, self.rejection_threshold))
            # we assign data to output node to perform a clean delete of bad channels
            self.output_node.data = _data
            self.output_node.delete_channel_by_idx(_ch_to_remove)
            _data = self.output_node.data

        # now using the new data we find and remove the x % of ephocs with the highest peak
        if self.rejection_percentage is not None:
            _max_amp = np.max(np.abs(_data), axis=0)
            rejection_thr = np.quantile(np.max(_max_amp, axis=0), 1 - self.rejection_percentage)
            to_keep = np.max(_max_amp, axis=0, keepdims=True) < rejection_thr
            _idx_to_keep = np.logical_and(_idx_to_keep, np.all(to_keep, axis=0).flatten())
            print('{:} epochs out of {:} will be kept based on a {:} percentage rejection'.format(
                np.all(to_keep, axis=0).sum(),
                _data.shape[2],
                self.rejection_percentage))

        if self.rejection_threshold is not None:
            # now we find epochs indexes across channels which are above threshold
            _max_amp = np.max(np.abs(_data), axis=0)
            to_keep = _max_amp <= self.rejection_threshold
            _idx_to_keep = np.logical_and(_idx_to_keep, np.all(to_keep, axis=0).flatten())
            print('{:} epochs out of {:} will be kept based on a {:} rejection threshold'.format(
                np.all(to_keep, axis=0).sum(),
                _data.shape[2],
                self.rejection_threshold))

        if self.std_threshold is not None:
            _epochs_std = np.std(_data, axis=0)
            _n_noisy_epochs_across_channels = np.sum(np.greater(_epochs_std,
                                                                (np.mean(_epochs_std, 1) +
                                                                 self.std_threshold * np.std(_epochs_std, 1)).reshape(
                                                                    -1, 1)),
                                                     axis=0,
                                                     keepdims=True)
            to_keep = _n_noisy_epochs_across_channels == 0
            _n_std_to_remove = np.sum(~to_keep)
            _std_percentage = 100 * _n_std_to_remove / _data.shape[2]
            _idx_to_keep = np.logical_and(_idx_to_keep, np.all(to_keep, axis=0).flatten())
            print('Rejecting a total of {:} epochs, corresponding to {:.2f}% above {:} std'.format(
                np.sum(~_idx_to_keep), _std_percentage, self.std_threshold))
        # print some information and reject epochs
        _p_rejected = 100 * (1 - np.sum(_idx_to_keep) / _data.shape[2])
        print('Percentage of total epochs rejected {:.2f}%'.format(_p_rejected))
        if _p_rejected == 100:
            print('All epochs were rejected!! check rejection level '
                  '(currently {:}) and run again'.format(self.rejection_percentage))

        self.output_node.data = _data[:, :, _idx_to_keep.flatten()]


class RemoveBadChannelsEpochsBased(InputOutputProcess):
    def __init__(self, input_process=InputOutputProcess,
                 threshold: float = 300.0,
                 max_epochs_above_threshold: float = 0.5,
                 **kwargs):
        """
        This class will remove a channel based on epochs data. If any channel has more than max_epochs_above_threshold
        percentage of epochs above a given threshold, this channel will be removed.
        :param input_process: InputOutputProcess Class
        :param threshold: the threshold to reject channels with too much noise
        :param max_epochs_above_threshold: if a single channel has more than max_epochs_above_threshold (percentage)
        epochs, the channel will be removed.
        :param kwargs: extra parameters to be passed to the superclass
        """
        super(RemoveBadChannelsEpochsBased, self).__init__(input_process=input_process, **kwargs)
        self.threshold = threshold
        self.max_epoch_above_threshold = max_epochs_above_threshold

    def transform_data(self):
        _data = self.input_node.data
        _max_amp = np.max(np.abs(_data), axis=0)
        _epoch_limit = int(self.max_epoch_above_threshold * _data.shape[2])
        _n_noisy_epochs_per_channel = np.sum(_max_amp > self.threshold, axis=1)
        _ch_to_remove = np.argwhere(_n_noisy_epochs_per_channel > _epoch_limit).flatten()
        print('Removing a total of {:} channels with more than {:} epochs above the threshold {:}'.format(
            np.sum(_ch_to_remove.size), _epoch_limit, self.threshold))
        # we assign data to output node to perform a clean delete of bad channels
        self.output_node.data = _data
        self.output_node.delete_channel_by_idx(_ch_to_remove)


class SortEpochs(InputOutputProcess):
    def __init__(self, input_process=InputOutputProcess,
                 ascending=False,
                 sort_by: str = 'std',
                 **kwargs):
        """
        This class will sort epochs by maximum amplitude across all trials.
        :param input_process: InputOutputProcess Class
        :param sort_by: string indicating the method to sort ephocs, either 'std' for standard deviation or 'amp' to use
        maximum amplitude per epoch.
        :param kwargs: extra parameters to be passed to the superclass
        """
        super(SortEpochs, self).__init__(input_process=input_process, **kwargs)
        self.ascending = ascending
        self.sort_by = sort_by

    def transform_data(self):
        _data = self.input_node.data
        if self.sort_by == 'amp':
            _measured_value = np.max(np.abs(_data), axis=0)
            _idx_sorted = np.argsort(_measured_value, axis=1)
        if self.sort_by == 'std':
            _measured_value = np.std(_data, axis=0)
            _idx_sorted = np.argsort(_measured_value, axis=1)
        sorted_data = np.zeros(_data.shape) * _data.unit
        if self.ascending:
            for _ch in range(_idx_sorted.shape[0]):
                sorted_data[:, _ch, :] = _data[:, _ch, _idx_sorted[_ch, :][::-1]]
        else:
            for _ch in range(_idx_sorted.shape[0]):
                sorted_data[:, _ch, :] = _data[:, _ch, _idx_sorted[_ch, :]]

        print('Sorting epochs by {:}'.format(self.sort_by))
        self.output_node.data = sorted_data


class AverageEpochs(InputOutputProcess):
    def __init__(self, input_process=InputOutputProcess,
                 weighted_average: bool = True,
                 weight_across_epochs: bool = True,
                 n_tracked_points: int | None = None,
                 block_size: int = 10,
                 roi_windows: np.array([TimeROI]) = np.array([TimeROI()]),
                 **kwargs):
        """
        This InputOutputProcess average epochs
        :param input_process: InputOutputProcess Class
        :param weighted_average: if True, weighted average will be used
        :param weight_across_epochs: if True, weights are computed across epochs (as in Elbeling 1984) otherwise weights
        are computed within epoch (1 / variance across time)
        :param n_tracked_points: number of equally spaced points over time used to estimate residual noise and weights
        :param block_size: number of trials that will be stacked together to estimate the residual noise
        :param roi_windows: time windows used to perform some measures (snr, rms)
        :param kwargs: extra parameters to be passed to the superclass
        """
        super(AverageEpochs, self).__init__(input_process=input_process, **kwargs)
        self.weighted_average = weighted_average
        self.n_tracked_points = n_tracked_points
        self.block_size = block_size
        self.roi_windows = roi_windows
        self.weight_across_epochs = weight_across_epochs

    def transform_data(self):
        block_size = max(self.block_size, 5)
        if self.n_tracked_points is None:
            self.n_tracked_points = self.input_node.data.shape[0]
        samples_distance = int(max(self.input_node.data.shape[0] // self.n_tracked_points, 1))
        w_ave, w, rn, cum_rn, w_fft, n, wb, nb, _ = \
            et_mean(epochs=self.input_node.data,
                    block_size=block_size,
                    samples_distance=samples_distance,
                    weighted=self.weighted_average,
                    weight_across_epochs=self.weight_across_epochs
                    )
        points_per_sweep = int(self.input_node.data.shape[0] / samples_distance)
        # compute noise degrees of freedom based on the effective degrees of freedoms
        dof = effective_sampling_size(w)[0, :]
        rn_dof = dof * points_per_sweep
        self.output_node.data = w_ave
        self.output_node.rn = rn
        self.output_node.cum_rn = cum_rn
        self.output_node.w = w
        self.output_node.n = n
        self.output_node.rn_df = rn_dof
        _stats = self.get_snr_table()
        self.output_node.statistical_tests = Tables(table_name=TestType.f_test_time,
                                                    data=_stats,
                                                    data_source=self.name)
        self.output_node.roi_windows = self.roi_windows

    def get_snr_table(self):
        final_snr, _, f_values = et_snr_in_rois(data_node=self.output_node,
                                                roi_windows=self.roi_windows)
        tests = []
        for _iw, _roi in enumerate(self.roi_windows):
            _samples = _roi.get_roi_samples(data_node=self.output_node)
            _ini = _samples[0]
            _end = _samples[-1]
            _label = None
            if self.roi_windows is not None:
                _label = _roi.label

            f_critic, df_num, df_den, p_value = f_test(
                f_values=f_values[:, _iw],
                df_numerator=5 * np.ones(self.output_node.data.shape[1]),
                df_noise=self.output_node.rn_df,
                alpha=self.output_node.alpha)

            for _idx_ch, _ch in enumerate(self.output_node.layout):
                df_den = self.output_node.rn_df
                tests.append(
                    FmpTest(df_1=df_num[_idx_ch],
                            df_2=df_den[_idx_ch],
                            f=f_values[_idx_ch, _iw],
                            f_critic=f_critic[_idx_ch],
                            p_value=p_value[_idx_ch],
                            rn=self.output_node.rn[_idx_ch],
                            snr=final_snr[_idx_ch, _iw],
                            ini_time=self.output_node.samples_to_x([_ini])[0],
                            end_time=self.output_node.samples_to_x([_end])[0],
                            n_epochs=self.output_node.n,
                            channel=_ch.label,
                            label=_label).__dict__
                )
        out = pd.DataFrame(tests)
        return out


class AverageEpochsFrequencyDomain(InputOutputProcess):
    def __init__(self,
                 input_process=InputOutputProcess,
                 n_tracked_points: int | None = None,
                 block_size: int = 10,
                 test_frequencies: type(np.array) | None = None,
                 n_fft: int | None = None,
                 weighted_average: bool = True,
                 weighted_frequency_domain: bool = False,
                 weight_across_epochs: bool = True,
                 weight_frequencies: type(np.array) | None = None,
                 delta_frequency: u.Quantity = 5. * u.Hz,
                 power_line_frequency: u.Quantity = 50 * u.Hz,
                 n_jobs: int = 1,
                 **kwargs):
        """
        This InputOutputProcess average epochs in the frequency domain
        :param input_process: InputOutputProcess Class
        :param n_tracked_points: number of equally spaced points over time used to estimate residual noise and weights
        :param block_size: number of trials that will be stack together to estimate the residual noise
        :param test_frequencies: numpy array with frequencies that will be used to compute statistics (Hotelling test)
        :param weighted_average: bool indicating if weighted average is to be used, otherwise standard average is used
        :param weighted_frequency_domain: boll indicating if the weghts are compute in the time or frequency domain
        :param weight_across_epochs: if True, weights are computed across epochs (as in Elbeling 1984) otherwise weights
        are computed within epoch (1 / variance across time)
        :param weight_frequencies: numpy array with frequencies that will be used to estimate weights when
        weighted_average is activated
        :param delta_frequency: frequency size around each test_frequencies to estimate weights and noise
        :param power_line_frequency: frequency of local power line frequency. This will be used to prevent using
        this frequency or its multiples when performing frequency statistics
        :param n_jobs: number of CPUs to compute fft
        :param kwargs: extra parameters to be passed to the superclass
        """
        super(AverageEpochsFrequencyDomain, self).__init__(input_process=input_process, **kwargs)
        self.n_tracked_points = n_tracked_points
        self.block_size = block_size
        self.test_frequencies = set_default_unit(test_frequencies, u.Hz)
        self.weight_frequencies = set_default_unit(weight_frequencies, u.Hz)
        self.weighted_average = weighted_average
        self.weighted_frequency_domain = weighted_frequency_domain
        self.weight_across_epochs = weight_across_epochs
        self.delta_frequency = set_default_unit(delta_frequency, u.Hz)
        self.power_line_frequency = set_default_unit(power_line_frequency, u.Hz)
        self.n_jobs = n_jobs

    def transform_data(self):
        # average processed data across epochs including frequency average
        if self.weighted_frequency_domain:
            if self.weight_frequencies is None and self.test_frequencies is not None:
                print('No specific frequency provided to estimate weights in the frequency-domain. Pooling across '
                      'test frequencies {:}. Results may be inaccurate if test frequencies contain no '
                      'relevant signal'.format(self.test_frequencies.to_string()))
                self.weight_frequencies = self.test_frequencies

        exact_frequencies = np.array([]) * u.dimensionless_unscaled
        freq_samples = np.array([]) * u.dimensionless_unscaled
        if self.weighted_frequency_domain and self.weighted_frequency_domain and self.weight_frequencies is not None:
            w_ave, snr, rn, by_freq_rn, by_freq_snr, w_fft, w, freq_samples, exact_frequencies = et_frequency_mean2(
                epochs=self.input_node.data,
                fs=self.input_node.fs,
                weighted_average=self.weighted_average,
                test_frequencies=self.test_frequencies,
                delta_frequency=self.delta_frequency,
                block_size=self.block_size,
                power_line_frequency=self.power_line_frequency,
                n_jobs=self.n_jobs
            )
        else:
            if self.n_tracked_points is None:
                self.n_tracked_points = self.input_node.data.shape[0]
            samples_distance = int(max(self.input_node.data.shape[0] // self.n_tracked_points, 1))
            w_ave, w, rn, cum_rn, w_fft, n, wb, nb, snr = \
                et_mean(epochs=self.input_node.data,
                        block_size=self.block_size,
                        weighted=self.weighted_average,
                        weight_across_epochs=self.weight_across_epochs,
                        samples_distance=samples_distance
                        )
            if self.test_frequencies is not None:
                n = w_ave.shape[0]
                freqs = np.arange(0, n) * self.input_node.fs / n
                k = np.array([np.argmin(np.abs(freqs - _f)) for _f in self.test_frequencies])
                exact_frequencies = freqs[k]

            if exact_frequencies.size:
                _fft = pyfftw.builders.rfft(self.input_node.data,
                                            overwrite_input=False,
                                            planner_effort='FFTW_ESTIMATE',
                                            axis=0,
                                            threads=self.n_jobs)()

                scaling_factor = 2 / self.input_node.data.shape[0]
                _fft_samples = _fft * scaling_factor * self.input_node.data.unit
                freq_samples = _fft_samples[k, ...]

        hts = []
        for _idx, _f in enumerate(exact_frequencies):
            _freq_samples = freq_samples[_idx, :, :]
            h_samples = np.vstack((np.real(_freq_samples), np.imag(_freq_samples)))
            h_samples = h_samples.reshape((2, *freq_samples.shape[1::]))
            _spectral_amp = w_mean(epochs=_freq_samples.reshape((1, *freq_samples.shape[1::])),
                                   weights=w[0, :, :])
            _hts = hotelling_t_square_test(samples=h_samples, weights=w, channels=self.input_node.layout)
            for _idx_ch, _ht in enumerate(_hts):
                _ht.frequency_tested = _f.squeeze()
                _spectral_phase = np.angle(_spectral_amp[:, _idx_ch]).squeeze()
                _ht.mean_amplitude = np.abs(_spectral_amp[:, _idx_ch]).squeeze()
                _ht.mean_phase = _spectral_phase
            hts = hts + _hts
            # hotelling_t_square_test
        self.output_node.data = w_fft
        self.output_node.n_fft = self.input_node.data.shape[0]
        self.output_node.domain = Domain.frequency
        self.output_node.frequency_resolution = self.input_node.fs/self.input_node.data.shape[0]
        self.output_node.rn = rn
        self.output_node.snr = snr
        all_ht2 = [_h.__dict__ for _h in hts]
        _stats = pd.DataFrame(all_ht2)
        self.output_node.statistical_tests = Tables(table_name=TestType.hotelling_t2_freq,
                                                    data=_stats,
                                                    data_source=self.name)
        _stats = self.get_frequency_peaks_as_pandas(pd.DataFrame(all_ht2))
        self.output_node.peaks = _stats
        self.output_node.processing_tables_local = Tables(table_name='peaks_frequency',
                                                          data=_stats,
                                                          data_source=self.name)

    @staticmethod
    def get_frequency_peaks_as_pandas(hotelling_tests: pd.DataFrame | None = None):
        f_peaks = []
        for _i, _s_ht in hotelling_tests.iterrows():
            _f_peak = EegPeak(
                channel=_s_ht.channel,
                x=_s_ht.frequency_tested,
                rn=_s_ht.rn,
                amp=_s_ht.mean_amplitude,
                amp_snr=_s_ht.snr,
                significant=bool(_s_ht.p_value < 0.05),
                peak_label="{:10.1f}".format(_s_ht.frequency_tested),
                show_label=True,
                positive=True,
                domain=Domain.frequency,
                spectral_phase=_s_ht.mean_phase)
            f_peaks.append(_f_peak.__dict__)
        _data_pd = pd.DataFrame(f_peaks)
        return _data_pd


class DeEpoch(InputOutputProcess):
    def __init__(self, input_process=InputOutputProcess,
                 demean_edges=True,
                 edge_duration: type(u.Quantity) | None = None,
                 event_code: int = 1,
                 event_duration: type(u.Quantity) | None = None,
                 **kwargs):
        """
        This function will convert a n*m*p matrix into an (n*p) * m matrix
        :param input_process: InputOutputProcess Class
        :param demean_edges: whether data should be demeaned at the edges before converting
        :param event_code: code of trigger events to be generated
        :param event_duration: length (seconds) of trigger events to be generated
        :param edge_duration: length (seconds) of the section that will be used to demean segments being joined
        :param kwargs: extra parameters to be passed to the superclass
        """
        super(DeEpoch, self).__init__(input_process=input_process, **kwargs)
        self.demean_edges = demean_edges
        self.edge_duration = set_default_unit(edge_duration, u.s)
        self.event_code = event_code
        self.event_duration = event_duration

    def transform_data(self):
        _data, _events = de_epoch(data=self.input_node.data.copy(),
                                  demean_edges=self.demean_edges,
                                  edge_duration=self.edge_duration,
                                  event_code=self.event_code,
                                  event_duration=self.event_duration,
                                  fs=self.input_node.fs)

        self.output_node.data = _data
        self.output_node.events = _events


class ApplyFunctionToTimeROI(InputOutputProcess):
    def __init__(self, input_process=InputOutputProcess,
                 roi_windows: np.array([TimeROI]) = np.array([TimeROI()]),
                 function_object: object | None = None,
                 test_name: str | None = None,
                 **kwargs):
        """
        This InputOutputProcess will apply any function to an array of TimeROI. The function_object should be a function
        with a unique output value. This will be computed for each channel and TimeROI.
        :param input_process: InputOutputProcess Class
        :param roi_windows: time windows used to perform some measures (snr, rms)
        :param function_object: the function to apply to each TimeROI
        :param test_name: string to describe what has been calculated. If empty, the function name will be used
        :param kwargs: extra parameters to be passed to the superclass
        """
        super(ApplyFunctionToTimeROI, self).__init__(input_process=input_process, **kwargs)
        self.roi_windows = roi_windows
        self.function_object = function_object
        self.test_name = test_name

    def transform_data(self):
        roi_samples = [roi.get_roi_samples(data_node=self.input_node) for roi in self.roi_windows]
        tests = []
        for _iw in range(len(roi_samples)):
            _samples = roi_samples[_iw]
            _ini = _samples[0]
            _end = _samples[-1]
            _label = None
            if self.roi_windows is not None:
                _label = self.roi_windows[_iw].label
            if self.test_name is not None:
                test_name = self.test_name
            else:
                test_name = self.function_object.__name__
            _value = self.function_object(self.input_node.data[_samples, ...])
            for _idx_ch, _ch in enumerate(self.input_node.layout):
                tests.append(TimeROIValue(function_value=_value[_idx_ch],
                                          label=_label,
                                          test_name=test_name,
                                          ini_time=self.input_node.samples_to_x([_ini])[0],
                                          end_time=self.input_node.samples_to_x([_end])[0],
                                          channel=_ch.label).__dict__)
        _data_pd = pd.DataFrame(tests)
        self.output_node.statistical_tests = Tables(table_name='time_roi_measurements',
                                                    data=_data_pd,
                                                    data_source=self.name)
