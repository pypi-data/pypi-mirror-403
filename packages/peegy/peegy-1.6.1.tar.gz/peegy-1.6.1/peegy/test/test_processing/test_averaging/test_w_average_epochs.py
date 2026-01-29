"""
Created on Tue Dec 16 10:55:37 2014

@author: jundurraga-ucl
"""
from peegy.processing.tools import epochs_processing_tools as ept
from peegy.processing.tools import eeg_epoch_operators as eop
from peegy.processing.tools.template_generator.auditory_waveforms import abr
from peegy.tools.signal_generator.noise_functions import generate_modulated_noise
import numpy as np
import matplotlib.pyplot as plt
import astropy.units as u
# Enable below for interactive backend
import matplotlib
if 'Qt5Agg' in matplotlib.rcsetup.all_backends:
    matplotlib.use('Qt5Agg')

# create synthetic data
fs = 8000.0 * u.Hz
duration = 16 * u.ms
n_channels = 4
n_trials = 1200
noise_dim = 4  # dimensionality of noise
source, _ = abr(fs=fs, time_length=duration)
n_samples = source.shape[0]
coeff = np.ones(n_channels//2) * 0.5 / (n_channels / 2)
coeff = np.expand_dims(np.hstack((coeff, coeff)), 0)
block_size = 100
s = source * coeff
s_std = np.std(s, axis=0)
s = np.tile(np.expand_dims(s, axis=2), (1, 1, n_trials))

desired_snr = 5.0
ini_std = 10.0 ** (-desired_snr / 20.0) * s_std * n_trials ** 0.5
theoretical_rn = ini_std / n_trials ** 0.5

noise = generate_modulated_noise(fs=fs.value,
                                 duration=source.shape[0] * n_trials / fs.value,
                                 f_noise_low=0,
                                 f_noise_high=4000,
                                 attenuation=0,
                                 n_channels=n_channels) * u.uV

noise = ini_std * noise / np.std(noise, axis=0)
noise = eop.et_fold(noise, n_samples)

# add non-stationary noise
for i in range(3):
    _ini = n_trials//4 + i * 6 * block_size
    noise[:, :, _ini: _ini + block_size] = noise[:, :, _ini: _ini + block_size] * 5

s[:, 0] = s[:, 0] * 0.5
data = noise + s
w_ave, w_w, rn_w, cumulative_rn_w, w_fft, nw, *_ = ept.et_mean(epochs=data,
                                                               block_size=block_size,
                                                               samples_distance=10,
                                                               weighted=True)

w_ave_2, w_w_2, rn_w_2, cumulative_rn_w_2, w_fft_2, nw_2, *_ = ept.et_mean(epochs=data,
                                                                           weight_across_epochs=False,
                                                                           weighted=True)

s_ave, w_s, rn_s, cumulative_rn_s, s_fft, ns, *_ = ept.et_mean(epochs=data,
                                                               block_size=block_size,
                                                               samples_distance=10,
                                                               weighted=False)


snr_w, s_var_w = ept.et_snr_in_rois(data=w_ave, rn=rn_w)
snr_w_2, s_var_w_2 = ept.et_snr_in_rois(data=w_ave_2, rn=rn_w_2)
snr_s, s_var_s = ept.et_snr_in_rois(data=s_ave, rn=rn_s)
print('snr_w in dB = {:}'.format(10 * np.log10(snr_w)))
print('snr_w_2 in dB = {:}'.format(10 * np.log10(snr_w_2)))
print('snr_s in dB = {:}'.format(10 * np.log10(snr_s)))

colour_w = 'red'
colour_w_2 = 'orange'
colour_s = 'blue'

fig = plt.figure()
ax = fig.add_subplot(111)
ax.plot(w_w[0, :, :].T, color=colour_w)
ax.plot(w_w_2[0, :, :].T, color=colour_w_2)
ax.plot(w_s[0, :, :].T, color=colour_s)
ax.set_ylabel("W ")
ax.set_xlabel("Block number")
plt.show()

fig = plt.figure()
ax = fig.add_subplot(111)
ax.set_title('Noise')
ax.plot(np.std(noise, axis=0).T)
ax.set_ylabel("Noise RMS")
ax.set_xlabel("Trial number")
plt.show()


fig = plt.figure()
ax = fig.add_subplot(141)
ax.plot(np.mean(s, axis=2))
ax.set_title('Target signal')

ax = fig.add_subplot(142)
ax.plot(data[:, 0, :], color=colour_w, alpha=0.005)
ax.plot(w_ave, color='black')
ax.set_title('Weighted average')

ax = fig.add_subplot(143)
ax.plot(data[:, 0, :], color=colour_w_2, alpha=0.005)
ax.plot(w_ave_2, color='black')
ax.set_title('Weighted average 2')

ax = fig.add_subplot(144)
ax.plot(data[:, 0, :], color=colour_s, alpha=0.005)
ax.plot(s_ave, color='black')
ax.set_title('Standard average')
plt.show()

fig = plt.figure()
ax = fig.add_subplot(111)
ax.plot(cumulative_rn_s, color=colour_s)
ax.set_title('Residual noise')
ax.plot(cumulative_rn_w, color=colour_w)
ax.plot(cumulative_rn_w_2, color=colour_w_2)
plt.show()


fig = plt.figure()
ax = fig.add_subplot(111)
ax.plot(10 * np.log10(snr_s), label='final snr_s', color=colour_s)
ax.plot(10 * np.log10(snr_w), label='final snr_w', color=colour_w)
ax.plot(10 * np.log10(snr_w_2), label='final snr_w_2', color=colour_w_2)

ax.set_ylabel("SNR [dB]")
ax.set_xlabel("Channel")
ax.axhline(y=desired_snr)
fig.legend()
plt.show()

cum_snr_w = np.array([])
cum_snr_w_2 = np.array([])
cum_snr_s = np.array([])
cum_snr_w_data = np.array([])
cum_snr_s_data = np.array([])

for i in range(data.shape[2]//block_size):
    end_pos = block_size + i*block_size
    sub_set = data[:, :, 0: end_pos]
    _w_ave, _, _rn_w, *_ = ept.et_mean(epochs=sub_set,
                                       block_size=block_size,
                                       samples_distance=10,
                                       weight_across_epochs=True,
                                       weighted=True)
    _w_ave_2, _, _rn_w_2, *_ = ept.et_mean(epochs=sub_set,
                                           weight_across_epochs=False)

    _s_ave, _, _rn_s,  *_ = ept.et_mean(epochs=sub_set,
                                        block_size=block_size,
                                        samples_distance=10,
                                        weighted=False)

    _rn_w_data = np.std(_w_ave - s[:, :, 0], axis=0)
    _rn_w_data_2 = np.std(_w_ave_2 - s[:, :, 0], axis=0)
    _rn_s_data = np.std(_s_ave - s[:, :, 0], axis=0)
    _snr_w, s_var_w = ept.et_snr_in_rois(data=_w_ave, rn=_rn_w)
    _snr_w_2, s_var_w_2 = ept.et_snr_in_rois(data=_w_ave_2, rn=_rn_w_2)
    _snr_s, s_var_s = ept.et_snr_in_rois(data=_s_ave, rn=_rn_s)
    _snr_w_data, s_var_w_data = ept.et_snr_in_rois(data=_w_ave, rn=_rn_w_data)
    _snr_w_2_data, s_var_w_data_2 = ept.et_snr_in_rois(data=_w_ave_2, rn=_rn_w_data_2)
    _snr_s_data, s_var_s_data = ept.et_snr_in_rois(data=_s_ave, rn=_rn_s_data)

    if i == 0:
        cum_snr_w = _snr_w
        cum_snr_w_2 = _snr_w_2
        cum_snr_s = _snr_s
        cum_snr_w_data = _snr_w_data
        cum_snr_w_2_data = _snr_w_2_data
        cum_snr_s_data = _snr_s_data
    else:
        cum_snr_w = np.hstack([cum_snr_w, _snr_w])
        cum_snr_w_2 = np.hstack([cum_snr_w_2, _snr_w_2])
        cum_snr_s = np.hstack([cum_snr_s, _snr_s])
        cum_snr_w_data = np.hstack([cum_snr_w_data, _snr_w_data])
        cum_snr_w_2_data = np.hstack([cum_snr_w_2_data, _snr_w_2_data])
        cum_snr_s_data = np.hstack([cum_snr_s_data, _snr_s_data])

fig = plt.figure()
ax = fig.add_subplot(111)
ax.plot(10 * np.log10(cum_snr_w.T + 1e-3), color=colour_w)
ax.plot(10 * np.log10(cum_snr_w_2.T + 1e-3), color=colour_w_2)
ax.plot(10 * np.log10(cum_snr_s.T + 1e-3), color=colour_s)
ax.axhline(y=desired_snr)
ax.set_ylabel("SNR [dB]")
ax.set_xlabel("Block number")
plt.show()

fig = plt.figure()
ax = fig.add_subplot(321)
ax.plot(10 * np.log10(cum_snr_w.T + 1e-3), color=colour_w)
ax.axhline(y=desired_snr)
ax.set_title("SNRw [dB]")
ax.set_ylabel("SNR [dB]")
ax.set_xlabel("Block number")

ax = fig.add_subplot(322)
ax.plot(10 * np.log10(cum_snr_w_data.T + 1e-3), color=colour_w)
ax.axhline(y=desired_snr)
ax.set_title("SNRw real [dB]")
ax.set_ylabel("SNR [dB]")
ax.set_xlabel("Block number")

ax = fig.add_subplot(323)
ax.plot(10 * np.log10(cum_snr_w_2.T + 1e-3), color=colour_w_2)
ax.axhline(y=desired_snr)
ax.set_title("SNRw_2 [dB]")
ax.set_ylabel("SNR_2 [dB]")
ax.set_xlabel("Block number")

ax = fig.add_subplot(324)
ax.plot(10 * np.log10(cum_snr_w_2_data.T + 1e-3), color=colour_w_2)
ax.axhline(y=desired_snr)
ax.set_title("SNRw_2 real [dB]")
ax.set_ylabel("SNR [dB]")
ax.set_xlabel("Block number")

ax = fig.add_subplot(325)
ax.plot(10 * np.log10(cum_snr_s.T + + 1e-3), color=colour_s)
ax.axhline(y=desired_snr)
ax.set_title("SNRs [dB]")
ax.set_ylabel("SNR [dB]")
ax.set_xlabel("Block number")

ax = fig.add_subplot(326)
ax.set_title("SNRs real [dB]")
ax.plot(10 * np.log10(cum_snr_s_data.T + 1e-3), color=colour_s)
ax.axhline(y=desired_snr)
ax.set_ylabel("SNR [dB]")
ax.set_xlabel("Block number")
plt.show()
