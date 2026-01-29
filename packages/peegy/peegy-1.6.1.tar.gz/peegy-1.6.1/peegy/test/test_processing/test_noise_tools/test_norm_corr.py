"""
Created on Tue Dec 16 10:55:37 2014

@author: jundurraga-ucl
"""
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
n_channels = 1
n_trials = 1200
noise_dim = 1  # dimensionality of noise
source, _ = abr(fs=fs, time_length=duration)
n_samples = source.shape[0]
coeff = [1]
block_size = 100
s = source * coeff
s_std = np.std(s, axis=0)
s = np.tile(np.expand_dims(s, axis=2), (1, 1, n_trials))

desired_snr = 80.0
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

data = noise + s * (1 + 2 * np.random.random((1, 1, s.shape[2])))
data = 100 * np.reshape(data, [-1, 1], 'F').squeeze().value
x_corr = np.zeros(data.shape)
for _i in np.arange(data.shape[0] - source.shape[0]):
    _ini = _i
    _end = np.minimum(_i + source.shape[0], data.shape[0])
    x1 = data[_ini: _end]
    x2 = source.squeeze().value
    x_corr[_i] = np.sum(x1 * x2) / np.sqrt(np.sum(x1 ** 2) * np.sum(x2 ** 2))
constructed = np.convolve(source.squeeze(), x_corr)
plt.plot(constructed / constructed.max())
plt.plot(data / data.max())
