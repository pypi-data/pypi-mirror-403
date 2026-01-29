from scipy.signal import hilbert, group_delay
import astropy.units as u
import numpy as np
from peegy.definitions.channel_definitions import Domain
from peegy.processing.pipe.definitions import InputOutputProcess
from peegy.processing.tools.detection.definitions import TimeROI
from scipy import signal
import pyfftw


class InstantaneousPhase(InputOutputProcess):
    def __init__(self, input_process=InputOutputProcess,
                 roi_windows: np.array([TimeROI]) = None,
                 relative_difference: bool = True,
                 reference_frequency: type(u.quantity) | None = None,
                 reference_time: type(u.quantity) | None = None,
                 **kwargs):
        """
        This InputOutputProcess computes the instantaneous phase of the data in  the inputprocess
        :param input_process: InputOutputProcess Class
        :param roi_windows: time windows used to perform some measures (snr, rms)
        :param relative_difference: if True, the difference using the initial phase as a reference will be returned
        :param reference_frequency: frequency to compute the relative phase difference
        :param reference_time: time point used to extract reference instantaneous phase
        :param kwargs: extra parameters to be passed to the superclass
        """
        super(InstantaneousPhase, self).__init__(input_process=input_process, **kwargs)
        self.roi_windows = roi_windows
        self.relative_difference = relative_difference
        self.reference_frequency = reference_frequency
        self.reference_time = np.array([reference_time.value]) * reference_time.unit

    def transform_data(self):
        analytic_signal = hilbert(self.input_node.data, axis=0)
        instantaneous_phase = np.unwrap(np.angle(analytic_signal), axis=0) * u.rad
        if self.relative_difference and self.reference_frequency is not None:
            ref_index = self.input_node.x_to_samples(self.reference_time)
            ref = np.cos(2 * np.pi * self.reference_frequency * u.rad * self.input_node.x[:, None] *
                         np.ones(self.input_node.data.shape) + instantaneous_phase[ref_index, :])
            relative_analytic_signal = hilbert(ref, axis=0)
            relative_instantaneous_phase = np.unwrap(np.angle(relative_analytic_signal), axis=0) * u.rad
            instantaneous_phase = relative_instantaneous_phase - instantaneous_phase
            instantaneous_phase = instantaneous_phase - instantaneous_phase[ref_index, :]
        self.output_node.data = instantaneous_phase
        # for the moment we use the rms of the entire epoch as a noise measurement
        self.output_node.rn = np.sqrt(np.mean(instantaneous_phase ** 2, axis=0))


class InstantaneousEnvelope(InputOutputProcess):
    def __init__(self, input_process=InputOutputProcess,
                 roi_windows: np.array([TimeROI]) = None,
                 **kwargs):
        """
        This InputOutputProcess computes the instantaneous phase of the data in  the inputprocess
        :param input_process: InputOutputProcess Class
        :param roi_windows: time windows used to perform some measures (snr, rms)
        :param kwargs: extra parameters to be passed to the superclass
        """
        super(InstantaneousEnvelope, self).__init__(input_process=input_process, **kwargs)
        self.roi_windows = roi_windows

    def transform_data(self):
        analytic_signal = hilbert(self.input_node.data, axis=0)
        amplitude_envelope = np.abs(analytic_signal) * self.input_node.data.unit
        self.output_node.data = amplitude_envelope
        # for the moment we use the rms of the entire epoch as a noise measurement
        self.output_node.rn = np.sqrt(np.mean(amplitude_envelope ** 2, axis=0))


class InstantaneousFrequency(InputOutputProcess):
    def __init__(self, input_process=InputOutputProcess,
                 roi_windows: np.array([TimeROI]) = None,
                 **kwargs):
        """
        This InputOutputProcess computes the instantaneous frequency of the data in  the inputprocess
        :param input_process: InputOutputProcess Class
        :param roi_windows: time windows used to perform some measures (snr, rms)
        :param kwargs: extra parameters to be passed to the superclass
        """
        super(InstantaneousFrequency, self).__init__(input_process=input_process, **kwargs)
        self.roi_windows = roi_windows

    def transform_data(self):
        analytic_signal = hilbert(self.input_node.data, axis=0)
        instantaneous_phase = np.unwrap(np.angle(analytic_signal), axis=0)
        instantaneous_frequency = (np.diff(instantaneous_phase, axis=0) /
                                   (2.0 * np.pi) * self.input_node.fs)
        self.output_node.data = instantaneous_frequency * u.dimensionless_unscaled


class GroupDelay(InputOutputProcess):
    def __init__(self, input_process=InputOutputProcess,
                 roi_windows: np.array([TimeROI]) = None,
                 frequencies: np.array(u.Quantity) = None,
                 **kwargs):
        """
        This InputOutputProcess computes the instantaneous frequency of the data in  the inputprocess
        :param input_process: InputOutputProcess Class
        :param roi_windows: time windows used to perform some measures (snr, rms)
        :param kwargs: extra parameters to be passed to the superclass
        """
        super(GroupDelay, self).__init__(input_process=input_process, **kwargs)
        self.roi_windows = roi_windows
        self.frequencies = frequencies

    def transform_data(self):
        if self.frequencies is None:
            self.frequencies = np.fft.rfftfreq(self.input_node.data.shape[0], 1 / self.input_node.fs)
            n_fft = self.input_node.data.shape[0]
        else:
            n_fft = self.frequencies.shape[0]
        gd = np.zeros((self.frequencies.shape[0], self.input_node.data.shape[1]))
        for _ch in range(self.input_node.data.shape[1]):
            w, g = group_delay((self.input_node.data[:, _ch], 1), w=self.frequencies.value,
                               fs=self.input_node.fs.value)
            gd[:, _ch] = g
        self.output_node.n_fft = n_fft
        self.output_node.data = gd / self.input_node.fs
        self.output_node.domain = Domain.frequency


class RelativeInstantaneousPhaseFrequency(InputOutputProcess):
    def __init__(self, input_process=InputOutputProcess,
                 reference_roi_window: TimeROI | None = None,
                 relative_difference: bool = True,
                 reference_frequency: type(u.quantity) | None = None,
                 wavelet_half_amplitude_time: u.Quantity = 80 * u.ms,
                 align_reference_phase: bool = True,
                 align_reference_time: u.Quantity = 0 * u.s,
                 **kwargs):
        """
        This InputOutputProcess computes the instantaneous phase of the data in  the inputprocess
        :param input_process: InputOutputProcess Class
        :param reference_roi_windows: reference time window to center phase
        :param relative_difference: if True, the difference using the initial phase as a reference will be returned
        :param reference_frequency: frequency to compute the relative phase difference
        :param wavelet_half_amplitude_time: full width half maximum length (in time) of the wavelet half-amplitude
        :param align_reference_phase: if true, the starting phase will by aligned to a given time given by
        align_reference_time
        :param align_reference_time: reference time used to align the phase of reference signal to the the input signal
        :param kwargs: extra parameters to be passed to the superclass
        """
        super(RelativeInstantaneousPhaseFrequency, self).__init__(input_process=input_process, **kwargs)
        self.reference_roi_window = reference_roi_window
        self.relative_difference = relative_difference
        self.reference_frequency = reference_frequency
        self.wavelet_half_amplitude_time = wavelet_half_amplitude_time
        self.align_reference_phase = align_reference_phase
        self.align_reference_time = align_reference_time

    def transform_data(self):
        s = (self.wavelet_half_amplitude_time.to(u.s) / 2 * self.input_node.fs.to(u.Hz))
        w = self.reference_frequency * (2 * s * np.pi) / self.input_node.fs
        y_filter = np.zeros(self.input_node.data.shape, dtype=complex)
        reference_signal = (np.cos(2 * np.pi * self.reference_frequency * u.rad * self.input_node.x) +
                            1j * np.sin(2 * np.pi * self.reference_frequency * u.rad * self.input_node.x))[:, None]
        reference_signal = reference_signal / np.abs(reference_signal)
        if self.input_node.data.ndim == 1:
            y_filter = signal.cwt(self.input_node.data.value, signal.morlet2, widths=[s], w=w)
        if self.input_node.data.ndim == 2:
            for _i in range(y_filter.shape[1]):
                y_filter[:, _i] = signal.cwt(self.input_node.data[:, _i].value, signal.morlet2,
                                             widths=[s], w=w)
        if self.input_node.data.ndim == 3:
            for _i in range(y_filter.shape[1]):
                for _j in range(y_filter.shape[2]):
                    y_filter[:, _i, _j] = signal.cwt(self.input_node.data[:, _i, _j].value, signal.morlet2,
                                                     widths=[s], w=w)
        normalized_vector = y_filter / (np.abs(y_filter)) * u.dimensionless_unscaled

        if self.align_reference_phase:
            _reference_signal = reference_signal * np.ones(normalized_vector.shape)
            _ref_sample = self.input_node.x_to_samples([self.align_reference_time])
            _phase = np.angle(normalized_vector[_ref_sample[0], ...])
            _ref_phase = np.angle(_reference_signal[_ref_sample[0], ...])
            _delta_phase = _phase - _ref_phase
            reference_signal = _reference_signal * np.exp(1j * _delta_phase.value)
        if self.input_node.data.ndim == 3:
            normalized_vector = np.mean(normalized_vector, axis=2)
        # get each phase
        reference_phase = np.unwrap(np.angle(reference_signal), axis=0)
        signal_phase = np.unwrap(np.angle(normalized_vector), axis=0)
        instantaneous_phase_difference = reference_phase - signal_phase
        if self.reference_roi_window is not None:
            _samples = self.reference_roi_window.get_roi_samples(self.input_node)
            reference_samples = np.arange(_samples[0], _samples[1])

            instantaneous_phase_difference = (
                    instantaneous_phase_difference -
                    np.mean(instantaneous_phase_difference[reference_samples, ...], axis=0))
        self.output_node.data = instantaneous_phase_difference
        # for the moment we use the rms of the entire epoch as a noise measurement
        self.output_node.rn = np.sqrt(np.mean(instantaneous_phase_difference ** 2, axis=0))

    @staticmethod
    def phase_value(v1, v2):
        vv1 = np.array([np.real(v1), np.imag(v1)]).T
        vv2 = np.array([np.real(v2), np.imag(v2)]).T
        cosine_angle = np.dot(vv1, vv2) / (np.linalg.norm(vv1) * np.linalg.norm(vv2))
        current_angle = np.arccos(cosine_angle)
        return current_angle


class InstantaneousPhaseChange(InputOutputProcess):
    def __init__(self, input_process=InputOutputProcess,
                 reference_roi_window: TimeROI | None = None,
                 relative_difference: bool = True,
                 reference_frequency: type(u.quantity) | None = None,
                 wavelet_half_amplitude_time: u.Quantity = 80 * u.ms,
                 **kwargs):
        """
        This InputOutputProcess computes the instantaneous phase of the data in  the inputprocess
        :param input_process: InputOutputProcess Class
        :param reference_roi_windows: reference time window to center phase
        :param relative_difference: if True, the difference using the initial phase as a reference will be returned
        :param reference_frequency: frequency to compute the relative phase difference
        :param wavelet_half_amplitude_time: length (in time) for the wavelength half-amplitude decay
        :param kwargs: extra parameters to be passed to the superclass
        """
        super(InstantaneousPhaseChange, self).__init__(input_process=input_process, **kwargs)
        self.reference_roi_window = reference_roi_window
        self.reference_frequency = reference_frequency
        self.wavelet_half_amplitude_time = wavelet_half_amplitude_time

    def transform_data(self):
        s = (self.wavelet_half_amplitude_time.to(u.s) * self.input_node.fs.to(u.Hz))
        w = self.reference_frequency * (2 * s * np.pi) / self.input_node.fs
        y_filter = np.zeros(self.input_node.data.shape, dtype=complex)
        if self.input_node.data.ndim == 1:
            y_filter = signal.cwt(self.input_node.data.value, signal.morlet2, widths=[s], w=w)
        if self.input_node.data.ndim == 2:
            for _i in range(y_filter.shape[1]):
                y_filter[:, _i] = signal.cwt(self.input_node.data[:, _i].value, signal.morlet2,
                                             widths=[s], w=w)
        if self.input_node.data.ndim == 3:
            for _i in range(y_filter.shape[1]):
                for _j in range(y_filter.shape[2]):
                    y_filter[:, _i, _j] = signal.cwt(self.input_node.data[:, _i, _j].value, signal.morlet2,
                                                     widths=[s], w=w)
        normalized_vector = y_filter / np.abs(y_filter)
        if self.input_node.data.ndim == 3:
            normalized_vector = np.mean(normalized_vector, axis=2)
        instantaneous_phase = np.unwrap(np.angle(normalized_vector) * u.rad,
                                        axis=0)
        dy = - np.gradient(instantaneous_phase, axis=0)
        instantaneous_phase_change = - dy * (1 / self.reference_frequency) * 1 / (2 * np.pi)
        if self.reference_roi_window is not None:
            _samples = self.reference_roi_window.get_roi_samples(self.input_node)
            reference_samples = np.arange(_samples[0], _samples[1])

            instantaneous_phase_change = (
                    instantaneous_phase_change -
                    np.mean(instantaneous_phase_change[reference_samples, :], axis=0))
        self.output_node.data = instantaneous_phase_change
        # for the moment we use the rms of the entire epoch as a noise measurement
        self.output_node.rn = np.sqrt(np.mean(instantaneous_phase_change ** 2, axis=0))


class TimeToFrequency(InputOutputProcess):
    def __init__(self, input_process=InputOutputProcess,
                 **kwargs):
        """
        This InputOutputProcess transform time-domain data to frequency domain
        :param input_process: InputOutputProcess Class
        :param kwargs: extra parameters to be passed to the superclass
        """
        super(TimeToFrequency, self).__init__(input_process=input_process, **kwargs)

    def transform_data(self):
        assert self.input_node.domain == Domain.time
        time_data = self.input_node.data
        n = self.input_node.data.shape[0]
        fft_within_epoch = pyfftw.builders.rfft(
            time_data,
            n=n,
            overwrite_input=False,
            planner_effort="FFTW_ESTIMATE",
            axis=0,
            threads=1,
        )

        self.output_node.data = fft_within_epoch() * self.input_node.data.unit * 2 / n
        self.output_node.n_fft = self.input_node.data.shape[0]
        self.output_node.domain = Domain.frequency
        self.output_node.frequency_resolution = self.input_node.fs / n
