from peegy.processing.pipe.definitions import InputOutputProcess
from peegy.processing.tools.epochs_processing_tools import et_mean
import multiprocessing
from peegy.plot import eeg_ave_epochs_plot_tools as eegpt
from peegy.definitions.channel_definitions import Domain
import pyfftw
import numpy as np
import os
import astropy.units as u
from PyQt5.QtCore import QLibraryInfo
from ssqueezepy import Wavelet, cwt, stft
from ssqueezepy.experimental import scale_to_freq
os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = QLibraryInfo.location(QLibraryInfo.PluginsPath)


class HilbertEnvelope(InputOutputProcess):
    def __init__(self, input_process=InputOutputProcess, high_pass=None, low_pass=None, **kwargs):
        """
        This process computes the  Hilbert Envelope of EEG data
        :param input_process: InputOutputProcess Class
        :param kwargs: extra parameters to be passed to the superclass
        """
        super(HilbertEnvelope, self).__init__(input_process=input_process, **kwargs)

    def transform_data(self):
        data = self.input_node.data.copy()
        _fft = pyfftw.builders.fft(data, overwrite_input=False, planner_effort='FFTW_ESTIMATE', axis=0,
                                   threads=multiprocessing.cpu_count())
        fx = _fft()
        n = fx.shape[0]
        h = np.zeros(n)
        if n % 2 == 0:
            h[0] = h[n // 2] = 1
            h[1:n // 2] = 2
        else:
            h[0] = 1
            h[1:(n + 1) // 2] = 2
        _ifft = pyfftw.builders.ifft(fx * h.reshape(-1, 1), overwrite_input=False, planner_effort='FFTW_ESTIMATE',
                                     axis=0,
                                     threads=multiprocessing.cpu_count())
        hilbert_data = _ifft()
        self.output_node.data = np.abs(hilbert_data)


class InducedResponse(InputOutputProcess):
    def __init__(self, input_process=InputOutputProcess,
                 weighted_average=True,
                 n_tracked_points=256,
                 block_size=5,
                 roi_windows=None, **kwargs):
        super(InducedResponse, self).__init__(input_process=input_process, **kwargs)
        self.weighted_average = weighted_average
        self.n_tracked_points = n_tracked_points
        self.block_size = block_size
        self.roi_windows = roi_windows

    def transform_data(self):
        trials_abs_w_ave, w, rn, cum_rn, w_fft, *_ = \
            et_mean(epochs=np.abs(self.input_node.data),
                    block_size=max(self.block_size, 5),
                    samples_distance=int(max(self.input_node.data.shape[0] // self.n_tracked_points, 10)),
                    roi_windows=self.roi_windows,
                    weighted=self.weighted_average
                    )
        w_ave, w, rn, cum_rn, w_fft, *_ = \
            et_mean(epochs=self.input_node.data,
                    block_size=max(self.block_size, 5),
                    samples_distance=int(max(self.input_node.data.shape[0] // self.n_tracked_points, 10)),
                    roi_windows=self.roi_windows,
                    weighted=self.weighted_average
                    )
        self.output_node.data = trials_abs_w_ave - np.abs(w_ave)
        self.output_node.rn = rn
        self.output_node.cum_rn = cum_rn
        self.output_node.snr = None
        self.output_node.cum_snr = None
        self.output_node.s_var = None


class TimeFrequencyResponse(InputOutputProcess):
    def __init__(self, input_process=InputOutputProcess,
                 time_window: u.Quantity = 0.3 * u.s,
                 sample_interval: u.Quantity = 0.004 * u.s,
                 topographic_channels=np.array([]),
                 title: str = '',
                 plot_x_lim=None,
                 plot_y_lim=None,
                 times=np.array([]),
                 fig_format='.png',
                 fontsize=12,
                 user_naming_rule: str = '',
                 spec_thresh=6,
                 average_mode='magnitude',
                 method: str = 'wavelet',
                 wavelet_type: str = 'morlet',
                 **kwargs):
        super(TimeFrequencyResponse, self).__init__(input_process=input_process, **kwargs)
        self.time_window = time_window
        self.sample_interval = sample_interval
        self.frequency = None
        self.time = None
        self.topographic_channels = topographic_channels
        self.title = title
        self.plot_x_lim = plot_x_lim
        self.plot_y_lim = plot_y_lim
        self.fig_format = fig_format
        self.fontsize = fontsize
        self.user_naming_rule = user_naming_rule
        self.times = times
        self.time_window = time_window
        self.sample_interval = sample_interval
        self.spec_thresh = spec_thresh
        self.average_mode = average_mode
        self.method = method
        self.wavelet_type = wavelet_type

    def transform_data(self):
        magnitude, freqs = self.time_frequency_transformation(epochs=self.input_node.data,
                                                              fs=self.input_node.fs,
                                                              time_window=self.time_window,
                                                              sample_interval=self.sample_interval,
                                                              average_mode=self.average_mode,
                                                              method=self.method,
                                                              wavelet_type=self.wavelet_type
                                                              )
        self.output_node.data = magnitude
        self.output_node.y = freqs
        self.output_node.x = self.input_node.x
        self.output_node.domain = Domain.time_frequency

    @staticmethod
    def time_frequency_transformation(epochs: np.array = np.array([]),
                                      method='spectrogram',
                                      wavelet_type='morlet',
                                      time_window=2.0,
                                      sample_interval=2.0,
                                      fs=0.0,
                                      average_mode='magnitude'):

        _waves, freqs, ave = None, None, None
        data = epochs
        if data.ndim == 2:
            data = data[:, :, None]
        if average_mode == 'complex':
            data = np.mean(epochs, 2, keepdims=True)
        for _i in range(data.shape[2]):
            if method == 'wavelet':
                wavelet = Wavelet(wavelet_type)
                w, scales = cwt(data[:, :, _i].T, wavelet)
                freqs = scale_to_freq(scales, wavelet, w.shape[2], fs=fs.to(u.Hz).value)
                _waves = w
            if method == 'stft':
                stft_data = stft(data[:, :, _i].T)[:, ::-1, :]
                freqs = np.linspace(1, 0, stft_data.shape[1]) * fs.to(u.Hz).value / 2
                _waves = stft_data
            if average_mode == 'magnitude':
                _waves = np.abs(_waves)
            if _i == 0:
                ave = _waves
            else:
                ave += _waves
            print('Computing spectrogram {:} out of {:}'.format(_i, data.shape[2]))
        ave /= data.shape[2]
        ave = np.transpose(ave, [2, 0, 1])
        freqs = freqs * u.Hz
        ave = ave * data.unit
        return ave, freqs


class PlotTimeFrequencyData(InputOutputProcess):
    def __init__(self, input_process=InputOutputProcess,
                 topographic_channels=np.array([]),
                 title: str = '',
                 plot_x_lim: [float, float] = None,
                 plot_y_lim: [float, float] = None,
                 times: np.array = np.array([]),
                 fig_format: str = '.png',
                 fontsize: float = 12,
                 user_naming_rule: str = '',
                 spec_thresh: float = -np.inf,
                 return_figures: bool = True,
                 save_figures: bool = False,
                 normalize: bool = True,
                 db_scale: bool = True,
                 **kwargs):
        super(PlotTimeFrequencyData, self).__init__(input_process=input_process, **kwargs)
        self.topographic_channels = topographic_channels
        self.title = title
        self.plot_x_lim = plot_x_lim
        self.plot_y_lim = plot_y_lim
        self.fig_format = fig_format
        self.fontsize = fontsize
        self.user_naming_rule = user_naming_rule
        self.times = times
        self.spec_thresh = spec_thresh
        self.return_figures = return_figures
        self.save_figures = save_figures
        self.normalize = normalize
        self.db_scale = db_scale

    def transform_data(self):
        assert self.input_node.domain == Domain.time_frequency, 'input should be a time-frequency transformed data'

        figures = eegpt.plot_eeg_time_frequency_power(
            ave_data=self.input_node,
            eeg_topographic_map_channels=self.topographic_channels,
            figure_dir_path=self.input_node.paths.figures_current_dir,
            figure_basename='{:}{:}'.format(
                self.input_process.name + '_',
                self.user_naming_rule),
            title=self.title,
            x_lim=self.plot_x_lim,
            y_lim=self.plot_y_lim,
            fig_format=self.fig_format,
            fontsize=self.fontsize,
            spec_thresh=self.spec_thresh,
            return_figures=self.return_figures,
            save_figures=self.save_figures,
            normalize=self.normalize,
            db_scale=self.db_scale
        )
        self.figures = figures
