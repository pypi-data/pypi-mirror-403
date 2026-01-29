from peegy.processing.pipe.definitions import InputOutputProcess
from peegy.processing.tools.epochs_processing_tools import et_subtract_oeg_template, et_subtract_correlated_ref
from peegy.processing.tools.template_generator.auditory_waveforms import fade_in_out_window
from peegy.processing.tools.multiprocessing.multiprocessesing_filter import filt_data
from peegy.processing.pipe.epochs import EpochData, AverageEpochs
import matplotlib.pyplot as plt
import peegy.processing.tools.filters.eegFiltering as eegf
from peegy.processing.tools.filters.resampling import eeg_resampling
from peegy.processing.tools.eeg_epoch_operators import et_unfold
import numpy as np
from sklearn.decomposition import FastICA
from sklearn.cross_decomposition import CCA
from sklearn.neighbors import KernelDensity
from peegy.processing.tools.math_tools import get_local_minima
import itertools
import os
import astropy.units as u
from peegy.tools.units.unit_tools import set_default_unit
from PyQt5.QtCore import QLibraryInfo
from tqdm import tqdm
import copy
from typing import List
os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = QLibraryInfo.location(QLibraryInfo.PluginsPath)


class ReSampling(InputOutputProcess):
    def __init__(self, input_process=InputOutputProcess,
                 new_sampling_rate: u.quantity.Quantity | None = None,
                 **kwargs):
        """
        This InputOutputProcess class will resample the data to the new_sampling_rate
        :param input_process: InputOutputProcess Class
        :param new_sampling_rate: float indicating the new sampling rate
        :param kwargs: extra parameters to be passed to the superclass
        """
        super(ReSampling, self).__init__(input_process=input_process, **kwargs)
        self.new_sampling_rate = set_default_unit(new_sampling_rate, u.Hz)

    def transform_data(self):
        _data = self.input_node.data.copy()
        data, _factor = eeg_resampling(x=_data,
                                       new_fs=self.new_sampling_rate,
                                       fs=self.input_node.fs)
        # data = resample(self.input_node.data.copy(), data.shape[0], t=None, axis=0, window=None, domain='time')
        # self.output_node.data = data * _data.unit
        self.output_node.data = data
        self.output_node.fs = self.input_node.fs * _factor
        self.output_node.process_history.append(self.process_parameters)
        self.output_node.statistical_tests = self.input_process.output_node.statistical_tests


class ReferenceData(InputOutputProcess):
    def __init__(self, input_process=InputOutputProcess,
                 reference_channels: List[str] | None = None,
                 remove_reference=True,
                 invert_polarity=False,
                 **kwargs):
        """
        This class will reference the data by subtracting the reference_channels (mean) from each individual channel
        :param input_process: InputOutputProcess Class
        :param reference_channels: list of string with the reference channels labels, if empty across channel average
        will be used
        :param remove_reference: boolean indicating whether to keep or remove the reference channel from the data
        :param invert_polarity: boolean indicating if channels polarity will be polarity inverted (data * -1)
        :param kwargs: extra parameters to be passed to the superclass
        """
        super(ReferenceData, self).__init__(input_process=input_process, **kwargs)
        if reference_channels is None:
            reference_channels = ['']
        self.reference_channels = reference_channels
        self.remove_reference = remove_reference
        self.invert_polarity = invert_polarity

    def transform_data(self):
        _ch_idx = self.input_node.get_channel_idx_by_label(self.reference_channels)
        if not _ch_idx.size:
            self.remove_reference = False
            _ch_idx = np.arange(self.input_node.layout.size)
        print('Referencing data to: ' + ''.join(['{:s} '.format(_ch.label) for _ch in self.input_node.layout[_ch_idx]]))
        reference = np.mean(self.input_node.data[:, _ch_idx], axis=1, keepdims=True)
        self.output_node.data = (self.input_node.data - reference) * (-1.0) ** self.invert_polarity

        if self.remove_reference:
            self.output_node.delete_channel_by_idx(_ch_idx)


class FilterData(InputOutputProcess):
    def __init__(self, input_process=InputOutputProcess,
                 high_pass: u.quantity.Quantity | None = None,
                 low_pass: u.quantity.Quantity | None = None,
                 zero_latency: bool = True,
                 ripple_db: u.Quantity = 60 * u.dB,
                 transition_width: u.Quantity = 1 * u.Hz,
                 **kwargs):
        """
        Filter EEG data using a zero group-delay technique
        :param input_process: InputOutputProcess Class
        :param high_pass: Frequency (in Hz) of high-pass filter
        :param low_pass: Frequency (in Hz) of low-pass filter
        :param zero_latency: If true, the latency (group delay) of the filter will be adjusted by (N + 1) / 2 which is
        the group delay of a linear phase FIR filter
        :param transition_width: width of filter transition band (in Hz)
        :param ripple_db: amount of ripple, in dB, in the pass-band and rejection regions. The magnitude variation will
        be below -ripple dB within the bandpass region, whilst the attenuation in the rejection band will be at least
        + ripple dB
        :param kwargs: extra parameters to be passed to the superclass
        """
        super(FilterData, self).__init__(input_process=input_process, **kwargs)
        self.low_pass = set_default_unit(low_pass, u.Hz)
        self.high_pass = set_default_unit(high_pass, u.Hz)
        self.zero_latency = zero_latency
        self.ripple_db = ripple_db
        self.transition_width = transition_width

    def transform_data(self):
        if self.low_pass is None and self.high_pass is None:
            self.output_node.data = self.input_node.data
            return
        filtered_signal = self.input_node.data.copy()
        _b = eegf.bandpass_fir_win(high_pass=self.high_pass,
                                   low_pass=self.low_pass,
                                   fs=self.input_node.fs,
                                   ripple_db=self.ripple_db.value,
                                   transition_width=self.transition_width,
                                   filt_filt_cutoff=False)
        _b = _b * u.dimensionless_unscaled
        if self.zero_latency:
            mode = 'original'
        else:
            mode = 'full'
        filtered_signal = filt_data(data=filtered_signal, b=_b, mode=mode)
        self.output_node.data = filtered_signal


class RegressOutEOG(InputOutputProcess):
    def __init__(self, input_process=InputOutputProcess,
                 ref_channel_labels: List[str] | None = None,
                 method: str = 'template',
                 high_pass: u.quantity.Quantity = 0.1 * u.Hz,
                 low_pass: u.quantity.Quantity = 20.0 * u.Hz,
                 peak_width: u.quantity.Quantity = 0.1 * u.s,
                 template_width: u.quantity.Quantity = 1.4 * u.s,
                 remove_eog_channels: bool = True,
                 save_figure: bool = True,  # save figure
                 fig_format: str = '.png',
                 user_naming_rule: str = '',
                 return_figures: bool = False,
                 n_iterations: int = 10,
                 kernel_bandwidth: float = 4 * 0.15,
                 use_initial_template: bool = True,
                 **kwargs):
        """
        This class removes EOG artifacts using a template technique. Blinking artifacts are detected and averaged to
        generate a template. This template is scaled for each channel in order to maximize correlation between each
        individual blink and individual events on each channel
        The resulting template is removed from the data, reducing blinks artifacts.
        :param input_process: InputOutputProcess Class
        :param ref_channel_labels: a list with the channel labels that contain the EOG
        :param high_pass: Frequency (in Hz) of high-pass filter all data. This is necessary to generate the template
        :param low_pass: Frequency (in Hz) of low-pass filter only applied to EOG channels
        :param peak_width: default minimum width (in seconds) to detect peaks
        :param template_width: the duration (in seconds) of the time window to average and generate a template
        :param remove_eog_channels: if true EOG channels will be removed once data has been cleaned
        :param save_figure: whether to save or not figures showing the detection and removal of blinks
        :param fig_format: format of output figure
        :param n_iterations: number of iterations to improve the template estimation
        :param kernel_bandwidth: factor use to control the with of the Gaussian kernel in threshold detection
        matching.
        :param use_initial_template: if true, a template eye blinking will be used as starting point to find events
        :param kwargs: extra parameters to be passed to the superclass
        """
        super(RegressOutEOG, self).__init__(input_process=input_process, **kwargs)
        self.ref_channel_labels = ref_channel_labels
        self.low_pass = low_pass
        self.high_pass = high_pass
        self.peak_width = peak_width
        self.template_width = template_width
        self.remove_eog_channels = remove_eog_channels
        self.save_figure = save_figure
        self.fig_format = fig_format
        self.method = method
        self.user_naming_rule = user_naming_rule
        self.return_figures = return_figures
        self.n_iterations = n_iterations
        self.kernel_bandwidth = kernel_bandwidth
        self.use_initial_template = use_initial_template

    def transform_data(self):
        data = self.input_node.data.copy()
        _ref_idx = self.input_node.get_channel_idx_by_label(labels=self.ref_channel_labels)
        figure_dir_path = self.input_node.paths.figures_current_dir
        _sep = '_' if self.user_naming_rule is not None else ''
        _naming_rule = '' if self.user_naming_rule is None else self.user_naming_rule
        figure_basename = self.name + _sep + _naming_rule
        artefact_method = self.method
        if artefact_method is None:
            if data.ndim == 3:
                artefact_method = 'correlation'
            else:
                artefact_method = 'template'

        if _ref_idx.size:
            print('Using {:} to remove eog artifacts'.format(artefact_method))
            if artefact_method == 'template':
                data, figures, *_ = et_subtract_oeg_template(data=data,
                                                             idx_ref=np.array(_ref_idx),
                                                             high_pass=self.high_pass,
                                                             low_pass=self.low_pass,
                                                             fs=self.input_node.fs,
                                                             template_width=self.template_width,
                                                             plot_results=self.save_figure,
                                                             figure_path=figure_dir_path,
                                                             figure_basename=figure_basename,
                                                             n_iterations=self.n_iterations,
                                                             kernel_bandwidth=self.kernel_bandwidth,
                                                             use_initial_template=self.use_initial_template
                                                             )
            if artefact_method == 'correlation':
                data, figures = et_subtract_correlated_ref(data=data,
                                                           idx_ref=np.array(_ref_idx),
                                                           high_pass=self.high_pass,
                                                           low_pass=self.low_pass,
                                                           fs=self.input_node.fs,
                                                           plot_results=self.save_figure,
                                                           figure_path=figure_dir_path,
                                                           figure_basename=figure_basename)

            if self.return_figures:
                self.figures = figures
            else:
                [plt.close(fig) for fig in figures]
        else:
            print('Reference channels for eye artefact reduction are not valid! Will return data unaltered.')

        self.output_node.data = data
        if self.remove_eog_channels and _ref_idx.size:
            self.output_node.delete_channel_by_idx(_ref_idx)


class RegressOutICA(InputOutputProcess):
    def __init__(self, input_process=InputOutputProcess,
                 ref_channel_labels: List[str] | None = None,
                 **kwargs):
        """
        This class uses independent component analysis to remove EOG activity. The removal is based on the correlation
        between the ICA and the reference channels (containing large EOG activity)
        :param input_process: InputOutputProcess Class
        :param ref_channel_labels: a list with the channel labels that contain the EOG
        :param kwargs:
        """
        super(RegressOutICA, self).__init__(input_process=input_process, **kwargs)
        self.ref_channel_labels = ref_channel_labels

    def transform_data(self):
        data = self.input_node.data.copy()
        _ref_idx = self.input_node.get_channel_idx_by_label(labels=self.ref_channel_labels)
        _cov = data[:, _ref_idx]
        _offset = int(data.shape[0] * 0.10)

        # Compute ICA
        print('Performing ICA analysis')
        ica = FastICA(n_components=data.shape[1], max_iter=1000)
        ica.fit(data)
        # decompose signal into components
        components = ica.fit_transform(data)
        corr_coefs = np.empty((components.shape[1], _cov.shape[1]))
        for _i_com, _i_cov in itertools.product(range(components.shape[1]), range(_cov.shape[1])):
            corr_coefs[_i_com, _i_cov] = \
                np.corrcoef(_cov[_offset:-_offset, _i_cov], components[_offset:-_offset, _i_com])[0, 1]
        _idx_to_remove = np.argmax(np.abs(corr_coefs), axis=0)
        print('Maximum correlations: {:}'.format(corr_coefs[np.argmax(np.abs(corr_coefs), axis=0), :]))
        print('Removing components: {:}'.format(_idx_to_remove))
        components[:, _idx_to_remove] = 0
        clean_data = ica.inverse_transform(components)
        self.output_node.data = clean_data


class RegressOutCCA(InputOutputProcess):
    def __init__(self, input_process=InputOutputProcess, ref_channel_labels: List[str] | None = None, **kwargs):
        super(RegressOutCCA, self).__init__(input_process=input_process, **kwargs)
        self.channel_labels = ref_channel_labels

    def transform_data(self):
        data = self.input_node.data.copy()
        _ref_idx = self.input_node.get_channel_idx_by_label(labels=self.ref_channel_labels)
        _cov = data[:, _ref_idx]
        # Compute ICA
        print('Performing ICA analysis')

        cca = CCA(n_components=data.shape[1])
        cca.fit(data, _cov)
        # decompose signal into components
        X_c, Y_c = cca.transform(data, _cov)
        # corr_coefs = np.empty((components.shape[1], _cov.shape[1]))
        # for _i_com, _i_cov in itertools.product(range(components.shape[1]), range(_cov.shape[1])):
        #     corr_coefs[_i_com, _i_cov] = \
        #     np.corrcoef(_cov[_offset:-_offset, _i_cov], components[_offset:-_offset, _i_com])[0, 1]
        # _idx_to_remove = np.argmax(np.abs(corr_coefs), axis=0)
        # print('Maximum correlations: {:}'.format(corr_coefs[np.argmax(np.abs(corr_coefs), axis=0), :]))
        # print('Removing components: {:}'.format(_idx_to_remove))
        # components[:, _idx_to_remove] = 0
        # clean_data = ica.inverse_transform(components)

        # self.output_node.data = clean_data


class AutoRemoveBadChannels(InputOutputProcess):
    def __init__(self, input_process=InputOutputProcess,
                 thr_sd=5.0 * u.dimensionless_unscaled,
                 amp_thr=50000.0 * u.uV,
                 interval=0.001 * u.s,
                 **kwargs):
        """
        This function will try to detect bad channels by looking at the standard deviation across channels.
        It will remove any channels with and std larger than thr_sd, which is computed across all channels.
        It also removes any channel whose amplitude exceeds amp_thr.
        :param input_process: InputOutputProcess Class
        :param thr_sd: threshold standard deviation to remove channels. Channels with larger std will be removed
        :param amp_thr: threshold amplitude. Channel exceeding this will be removed
        :param interval: time interval to subsample the data before estimating std (this is used to speed up the process
        in very long data files
        :param kwargs: extra parameters to be passed to the superclass
        """
        super(AutoRemoveBadChannels, self).__init__(input_process=input_process, **kwargs)
        self.thr_sd = thr_sd
        self.amp_thr = set_default_unit(amp_thr, u.uV)
        self.interval = set_default_unit(interval, u.s)

    def transform_data(self):
        if self.input_node.data.ndim == 3:
            data = et_unfold(self.input_node.data)
        else:
            data = self.input_node.data
        step_size = np.maximum(int(self.interval * self.input_node.fs), 1)
        _samples = np.arange(0, self.input_node.data.shape[0], step_size).astype(int)
        sub_data = data[_samples, :]
        # compute dc component
        _dc_component = np.mean(np.abs(sub_data), axis=0)
        bad_channels = np.where(_dc_component > self.amp_thr)[0]
        _others_idx = np.array([idx for idx in np.arange(sub_data.shape[1]) if idx not in bad_channels], dtype=int)
        a_std = np.std(sub_data[:, _others_idx], axis=0)
        thr_ci = self.thr_sd * np.std(a_std) + np.mean(a_std)
        n_ch_idx = np.where(a_std > thr_ci)[0]
        bad_idx = _others_idx[n_ch_idx] if n_ch_idx.size else np.array([], dtype=int)
        bad_channels = np.concatenate((bad_channels, bad_idx))
        _bad_channels_index = np.unique(bad_channels)
        self.output_node.data = self.input_node.data.copy()
        self.output_node.delete_channel_by_idx(_bad_channels_index)


class RemoveBadChannels(InputOutputProcess):
    def __init__(self, input_process=InputOutputProcess, bad_channels: List[str] | None = None, **kwargs):
        """
        This class will remove any channel passed in bad_channel
        :param input_process: InputOutputProcess Class
        :param bad_channels: list of strings with the label of the channels to be removed
        :param kwargs: extra parameters to be passed to the superclass
        """
        super(RemoveBadChannels, self).__init__(input_process=input_process, **kwargs)
        if bad_channels is None:
            bad_channels = ['']
        self.bad_channels = bad_channels

    def transform_data(self):
        idx_bad_channels = [_i for _i, _item in enumerate(self.input_node.layout) if _item.label in self.bad_channels]
        _bad_channels_index = np.unique(idx_bad_channels)
        self.output_node.data = self.input_node.data.copy()
        if _bad_channels_index.size:
            self.output_node.delete_channel_by_idx(_bad_channels_index)


class BaselineCorrection(InputOutputProcess):
    def __init__(self, input_process=InputOutputProcess,
                 ini_time: u.quantity.Quantity | None = None,
                 end_time: u.quantity.Quantity | None = None,
                 **kwargs):
        """
        This class will remove the mean of the data on each row between the specified times (ini_time and end_time)
        :param input_process: InputOutputProcess Class
        :param ini_time: initial time (in sec) from which mean will be calculated
        :param end_time: end time (in sec) for which the mean will be calculated
        :param kwargs: extra parameters to be passed to the superclass
        """
        super(BaselineCorrection, self).__init__(input_process=input_process, **kwargs)
        self.ini_time = set_default_unit(ini_time, u.s)
        self.end_time = set_default_unit(end_time, u.s)

    def transform_data(self):
        data = self.input_node.data
        ini_time = 0.0 * u.s if self.ini_time is None else self.ini_time
        end_time = np.inf * u.s if self.end_time is None else self.end_time
        _samples = self.input_node.x_range_to_samples(ini_time=ini_time, end_time=end_time)
        data = data - np.mean(data[_samples], axis=0)
        self.output_node.data = data


class SetBadEvents(InputOutputProcess):
    def __init__(self, input_process=InputOutputProcess,
                 reject_dc: bool = True,
                 rejection_percentage: float | None = None,
                 rejection_threshold: u.quantity.Quantity | None = None,
                 window_duration: u.quantity.Quantity | None = None,
                 max_percentage_epochs_above_threshold: float = 1.0,
                 event_code: float | None = None,
                 events_mask: int | None = None,
                 kernel_bandwidth: float = 0.15,
                 **kwargs):
        """
        This class will epochs where a given threshold has been exceeded. If any channel exceeds the threshold at a
        given trial, that particular epoch will be removed from all channels. This is done to keep the data in a single
        matrix.
        :param input_process: InputOutputProcess Class
        :param reject_dc: bool indicating if detected DC should be found and marked as bad events
        :param max_percentage_epochs_above_threshold: if a single channel has more than max_epochs_above_threshold
        (percentage) epochs, the channel will be removed.
        :param rejection_percentage indicates the percentage of epochs to remove.
        above the threshold, the channel will be removed.
        :param rejection_threshold: indicates level above which epochs will be rejected
        :param kwargs: extra parameters to be passed to the superclass
        """
        super(SetBadEvents, self).__init__(input_process=input_process, **kwargs)
        self.reject_dc = reject_dc
        self.rejection_threshold = set_default_unit(rejection_threshold, u.uV)
        self.event_code = event_code
        self.events_mask = events_mask
        self.kernel_bandwidth = kernel_bandwidth
        self.window_duration = window_duration

    def transform_data(self):
        if not self.input_node.events.events().size:
            print('no events in data')
            return
        data = self.input_node.data
        self.output_node.events = copy.deepcopy(self.input_node.events)
        self.output_node.data = data
        self.output_node.events.mask = self.events_mask

        _time = self.window_duration
        if self.window_duration is None:
            _time = np.mean(np.diff(self.output_node.events.get_events_time(code=self.event_code)))
        _window_samples = int(_time * self.input_node.fs)
        events_index = self.output_node.events.get_events_index(code=self.event_code,
                                                                fs=self.input_node.fs)
        _derivarive = np.diff(data, axis=0)
        _idx_bad_events_dc = np.array([], dtype=int)
        if self.reject_dc:
            std = np.array([]) * data.unit
            for i, _event_ini in enumerate(tqdm(events_index, desc='Finding DC intervals')):
                # ensure that blocks match buffer size
                _event_ini = np.minimum(np.maximum(0, _event_ini), _derivarive.shape[0])
                _event_end = np.maximum(0,
                                        np.minimum(_event_ini + _window_samples, _derivarive.shape[0]))
                _current_buffer = _derivarive[_event_ini:_event_end, :]
                if _current_buffer.size == 0:
                    continue
                _std = np.std(_current_buffer, axis=0, keepdims=True)
                if i == 0:
                    std = _std
                else:
                    std = np.vstack((std, _std))
            if std.size > 0:
                q3, q1 = np.percentile(std, [95, 5], axis=0)
                iqr = q3 - q1

                bw = iqr * self.kernel_bandwidth
                if np.all(bw.value != 0):
                    for idx_ch in range(data.shape[1]):
                        kde = KernelDensity(bandwidth=bw[idx_ch].value, kernel='gaussian')
                        kde.fit(std[:, idx_ch][:, None].value)
                        x_d = np.linspace(std[:, idx_ch].min() - 5 * bw[idx_ch],
                                          std[:, idx_ch].max() + 5 * bw[idx_ch], 1000).reshape(-1, 1)
                        log_dens = kde.score_samples(x_d.value)
                        _pdf = np.exp(log_dens)
                        _minima, _minima_idx = get_local_minima(_pdf.squeeze())
                        _max_idx = _pdf.argmax()
                        threshold = None
                        if _minima_idx[_minima_idx < _max_idx].size:
                            threshold_idx = _minima_idx[_minima_idx < _max_idx][-1]
                            threshold = x_d[threshold_idx]
                            _idx_bad_events_dc = np.append(_idx_bad_events_dc, np.argwhere(std[:, idx_ch] < threshold))
                        # if show_histogram:
                        #     fig = plt.figure()
                        #     ax = fig.add_subplot(111)
                        #     ax.fill(x_d, _pdf, fc="#AAAAFF")
                        #     ax.plot(x_d[threshold_idx], _pdf[threshold_idx], 'o')
                        #     ax.plot(x_d[_max_idx], _pdf[_max_idx], 'o')
                        #     fig.show()
        _idx_bad_events_thr = np.array([], dtype=int)
        if self.rejection_threshold is not None:
            for i, _event_ini in enumerate(tqdm(events_index,
                                                desc='Finding data intervals above {:}'.format(
                                                    self.rejection_threshold))):
                # ensure that blocks match buffer size
                _event_ini = np.minimum(np.maximum(0, _event_ini), data.shape[0])
                _event_end = np.maximum(0,
                                        np.minimum(_event_ini + _window_samples, data.shape[0]))
                _current_buffer = data[_event_ini:_event_end, :]
                if _current_buffer.size == 0:
                    continue
                if np.any(np.abs(_current_buffer) > self.rejection_threshold):
                    _idx_bad_events_thr = np.append(_idx_bad_events_thr, i)

        _idx_bad_events = np.unique(np.concatenate((_idx_bad_events_dc, _idx_bad_events_thr)))
        if _idx_bad_events.size:
            self.output_node.events.set_events_status(event_idx=_idx_bad_events,
                                                      bad_event=True)
            print('{:} out of {:} events set as bad based on DC precense'.format(
                _idx_bad_events_dc.size,
                events_index.size
            ))
            print('{:} out of {:} events set as bad based on rejection threshold criteria of {:}'.format(
                _idx_bad_events_thr.size,
                events_index.size,
                self.rejection_threshold
            ))
            print('Setting {:} out of {:} events as bad (based on threshold and DC)'.format(
                _idx_bad_events.size,
                events_index.size
            ))
            print(self.output_node.events.summary())


class RemoveEvokedResponse(InputOutputProcess):
    def __init__(self, input_process=InputOutputProcess,
                 pre_stimulus_interval: u.quantity.Quantity | None = None,
                 post_stimulus_interval: u.quantity.Quantity | None = None,
                 baseline_correction_ini_time: u.quantity.Quantity | None = None,
                 baseline_correction_end_time: u.quantity.Quantity | None = None,
                 event_code: float | None = None,
                 base_line_correction: bool = False,
                 demean: bool = True,
                 events_mask: int | None = None,
                 weighted_average: bool = True,
                 weight_across_epochs: bool = False,
                 n_tracked_points: int | None = None,
                 block_size: int = 1,
                 fade_in_out: bool = False,
                 fade_in_out_percentage: float = 0.05,
                 **kwargs):
        """
        This class will remove the evoked response from the continuous data and return the continuous data.
        :param input_process: InputOutputProcess Class
        :param pre_stimulus_interval: the length (in sec) of the data to be read before the trigger
        :param post_stimulus_interval: the length (in sec) of the data to be read after the trigger
        :param event_code: integer indicating the event code to be used to epoch the data
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
        :param demean: whether to remove the mean from each epoch
        :param events_mask: integer value used to masker triggers codes. This is useful to ignore triggers inputs above
        a particular value. For example, if only the first 8 trigger inputs were used (max decimal value is 255), in a
        system with 16 trigger inputs, then the masker could be set to 255 to ignore any trigger from trigger inputs 9
        to 16
        :param weighted_average: if True, weighted average will be used
        :param weight_across_epochs: if True, weights are computed across epochs (as in Elbeling 1984) otherwise weights
        are computed within epoch (1 / variance across time)
        :param n_tracked_points: number of equally spaced points over time used to estimate residual noise and weights
        :param block_size: number of trials that will be stacked together to estimate the residual noise
        :param fade_in_out: It True, a faded in and out window will be applied to evoked response to prevent edge
        artefacts
        :param fade_in_out_percentage: defents the percentage of the signal in which fade-in and fade-out will take
        place. E.g., if epoch is 1.0s, then the fade-in and fade-out will last 50 ms if fade_in_out_percentage is 0.05
        :param kwargs: extra parameters to be passed to the superclass
        """
        super(RemoveEvokedResponse, self).__init__(input_process=input_process, **kwargs)
        self.pre_stimulus_interval = set_default_unit(pre_stimulus_interval, u.s)
        self.post_stimulus_interval = set_default_unit(post_stimulus_interval, u.s)
        self.event_code = event_code
        self.base_line_correction = base_line_correction
        self.demean = demean
        self.events_mask = events_mask
        self.baseline_correction_ini_time = baseline_correction_ini_time
        self.baseline_correction_end_time = baseline_correction_end_time
        self.weighted_average = weighted_average
        self.n_tracked_points = n_tracked_points
        self.block_size = block_size
        self.weight_across_epochs = weight_across_epochs
        self.fade_in_out = fade_in_out
        self.fade_in_out_percentage = fade_in_out_percentage

    def transform_data(self):
        data = self.input_node.data.copy()
        epochs = EpochData(input_process=self.input_process,
                           pre_stimulus_interval=self.pre_stimulus_interval,
                           post_stimulus_interval=self.post_stimulus_interval,
                           event_code=self.event_code,
                           events_mask=self.events_mask,
                           base_line_correction=self.base_line_correction,
                           baseline_correction_ini_time=self.baseline_correction_ini_time,
                           baseline_correction_end_time=self.baseline_correction_end_time,
                           keep_input_node=True
                           )
        epochs.run()
        evoked_response = AverageEpochs(input_process=epochs,
                                        keep_input_node=False,
                                        weighted_average=self.weighted_average,
                                        weight_across_epochs=self.weight_across_epochs,
                                        block_size=self.block_size,
                                        n_tracked_points=self.n_tracked_points)
        evoked_response.run()
        _epoch_samples = evoked_response.output_node.data.shape[0]
        evoked_data = evoked_response.output_node.data
        if self.fade_in_out:
            fade_window = fade_in_out_window(n_samples=_epoch_samples,
                                             fraction=self.fade_in_out_percentage)
            evoked_data = evoked_data * fade_window

        for _event_idx in self.input_node.events.get_events_index(self.event_code, fs=self.input_node.fs):
            _ini = _event_idx
            _end = np.minimum(_event_idx + _epoch_samples, data.shape[0])
            _b_size = _end - _ini
            if _b_size > 0:
                _er = evoked_data[0: _end - _ini, :]
                data[_ini: _end, :] = data[_ini: _end, :] - _er
        self.output_node.data = data
