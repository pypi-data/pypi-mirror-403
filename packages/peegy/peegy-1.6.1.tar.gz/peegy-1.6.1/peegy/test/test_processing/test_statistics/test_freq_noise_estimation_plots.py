"""
.. _tut-acc-sim:

Test spatial filtering with evoked response (Simulation)
==============================

This example simulates an evoked responses with non-stationary noise.
We illustrate how weighted averaging and DSS can lead to much better results in terms of recovering the data.
This example follows that by Alain de Cheveigné (http://audition.ens.fr/adc/NoiseTools/) but it has been extended
to include non-stationary noise and weighted average.

"""
import matplotlib.pyplot as plt
from peegy.processing.tools.eeg_epoch_operators import et_mmat
import numpy as np
from scipy.stats import norm
from astropy import units as u
# Enable below for interactive backend
import matplotlib
if 'Qt5Agg' in matplotlib.rcsetup.all_backends:
    matplotlib.use('Qt5Agg')
__author__ = 'jundurraga'

# create synthetic data
nsamples = 500
nchans = 1
ntrials = 100
noise_dim = 20  # dimensionality of noise
freq = 100
fs = 1000

source = np.sin(2 * np.pi * np.arange(nsamples) / fs * freq)
np.random.seed(2)
mix_m = np.ones((nchans, 1))
s = source * mix_m
s = np.tile(np.expand_dims(s.T, axis=2), (1, 1, ntrials))
SNR = 5

noise_unmixed = norm.ppf(np.random.rand(noise_dim * ntrials * nsamples))
noise_unmixed = np.reshape(noise_unmixed, [nsamples, noise_dim, ntrials], order='F')

noise_mix = norm.ppf(np.random.rand(nchans * noise_dim))
noise_mix = np.reshape(noise_mix, [noise_dim, nchans], order='F')
noise = et_mmat(noise_unmixed, noise_mix)

scaled_source = s * u.uV / np.std(s)
scaled_noise = (1 / SNR) * np.std(s) * noise * u.uV / np.std(noise)

# mix data
data = scaled_noise + scaled_source
frequencies = freq * (1 + np.arange(1))

yfft = np.fft.fft(data, axis=0).value
freqs = np.arange(0, data.shape[0]) * fs / data.shape[0]
k = np.argmin(np.abs(freqs - freq))
yfft_bin = yfft[k, ...]

r = np.abs(yfft_bin)
ang = np.angle(yfft_bin)
mean_yfft_bin = np.abs(np.mean(yfft, axis=2))

plt.figure()
plt.plot(r * np.cos(ang), r * np.sin(ang), marker='o', color='b', linestyle="None")

noise_bin = yfft_bin - np.mean(yfft_bin, axis=1, keepdims=True)
mean_yfft_noise_bin = np.abs(np.mean(noise_bin, axis=1))
# noise_bin_power = np.sqrt(np.mean(np.abs(noise_bin) ** 2.0, axis=1) / noise_bin.shape[1])
noise_bin_power = np.var(noise_bin, axis=1, ddof=1) / noise_bin.shape[1]

# actual noise
yfft_noise = np.fft.fft(scaled_noise, axis=0).value
yfft_noise_bin = yfft_noise[k, ...]
yfft_noise_mean = np.mean(yfft_noise_bin, axis=1, keepdims=True)
yfft_noise_mean_power = np.abs(yfft_noise_mean) ** 2.0

noise_across_bins = np.sum(np.abs(np.mean(yfft_noise, axis=2)) ** 2, axis=0) / yfft_noise.shape[0]


plt.figure()
plt.plot(yfft_noise_mean_power)
plt.plot(noise_bin_power)
plt.show()

plt.figure()
plt.plot(freqs, mean_yfft_bin ** 2)
[plt.axhline(y=np.mean(_nb), color='orange') for _nb in noise_bin_power]
[plt.axhline(y=np.mean(_nb), color='red') for _nb in yfft_noise_mean_power]
plt.axhline(y=noise_across_bins, color='blue')
plt.show()


plt.figure()
plt.plot(freqs, np.abs(np.mean(yfft_noise, axis=2)) ** 2)
[plt.axhline(y=np.mean(_nb), color='orange') for _nb in noise_bin_power]
[plt.axhline(y=np.mean(_nb), color='red') for _nb in yfft_noise_mean_power]
plt.show()


####
r_n = np.abs(noise_bin)
ang_n = np.angle(noise_bin)
plt.plot(r_n * np.cos(ang_n), r_n * np.sin(ang_n), marker='o', color='orange', linestyle="None")
plt.plot(r_n * np.cos(ang_n), r_n * np.sin(ang_n), marker='o', color='orange', linestyle="None")
