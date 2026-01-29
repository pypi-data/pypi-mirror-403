from scipy.signal import hilbert
import astropy.units as u
import numpy as np
from scipy import signal
import matplotlib.pyplot as plt


def phase_value(v1, v2):
    vv1 = np.array([np.real(v1), np.imag(v1)]).T
    vv2 = np.array([np.real(v2), np.imag(v2)]).T
    cosine_angle = np.dot(vv1, vv2) / (np.linalg.norm(vv1) * np.linalg.norm(vv2))
    current_angle = np.arccos(cosine_angle)
    return current_angle


reference_frequency = 40 * u.Hz
half_width = 10 * u.ms
fs = 400 * u.Hz
M = int(10 * half_width * fs)
time = np.arange(M) / fs
s = (half_width.to(u.s) * fs)
w = reference_frequency * (2 * s * np.pi) / fs
wavelet = signal.morlet2(M, s, w)
plt.plot(time, abs(wavelet) / np.max(abs(wavelet)))
plt.plot(time, np.real(wavelet) / np.max(abs(wavelet)))
plt.show()

fs = 512 * u.Hz
reference_frequency = 80 * u.Hz
M = 100
s = 16.0
w = reference_frequency * (2 * s * np.pi) / fs
wavelet = signal.morlet2(M, s, w.value)
time = np.arange(0, 512) / fs
ini_phase = np.pi/2 * u.rad
reference_signal = (np.cos(2 * np.pi * reference_frequency * u.rad * time[:, None] - 0*ini_phase) +
                    1j * np.sin(2 * np.pi * reference_frequency * u.rad * time[:, None] - 0*ini_phase))

reference_signal = reference_signal * np.ones((reference_signal.shape[0], 10))
for phase in np.linspace(0, np.pi, 10) * u.rad:
    data = (np.cos(2 * np.pi * u.rad * reference_frequency * time - ini_phase)[:, None] +
            0.01 * np.random.randn(time.size, 1))

    data[data.shape[0] // 2::] = (np.cos(2 * np.pi * u.rad * reference_frequency * time[data.shape[0] // 2::] -
                                         ini_phase + phase)[:, None] +
                                  0.01 * np.random.randn(time[data.shape[0] // 2::].size, 1))

    y_filter = np.zeros(data.shape, dtype=complex)
    if data.ndim == 1:
        y_filter = signal.cwt(data.value, signal.morlet2, widths=[s], w=w)
    if data.ndim == 2:
        for _i in range(y_filter.shape[1]):
            y_filter[:, _i] = signal.cwt(data[:, _i].value, signal.morlet2,
                                         widths=[s], w=w)
    if data.ndim == 3:
        for _i in range(y_filter.shape[1]):
            for _j in range(y_filter.shape[2]):
                y_filter[:, _i, _j] = signal.cwt(data[:, _i, _j].value, signal.morlet2,
                                                 widths=[s], w=w)
    y_filter = hilbert(data, axis=0)
    # signal_instantaneous_phase = np.unwrap(np.angle(y_filter), axis=0) *
    # u.rad * np.ones((signal_instantaneous_phase.shape[0], 10))
    # plt.plot(time, signal_instantaneous_phase * 180 / np.pi, label='signal_phase')
    plt.figure(1)
    plt.plot(time, data, label='signal')
    plt.plot(time, np.real(reference_signal), label='signal')
    # plt.show()
    reference_instantaneous_phase = np.unwrap(np.angle(reference_signal), axis=0)
    plt.plot(time, reference_instantaneous_phase * 180 / np.pi, label='reference_phase')
    # if data.ndim <= 2:
    #     relative_instantaneous_phase = reference_instantaneous_phase - signal_instantaneous_phase
    # if data.ndim == 3:
    #     relative_instantaneous_phase = reference_instantaneous_phase[:, None] - signal_instantaneous_phase

    # relative_instantaneous_phase_2 = phase(y_filter, reference_signal)
    # M = 10
    # s = 1.0
    # w = 1 * reference_frequency * (2 * s * np.pi) / fs
    # wavelet = signal.morlet(M, s, w)
    # y_filter = signal.cwt(data.value.squeeze(), signal.morlet2, widths=[s], w=w).squeeze()
    # y_filter = signal.convolve(data.squeeze(), wavelet, 'same')[:, None]
    # y_filter = hilbert(np.real(y_filter), axis=0)
    # y_filter = signal.cwt(np.flip(y_filter, axis=0), signal.morlet2, widths=[s], w=w)[:, None]
    phase_vectorized = np.vectorize(phase_value)
    relative_instantaneous_phase_3 = np.unwrap(phase_vectorized(y_filter, reference_signal.value), axis=0)
    # mul = y_filter * reference_signal
    # dot = (np.real(mul) + np.imag(mul)) / (np.linalg.norm(np.real(mul)) * np.linalg.norm(np.imag(mul)))
    # relative_instantaneous_phase_2 = np.unwrap(np.arccos(dot), axis=0)
    plt.figure(2)
    # plt.plot(time, relative_instantaneous_phase * 180 / np.pi, label='hilbert')
    plt.plot(time, relative_instantaneous_phase_3.squeeze() * 180 / np.pi, label='projection_hilbert')
    # plt.plot(time, relative_instantaneous_phase_3 * 180 / np.pi, label='projection_morlet')
    plt.legend()
plt.show()
plt.show()
