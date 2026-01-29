"""
.. _tut-acc-sim:

Test spatial filtering with evoked response (Simulation)
==============================

This example simulates an evoked responses with non-stationary noise.
We illustrate how wegithed averaging and DSS can lead to much better results in terms of recovering the data.
This example follows that by Alain de Cheveigné (http://audition.ens.fr/adc/NoiseTools/) but it has been extended
to include non-stationary noise and weighted average.

"""
# Enable below for interactive backend
import matplotlib
if 'Qt5Agg' in matplotlib.rcsetup.all_backends:
    matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
import peegy.processing.tools.filters.spatial_filtering.spatial_filtering as sf
from peegy.processing.tools.eeg_epoch_operators import et_time_shifted_xcovariance, et_mmat, \
    et_weighted_covariance
from peegy.processing.tools.epochs_processing_tools import et_mean
import numpy as np
import matplotlib.gridspec as gridspec
from scipy.stats import norm
from typing import List
__author__ = 'jundurraga'


def plot_covariances(covariances: List[np.array] | None = None):
    gs = gridspec.GridSpec(1, len(covariances))
    fig = plt.figure()
    for _i, _cov in enumerate(covariances):
        ax = plt.subplot(gs[0, _i])
        maxis = ax.matshow(_cov)
        plt.colorbar(maxis)
    return fig


def plot_data_results(data_list: List[np.array] | None = None, titles: List[str] | None = None):
    gs = gridspec.GridSpec(1, len(data_list))
    fig = plt.figure()
    for _i, (_data, _title) in enumerate(zip(data_list, titles)):
        ax = plt.subplot(gs[0, _i])
        ax.plot(_data)
        ax.set_title(_title)
    return fig


# create synthetic data
n_samples = 1000 * 3
n_channels = 30
n_trials = 100
noise_dim = 20  # dimensionality of noise
source = np.concatenate((
    np.zeros((n_samples//3, )),
    np.sin(2 * np.pi * np.arange(n_samples / 3) / (n_samples / 3)),
    np.zeros((n_samples//3, ))))

np.random.seed(2)
mix_m = norm.ppf(np.random.rand(n_channels, 1))
s = source * mix_m
s = np.tile(np.expand_dims(s.T, axis=2), (1, 1, n_trials))
SNR = 0.1

noise_unmixed = norm.ppf(np.random.rand(noise_dim * n_trials * n_samples))
noise_unmixed = np.reshape(noise_unmixed, [n_samples, noise_dim, n_trials], order='F')

noise_mix = norm.ppf(np.random.rand(n_channels * noise_dim))
noise_mix = np.reshape(noise_mix, [noise_dim, n_channels], order='F')
noise = et_mmat(noise_unmixed, noise_mix)

scaled_source = SNR * s / np.std(s)
scaled_noise = noise / np.std(noise)

# generate non-stationary noise
for i in np.arange(1, 4):
    _ini = i*20
    _end = _ini + 10
    scaled_noise[:, :, _ini: _end] += 1e2 * i * scaled_noise[:, :, _ini: _end]
# for i in np.arange(50, 100):
#     scaled_noise[:, :, i] += 1e3 * scaled_noise[:, :, i]
# mix data

data = scaled_noise + scaled_source
n_components = np.arange(1)
# standard averaging of the data
s_ave, s_w, s_rn, *_ = et_mean(data, block_size=1, weighted=False)
# weighted averaging of the data
w_ave, w_w, w_rn, *_ = et_mean(data, block_size=1, weighted=True, weight_across_epochs=False)


# clean data using dss with weighted average as bias. Data covariance weighted with same weights
cref, tw_ref = et_weighted_covariance(data)
cref = cref / tw_ref
c1, tw1 = et_weighted_covariance(w_ave)
c1 = c1 / tw1
# plot_covariances(covariances=[cref, c1, cref, c1])
todss, pwr0, pwr1, n0, n1 = sf.nt_dss0(cref, c1)
z0 = et_mmat(data, todss)
cov_1, tw_cov = et_time_shifted_xcovariance(z0, data, wy=w_w)
cov_1 = cov_1 / tw_cov
data_clean0 = et_mmat(z0[:, n_components, :], cov_1[n_components, :])
# data_clean0 = et_mmat(z0[:, n_components, :], cov_1[n_components, :])


# clean data using dss with standard average as bias and standard average weights for the covariance.
cref, tw_ref = et_weighted_covariance(data, w=s_w)
c1, tw1 = et_weighted_covariance(s_ave)
cref = cref / tw_ref
c1 = c1 / tw1
todss, pwr0, pwr1, n0, n1 = sf.nt_dss0(cref, c1)
z1 = et_mmat(data, todss)
cov_1, tw_cov = et_time_shifted_xcovariance(z1, data, wy=s_w)
cov_1 = cov_1 / tw_cov
data_clean1 = et_mmat(z1[:, n_components, :], cov_1[n_components, :])

# clean data using dss with weighted average as bias. Covariance weighted with standard average weights
cref, tw_ref = et_weighted_covariance(data, w=s_w)
c1, tw1 = et_weighted_covariance(w_ave)
cref = cref / tw_ref
c1 = c1 / tw1
todss, pwr0, pwr1, n0, n1 = sf.nt_dss0(cref, c1, keep1=1e-4)
z2 = et_mmat(data, todss)
cov_1, tw_cov = et_time_shifted_xcovariance(z2, data, wy=s_w)
cov_1 = cov_1 / tw_cov
data_clean2 = et_mmat(z2[:, n_components, :], cov_1[n_components, :])

w_ave_0, *_ = et_mean(data_clean0, block_size=1, weighted=True, weight_across_epochs=False)
w_ave_1, *_ = et_mean(data_clean1, block_size=1, weighted=True, weight_across_epochs=False)
w_ave_2, *_ = et_mean(data_clean2, block_size=1, weighted=True, weight_across_epochs=False)
w_ave_z0, *_ = et_mean(z0[:, 0:3, :], block_size=1, weighted=True, weight_across_epochs=False)
w_ave_z1, *_ = et_mean(z1[:, 0:3, :], block_size=1, weighted=True, weight_across_epochs=False)
w_ave_z2, *_ = et_mean(z2[:, 0:3, :], block_size=1, weighted=True, weight_across_epochs=False)

plot_data_results([np.mean(scaled_source, axis=2),
                   s_ave,
                   w_ave,
                   w_ave_0,
                   w_ave_1,
                   w_ave_2,
                   w_ave_z0,
                   w_ave_z1,
                   w_ave_z2],
                  ['Target source',
                   'standard average',
                   'weighted average',
                   'w_cov & w_ave',
                   's_cov & s_ave',
                   's_cov & w_ave',
                   'components data_clean0',
                   'components data_clean1',
                   'components data_clean2',
                   ]
                  )
plt.show()
plt.show()
