import numpy as np

import peegy.definitions.default_paths
from peegy.definitions.channel_definitions import Domain, ChannelItem
from peegy.processing.pipe.definitions import InputOutputProcess, DataNode
from peegy.processing.tools.multiprocessing.multiprocessesing_filter import filt_data
from peegy.tools.signal_generator import noise_functions as nf
from peegy.layouts import layouts
import astropy.units as u
from peegy.directories.tools import DirectoryPaths
from peegy.processing.events.event_tools import detect_events
from peegy.definitions.events import Events
from peegy.processing.tools.template_generator.auditory_waveforms import eog_template, fade_in_out_window
from peegy.tools.units.unit_tools import set_default_unit
from scipy.linalg import eigh, cholesky
import pyqtgraph as pg

pg.setConfigOption('leftButtonPan', False)


def correlated_noise(method: str = 'cholesky',
                     noise_token: type(np.array) | None = None,
                     n_channels: int = 4,
                     covariance_matrix: type(np.array) | None = None,
                     ):
    assert covariance_matrix.shape == (n_channels, n_channels)
    # We need a matrix `c` for which `c*c^T = r`.  We can use, for example,
    # the Cholesky decomposition, or we can construct `c` from the
    # eigenvectors and eigenvalues.
    # check if covariance matrix is unitary
    if np.all(covariance_matrix == 1):
        c = np.ones(covariance_matrix.shape)
    elif method == 'cholesky':
        # Compute the Cholesky decomposition.
        c = cholesky(covariance_matrix, lower=True)
    else:
        # Compute the eigenvalues and eigenvectors.
        evals, evecs = eigh(covariance_matrix)
        # Construct c, so c*c^T = r.
        c = np.dot(evecs, np.diag(np.sqrt(evals)))

    # Convert the data to correlated random variables.
    y = np.dot(c, noise_token.T).T
    return y


class GenerateInputData(InputOutputProcess):
    def __init__(self,
                 template_waveform: type(np.array) | None = None,
                 stimulus_waveform: type(np.array) | None = None,
                 fs: u.quantity.Quantity = 16384.0 * u.Hz,
                 alternating_polarity=False,
                 n_channels: int | None = None,
                 snr: float = 3,
                 line_noise_amplitude: u.quantity.Quantity = 0 * u.uV,
                 line_noise_mixing_matrix: type(np.array) | None = None,
                 line_noise_frequency: u.Quantity = 50 * u.Hz,
                 line_noise_n_harmonics: int = 1,
                 include_non_stationary_noise_events=False,
                 noise_events_interval: u.quantity.Quantity = 25.0 * u.s,
                 noise_events_duration: u.quantity.Quantity = 15.0 * u.s,
                 noise_events_power_delta_db: float = 6.0,
                 noise_jitter_percentage: float = 0,
                 noise_seed: float | None = None,
                 noise_attenuation: float = 0,
                 noise_covariance_matrix: type(np.array) | None = None,
                 mixing_matrix: type(np.array) | None = None,
                 artefacts_mixing_matrix: type(np.array) | None = None,
                 eog_mixing_matrix: type(np.array) | None = None,
                 return_eog_channel: bool = True,
                 include_eog_events: bool = False,
                 fade_in_out: bool = False,
                 event_times: type(np.array) | None = None,
                 event_code: float = 1.0,
                 events_asymmetry_interval: int = 1,
                 events_asymmetry_factor: float = 1.0,
                 layout_file_name: str | None = None,
                 figures_folder: str | None = None,
                 figures_subset_folder: str = '',
                 return_noise_only=False,
                 f_noise_low: u.Quantity = 0 * u.Hz,
                 f_noise_high: type(u.Quantity) | None = None,
                 f_var_low: u.Quantity = 0 * u.Hz,
                 f_var_high: type(u.Quantity) | None = None,
                 neural_ini_time_snr: u.Quantity = 0 * u.s,
                 neural_end_time_snr: type(u.Quantity) | None = None,
                 noise_generation_length_factor: float = 1.0) -> InputOutputProcess:
        """
        This class allows to generate data that can be used without the need of having a bdf or edf file.
        This InputOutput process takes an input template and convolve it with delta at event times.
        The output will have as many channels as desired and the maximum snr will be given by snr.
        If requested, non-stationary noise events will be generated. The snr will be calculated relative to the
        stationary noise. The non-stationary events will vary around that stationary level by x dB as passed in
        noise_events_power_delta_db.
        The output events will be coded with the provided event code.
        :param template_waveform: a numpy array with the template waveform to be use as signal
        :param stimulus_waveform: a numpy array with the presented waveform. Useful to generate stimulus artifacts
        :param fs: the sampling rate of the template_waveform
        :param alternating_polarity: if true, stimulus_waveform is alternating in polarity for every epoch
        :param n_channels: number of channels to generate
        :param snr: signal-to-noise ratio defined as variance_signal / variance_noise, 0 < snr < inf.
        This will be used to set the amplitude of the stationary noise
        :param line_noise_amplitude: amplitude in uV of 50 Hz line noise
        :param line_noise_frequency: frequency of line noise
        :param line_noise_n_harmonics: number of harmonics to include in line noise
        :param include_non_stationary_noise_events: if True, non-stationary noise events will be included
        :param noise_events_interval: interval time [in seconds] between non-stationary events
        :param noise_events_duration: maximum duration of each non-stationary noise event
        :param noise_events_power_delta_db: the dB change of power in the noise noise relative to stationary noise power
        :param noise_jitter_percentage: percentage of jitter in terms of noise_events_interval
        :param noise_seed: float to set the random generator
        :param noise_attenuation: indicates the attenuation of the noise (1 / f ** noise_attenuation), set to 0 for
        white noise and to 3 for pink noise
        :param noise_covariance_matrix: n_channels by n_channels matrix indicating the desired covariance of the noise
        :param mixing_matrix: numpy array with the coefficients that will be applied to template wavefrom
        :param include_eog_events: if True, eog-like artifacts will be included
        :param return_eog_channel: it True, eog waveforms will be appended as another channel
        :param fade_in_out: It True, convolved template will be faded in and out to prevent onset effects
        :param event_times: numpy array with the location of the events. The wave
        :param event_code: desired event code to be assigned to time events
        :param events_asymmetry_interval: integer indicating the number rate at which events delta pulses will be
        modulated with a value different from 1. This is useful to simulate an asymmetric neural response every
        events_asymmetry_interval events.
        :param events_asymmetry_factor: float: indicate the scaling factor of  the dirac pulse applied every
        events_asymmetry_interval.
        :param layout_file_name: name of layout to be used. e.g. "biosemi32.lay"
        :param figures_folder: path to save generated figures
        :param figures_subset_folder: string indicating a subfolder name in figures_path
        :param return_noise_only: boolean indicating if the output will consist of noise only or not. This is useful to
        :param f_noise_low: low cuttoff frequency of generated noise
        :param f_noise_high: high cuttof frequency of generated noise
        :param f_var_low: low cuttoff to compute the energy of the noise. This is useful to produce noise where the
        energy needs to be equated in a frequency range.
        :param f_var_high: high cuttoff to compute the energy of the noise. This is useful to produce noise where the
        energy needs to be equated in a frequency range.
        :param noise_generation_length_factor is used to generate a noise that last longer than desired. This has the
        effect of increasing the density of the frequency components.
        :param neural_ini_time_snr: starting time to compute the target signal power for snr scaling
        :param neural_end_time_snr: ending time to compute the target signal power for snr scaling
        compare results with and without a target signal whilst keeping the noise output fixed.
        """
        super(GenerateInputData, self).__init__()
        self.template_waveform = template_waveform
        self.stimulus_waveform = stimulus_waveform
        self.alternating_polarity = alternating_polarity
        self.n_channels = n_channels
        self.snr = snr
        self.line_noise_amplitude = set_default_unit(line_noise_amplitude, u.V)
        self.line_noise_frequency = set_default_unit(line_noise_frequency, u.Hz)
        self.line_noise_n_harmonics = line_noise_n_harmonics
        self.line_noise_mixing_matrix = line_noise_mixing_matrix
        self.fs = set_default_unit(fs, u.Hz)
        self.include_non_stationary_noise = include_non_stationary_noise_events
        self.noise_events_interval = set_default_unit(noise_events_interval, u.s)
        self.noise_events_duration = set_default_unit(noise_events_duration, u.s)
        self.noise_events_power_delta_db = noise_events_power_delta_db
        self.noise_jitter_percentage = noise_jitter_percentage
        self.noise_seed = noise_seed
        self.noise_attenuation = noise_attenuation
        self.noise_covariance_matrix = set_default_unit(noise_covariance_matrix, template_waveform.unit ** 2.0)
        self.noise_generation_length_factor = noise_generation_length_factor
        self.event_times = set_default_unit(event_times, u.s)
        self.event_code = event_code
        self.events_asymmetry_interval = events_asymmetry_interval
        self.events_asymmetry_factor = events_asymmetry_factor
        self.include_eog_events = include_eog_events
        self.simulated_artifact = None
        self.simulated_neural_response = None
        self.simulated_artifact_response = None
        self.output_node = None
        self.layout_file_name = layout_file_name
        self.mixing_matrix = mixing_matrix
        self.artefacts_mixing_matrix = artefacts_mixing_matrix
        self.eog_mixing_matrix = eog_mixing_matrix
        self.return_eog_channel = return_eog_channel
        self.fade_in_out = fade_in_out
        self.return_noise_only = return_noise_only
        self.f_noise_low = set_default_unit(f_noise_low, u.Hz)
        self.f_noise_high = set_default_unit(f_noise_high, u.Hz)
        self.f_var_low = set_default_unit(f_var_low, u.Hz)
        self.f_var_high = set_default_unit(f_var_high, u.Hz)
        self.neural_ini_time_snr = neural_ini_time_snr
        self.neural_end_time_snr = neural_end_time_snr
        self.stationary_noise = None
        figures_folder = figures_folder if figures_folder is not None else\
            peegy.definitions.default_paths.test_figures_path
        self.figures_subset_folder = figures_subset_folder

        _ch = []
        [_ch.append(ChannelItem(label='CH_{:}'.format(i), idx=i)) for i in range(n_channels)]
        layout = np.array(_ch)
        self.output_node = DataNode(fs=fs,
                                    domain=Domain.time,
                                    layout=layout,
                                    paths=DirectoryPaths(delete_all=False,
                                                         delete_figures=False,
                                                         figures_folder=figures_folder,
                                                         figures_subset_folder=figures_subset_folder)
                                    )

    def transform_data(self):
        if self.noise_seed is not None:
            np.random.seed(self.noise_seed)
        # create synthetic data
        _events_idx = np.floor(self.event_times * self.fs).astype(int)
        events = np.zeros((int(self.event_times[-1] * self.fs) + 1, 1))
        events[_events_idx, :] = 1
        events[_events_idx[0::self.events_asymmetry_interval], :] = self.events_asymmetry_factor
        source = self.template_waveform
        # convolve source with dirac train to generate entire signal
        source = filt_data(data=source, b=events.flatten(), mode='full', onset_padding=False)
        fade_window = np.ones(source.shape)
        if self.fade_in_out:
            fade_window = fade_in_out_window(n_samples=source.shape[0],
                                             fraction=10 * self.template_waveform.shape[0] / source.shape[0])
        source = source * fade_window
        # generate the source in all channels
        if self.mixing_matrix is None:
            self.mixing_matrix = np.diag(np.ones(self.n_channels))
        tailed_source = source
        if tailed_source.shape[1] != self.n_channels:
            tailed_source = np.tile(source, (1, self.n_channels))
        assert tailed_source.shape[1] == self.mixing_matrix.shape[1]
        neural_response = tailed_source.dot(self.mixing_matrix)
        self.simulated_neural_response = neural_response

        # artifact mixing matrix
        mixed_stimulus_artefacts = np.zeros(neural_response.shape)
        artefact_source = None
        if self.stimulus_waveform is not None:
            artefact_source, mixed_stimulus_artefacts = generate_arbitrary_artefacts(
                stimulus_waveform=self.stimulus_waveform,
                n_channels=self.n_channels,
                events=events.copy(),
                alternating_polarity=self.alternating_polarity,
                artefacts_mixing_matrix=self.artefacts_mixing_matrix)
            self.simulated_artifact = artefact_source
            self.simulated_artifact_response = mixed_stimulus_artefacts

        # eog mixing matrix
        eog_mixed_artefacts = np.zeros(source.shape) * u.uV
        if self.include_eog_events:
            eog_waveform, eog_mixed_artefacts = generate_eog_artefacts(size=source.shape[0],
                                                                       n_channels=self.n_channels,
                                                                       eog_mixing_matrix=self.eog_mixing_matrix,
                                                                       fs=self.fs)

        # generate eeg noise
        noise, noise_var = generate_eeg_noise(f_noise_high=self.f_noise_high,
                                              f_noise_low=self.f_noise_low,
                                              f_var_high=self.f_var_high,
                                              f_var_low=self.f_var_low,
                                              n_channels=self.n_channels,
                                              fs=self.fs,
                                              noise_attenuation=self.noise_attenuation,
                                              noise_seed=self.noise_seed,
                                              noise_covariance_matrix=self.noise_covariance_matrix,
                                              size=source.shape[0],
                                              noise_generation_length_factor=self.noise_generation_length_factor,
                                              include_non_stationary_noise=self.include_non_stationary_noise,
                                              noise_events_duration=self.noise_events_duration,
                                              noise_events_interval=self.noise_events_interval,
                                              noise_events_power_delta_db=self.noise_events_power_delta_db,
                                              noise_jitter_percentage=self.noise_jitter_percentage
                                              )

        # generate line noise
        if self.line_noise_mixing_matrix is None:
            self.line_noise_mixing_matrix = np.diag((1 + np.random.rand(self.n_channels) * 0.001))
        line_artefact = generate_line_noise(size=source.shape[0],
                                            fs=self.fs,
                                            n_channels=self.n_channels,
                                            line_noise_amplitude=self.line_noise_amplitude,
                                            line_noise_frequency=self.line_noise_frequency,
                                            line_noise_n_harmonics=self.line_noise_n_harmonics,
                                            line_noise_mixing_matrix=self.line_noise_mixing_matrix)

        # compute variance of signal
        _ini_sample = int(self.neural_ini_time_snr * self.fs)
        _end_sample = neural_response.shape[0]
        if self.neural_end_time_snr is not None:
            _end_sample = np.minimum(int(self.neural_end_time_snr * self.fs), neural_response.shape[0])
        neural_var = np.var(neural_response[_ini_sample: _end_sample], ddof=1, axis=0)
        # scale signal

        scaled_noise = (neural_var / (self.snr * noise_var)) ** 0.5 * noise
        scaled_noise_variance = np.var(scaled_noise, ddof=1, axis=0) + np.finfo(float).eps * scaled_noise.unit ** 2.0
        data = (neural_response * (not self.return_noise_only) +
                scaled_noise +
                line_artefact +
                eog_mixed_artefacts +
                mixed_stimulus_artefacts)

        print('Theoretical RN for {:} events is {:}, and SNR {:} [dB] when target signal is included'.format(
            self.event_times.shape[0],
            np.sqrt(scaled_noise_variance / self.event_times.shape[0]),
            10 * np.log10(self.event_times.shape[0] * neural_var / scaled_noise_variance + np.finfo(float).eps)))
        events[_events_idx.astype(int)] = self.event_code

        self.output_node = DataNode(data=data,
                                    fs=self.fs,
                                    domain=Domain.time,
                                    layout=self.input_node.layout,
                                    )
        if self.layout_file_name is not None:
            self.output_node.apply_layout(layouts.Layout(file_name=self.layout_file_name))

        self.output_node.paths = self.input_node.paths
        self.get_events(events)
        if self.include_eog_events and self.return_eog_channel:
            self.output_node.append_new_channel(new_data=eog_waveform,
                                                layout_label='EOG1')
        self.stationary_noise = scaled_noise

    def get_events(self, events):
        events = detect_events(event_channel=events, fs=self.output_node.fs)
        events = Events(events=np.array(events))
        for i, _code in enumerate(np.unique(events.get_events_code())):
            print('Event code:', _code, 'Number of events:', events.get_events_code(code=_code).size)
        self.output_node.events = events


def generate_eog_artefacts(size: int | None = None,
                           n_channels: int | None = None,
                           eog_mixing_matrix: type(np.array) | None = None,
                           fs: type(u.Quantity) | None = None,
                           events_mean_time: u.Quantity = 2 * u.s,
                           events_std_time: u.Quantity = 1.4 * u.s):
    if eog_mixing_matrix is None:
        eog_mixing_matrix = np.diag((np.random.rand(n_channels) - 0.5) / 0.5)
    # generates and convolve eye artifacts
    oeg_events = np.zeros((size, 1))
    eog_time_events = np.cumsum(
        events_std_time * np.random.randn(int((size/fs) / events_mean_time)) + events_mean_time)
    eog_time_events = np.minimum(np.maximum(eog_time_events, 0), np.floor((size - 1) / fs))
    _oeg_events_idx = np.floor(eog_time_events * fs).astype(int)
    oeg_events[_oeg_events_idx, :] = 1
    # _oeg_template, _ = eog(fs)
    _oeg_template, _ = eog_template(fs)
    oeg_events = filt_data(data=_oeg_template,
                           b=oeg_events.flatten(),
                           mode='full',
                           onset_padding=False)
    eog_waveform = oeg_events[0: size, :]
    eog_mixed_artefacts = np.tile(eog_waveform, (1, n_channels)).dot(eog_mixing_matrix)
    return eog_waveform, eog_mixed_artefacts


def generate_arbitrary_artefacts(stimulus_waveform: type(np.array) | None = None,
                                 n_channels: int | None = None,
                                 events: type(np.array) | None = None,
                                 alternating_polarity: bool = False,
                                 artefacts_mixing_matrix: type(np.array) | None = None):
    if artefacts_mixing_matrix is None:
        artefacts_mixing_matrix = np.diag(np.ones(n_channels))
    events_idx = np.argwhere(events == 1)
    if alternating_polarity:
        events[events_idx[1:-1:2], :] = -1

    artefact_source = filt_data(data=stimulus_waveform,
                                b=events.flatten(),
                                mode='full',
                                onset_padding=False)
    tiled_artefact_source = artefact_source
    if tiled_artefact_source.shape[1] != n_channels:
        tiled_artefact_source = np.tile(artefact_source, (1, n_channels))
    assert tiled_artefact_source.shape[1] == n_channels
    mixed_artefacts = tiled_artefact_source.dot(artefacts_mixing_matrix)
    return artefact_source, mixed_artefacts


def generate_eeg_noise(f_noise_high: type(u.Quantity) | None = None,
                       f_noise_low: type(u.Quantity) | None = None,
                       f_var_high: type(u.Quantity) | None = None,
                       f_var_low: type(u.Quantity) | None = None,
                       fs: type(u.Quantity) | None = None,
                       noise_attenuation: float = 0,
                       noise_seed: float | None = None,
                       noise_covariance_matrix: type(np.array) | None = None,
                       n_channels: int | None = None,
                       size: int | None = None,
                       noise_generation_length_factor: float = 3,
                       include_non_stationary_noise: bool = False,
                       noise_events_interval: type(u.Quantity) | None = None,
                       noise_events_duration: type(u.Quantity) | None = None,
                       noise_events_power_delta_db: float | None = None,
                       noise_jitter_percentage: float = 0,
                       ):
    if f_noise_high is None:
        f_noise_high = fs / 2
    else:
        f_noise_high = np.minimum(f_noise_high.to(u.Hz).value, fs.to(u.Hz).value / 2) * u.Hz
    if f_var_high is None:
        f_var_high = fs / 2
    else:
        f_var_high = np.minimum(f_var_high.to(u.Hz).value, fs.to(u.Hz).value / 2) * u.Hz

    # to do: use FIR filter to generate 1 /f ** p noise!
    noise = nf.generate_modulated_noise(
        fs=fs.to(u.Hz).value,
        f_noise_low=f_noise_low.to(u.Hz).value,
        f_noise_high=f_noise_high.to(u.Hz).value,
        duration=size / fs.to(u.Hz).value * noise_generation_length_factor,
        n_channels=n_channels,
        attenuation=noise_attenuation,
        noise_seed=noise_seed)
    # if noise_seed is not None:
    #     np.random.seed(noise_seed)
    # noise = np.random.normal(1, size=(size, n_channels))

    if noise_covariance_matrix is None:
        noise_covariance_matrix = np.diag(np.ones(n_channels))
    noise_covariance_matrix = set_default_unit(noise_covariance_matrix, u.dimensionless_unscaled)
    noise = noise[0: size, ...]
    noise = correlated_noise(noise_token=noise,
                             n_channels=n_channels,
                             covariance_matrix=noise_covariance_matrix.value)

    print('noise correlation: {:}'.format(np.corrcoef(noise.T)))

    noise = noise - np.mean(noise, axis=0)
    # normalize noise to have required rms
    freq = np.fft.fftfreq(noise.shape[0], 1) * fs
    noise_psd = 1 / (noise.shape[0] ** 2) * np.abs(np.fft.fft(noise, axis=0)) ** 2.0
    noise_psd[0, :] = noise_psd[0, :] / 2
    _idx_psd = np.argwhere(np.logical_and(freq >= f_var_low, freq <= f_var_high))[:, 0]
    stationary_noise_var = np.sum(2 * noise_psd[_idx_psd, :], axis=0)

    # stationary_noise_var = np.var(noise, ddof=0, axis=0)
    if include_non_stationary_noise:
        # non-stationary noise (e.g. 1 event every 20 seconds)
        _new_noise_events = np.arange(0, size,
                                      noise_events_interval * fs) / fs
        for _i, _ne in enumerate(_new_noise_events):
            _noise_samples = int(fs * noise_events_duration)
            _jitter = 0
            if noise_jitter_percentage > 0:
                _min_jitter = -int(fs * noise_events_interval / 2 * noise_jitter_percentage)
                _max_jitter = np.maximum(int(fs * noise_events_interval / 2 * noise_jitter_percentage), 1)
                _jitter = np.random.randint(_min_jitter,
                                            _max_jitter)
            _ini_pos = np.maximum(int(_ne * fs) + _jitter, 0)
            # _noise_samples = np.random.randint(1, int(fs * noise_events_duration))

            _ini_pos = np.minimum(_ini_pos, size)
            _end_pos = np.minimum(_ini_pos + _noise_samples - 1, size)
            noise[_ini_pos:_end_pos, :] += np.random.normal(0, 10 ** (noise_events_power_delta_db / 20) * 0.1,
                                                            size=(_end_pos - _ini_pos, n_channels))

    return noise, stationary_noise_var


def generate_line_noise(size: int | None = None,
                        fs: type(u.Quantity) | None = None,
                        n_channels: int | None = None,
                        line_noise_mixing_matrix: type(np.array) | None = None,
                        line_noise_amplitude: u.Quantity = 10 * u.uV,
                        line_noise_frequency: u.Quantity = 50 * u.Hz,
                        line_noise_n_harmonics: int = 1):
    # generate line noise
    if line_noise_n_harmonics is None:
        line_noise_n_harmonics = int(np.floor((fs / 2) / line_noise_frequency))
    if line_noise_mixing_matrix is None:
        line_noise_mixing_matrix = np.diag(np.ones(n_channels))
    line_coeff = line_noise_mixing_matrix * line_noise_amplitude
    _line_signal = np.zeros((size, 1))
    for _n in range(line_noise_n_harmonics):
        _line_signal[:, 0] = _line_signal[:, 0] + 1 / (_n + 1) * np.sin(
            2.0 * np.pi * line_noise_frequency * (_n + 1) * np.arange(0, size) * u.rad / fs)

    line_signal = np.tile(_line_signal, (1, n_channels)).dot(line_coeff)
    return line_signal
