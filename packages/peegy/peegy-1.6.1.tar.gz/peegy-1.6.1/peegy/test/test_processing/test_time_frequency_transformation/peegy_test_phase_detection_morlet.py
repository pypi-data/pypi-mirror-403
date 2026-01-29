import astropy.units as u
from scipy import signal
import matplotlib.pyplot as plt
import numpy as np
# from ssqueezepy import Wavelet
# import pywt


reference_frequency = 40 * u.Hz
half_width = 2 / reference_frequency
fs = 1000 * u.Hz

# fwhm = (4 / reference_frequency)
# b = 2 * (fwhm / (2 * np.sqrt(2 * np.log(2)))) ** 2.0
# c = reference_frequency
# morlet = 'cmor{:}-{:}'.format(b.value, c.value)
# wavelet = pywt.ContinuousWavelet(morlet)
# [wav, time] = wavelet.wavefun(level=16)
# scale = pywt.frequency2scale(wavelet=wavelet, freq=reference_frequency/fs.value, precision=16).value
# print(pywt.scale2frequency(wavelet, [scale], precision=16) / (1/fs))
# freq = np.arange(0, wav.size) * 1 / np.mean(np.diff(time)) / wav.size
# yfft = np.fft.fft(wav, axis=0)
#
# plt.figure()
# plt.plot(freq, np.abs(yfft))
# plt.plot(reference_frequency.value, np.abs(yfft).max(), 'o')
# plt.xlim([0, 2 * reference_frequency.value])
# plt.xlabel('Frequency [Hz]')
# plt.show()
#
# n_wavelet = wav / np.max(np.abs(wav))
# _ini = np.argwhere(np.abs(n_wavelet) >= 0.5)[0]
# _end = np.argwhere(np.abs(n_wavelet) >= 0.5)[-1]
# full_width_half_max = (time[_end] - time[_ini])
# plt.figure()
# plt.plot(time, np.abs(n_wavelet))
# plt.plot(time[_ini], np.abs(n_wavelet)[_ini], 'o')
# plt.plot(time[_end], np.abs(n_wavelet)[_end], 'o')
# plt.plot(time, np.real(n_wavelet))
# plt.xlabel('Time [s]')
# plt.show()

# M is just for plot. We use CWT for convolution
M = 1000
time = np.arange(M) / fs
s = (half_width.to(u.s) * fs)
w = reference_frequency * (2 * s * np.pi) / fs
wavelet = signal.morlet2(M, s, w)
n_wavelet = wavelet / np.max(np.abs(wavelet))
_ini = np.argwhere(np.abs(n_wavelet) >= 0.5)[0]
_end = np.argwhere(np.abs(n_wavelet) >= 0.5)[-1]
full_width_half_max = (time[_end] - time[_ini])

plt.plot(time, n_wavelet)
plt.plot(time, np.abs(n_wavelet))
plt.plot(time, np.real(n_wavelet))
plt.plot(time[_ini], np.abs(n_wavelet)[_ini], 'o')
plt.plot(time[_end], np.abs(n_wavelet)[_end], 'o')
plt.show()


# define test stimuli and reference signal
duration = 1 * u.s
time = np.arange(0, int(duration * fs)) / fs
ini_phase = np.pi / 2 * u.rad
# reference is cosine convolved with wavelet so that phase includes the filter response
reference_signal = (np.cos(2 * np.pi * reference_frequency * u.rad * time[:, None] - ini_phase) +
                    1j * np.sin(2 * np.pi * reference_frequency * u.rad * time[:, None] - ini_phase))
reference_signal = reference_signal / np.abs(reference_signal)
noise_amp = 0.1
fig1, axs = plt.subplots(2)
# now we estimate the phase changes for a range of phase transitions at the mid-point of the time axis
for phase in np.linspace(0, np.pi, 10) * u.rad:
    # generate test signal
    data = (np.cos(2 * np.pi * u.rad * reference_frequency * time - ini_phase)[:, None] +
            noise_amp * np.random.randn(time.size, 1))
    # generate phase transition
    data[data.shape[0] // 10::] = (np.cos(2 * np.pi * u.rad * reference_frequency * time[data.shape[0] // 10::] -
                                          ini_phase + phase)[:, None] +
                                   noise_amp * np.random.randn(time[data.shape[0] // 10::].size, 1))

    data[data.shape[0] // 4::] = (np.cos(2 * np.pi * u.rad * reference_frequency * time[data.shape[0] // 4::] -
                                         ini_phase + 2 * phase)[:, None] +
                                  noise_amp * np.random.randn(time[data.shape[0] // 4::].size, 1))

    # convolve signal with complex-wavelet
    y_filter = np.zeros(data.shape, dtype=complex)
    ####
    # wavelet = Wavelet('morlet')
    # Wx, scales = cwt(data.value.T, wavelet)
    # freqs_cwt = scale_to_freq(scales, wavelet, y_filter.shape[0], fs=fs.value)
    # _ifreq = np.argwhere(freqs_cwt == reference_frequency.value)
    # y_filter = Wx.T[:, _ifreq[0], ...]
    ####
    if data.ndim == 1:
        y_filter = signal.cwt(data.value, signal.morlet2, widths=[s], w=w)
        # y_filter, _ = pywt.cwt(data.value,
        #                        wavelet=wavelet,
        #                        scales=[scale],
        #                        sampling_period=1 / fs.value)
        y_filter = y_filter[:, None, None]
    if data.ndim == 2:
        for _i in range(y_filter.shape[1]):
            y_filter[:, _i] = signal.cwt(data[:, _i].value, signal.morlet2,
                                         widths=[s], w=w)
            # y_filter[:, _i], _ = pywt.cwt(data[:, _i].value,
            #                               wavelet=wavelet,
            #                               scales=[scale],
            #                               sampling_period=1 / fs.value)
            y_filter = y_filter[:, None]
    if data.ndim == 3:
        for _i in range(y_filter.shape[1]):
            for _j in range(y_filter.shape[2]):
                y_filter[:, _i, _j] = signal.cwt(data[:, _i, _j].value, signal.morlet2,
                                                 widths=[s], w=w)
                # y_filter[:, _i, _j], _ = pywt.cwt(data[:, _i, _j].value,
                #                                   wavelet=wavelet,
                #                                   scales=[scale],
                #                                   sampling_period=1 / fs.value)
    # make unitary complex vector for phase estimation
    normalized_vector = y_filter / np.abs(y_filter)
    # if data comes in trials, then we average
    average_vector = np.mean(normalized_vector, axis=2)
    axs[0].plot(time, data, label='signal')
    axs[0].plot(time, np.real(reference_signal), label='ref')
    # compute phase difference
    # instantaneous_phase_difference = np.unwrap(np.angle(average_vector) * u.rad - np.angle(reference_signal), axis=0)
    instantaneous_phase_difference = (np.unwrap(np.angle(reference_signal), axis=0) -
                                      np.unwrap(np.angle(average_vector) * u.rad, axis=0)
                                      )
    axs[1].plot(time, instantaneous_phase_difference * 180 / np.pi, label='{:}'.format(phase * 180 / (np.pi * u.rad)))
    axs[1].legend()
plt.show()
plt.show()
