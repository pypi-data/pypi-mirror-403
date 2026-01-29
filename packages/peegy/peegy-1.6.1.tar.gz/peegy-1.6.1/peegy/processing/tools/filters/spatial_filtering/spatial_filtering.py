import numpy as np
import peegy.processing.tools.eeg_epoch_operators as eo
from peegy.tools.units.unit_tools import set_default_unit
import astropy.units as u
import warnings
from scipy.linalg import cholesky, eigh

__author__ = 'jundurraga'


def nt_dss0(c0: np.array = np.array([]),
            c1: np.array = np.array([]),
            keep0: int | None = None,
            keep1: float = 1e-9,
            perc0: float = 1,
            perc1: float | None = None
            ):
    """
    Generate DSS matrix
    :param c0: average covariance matrix across all epochs
    :param c1: covariance matrix of average data
    :param keep0: number of components to keep. This parameter is useful to remove negligent components and to add
    numerical stability.
    :param keep1: float indicating the a threshold (relative to the maximum eigenvalue) to keep components and to add
    numerical stability.
    :param perc0: float indicating a percentage of explained variance that would be used as a threshold to keep
    components when whitening data.
    :param perc1: float indicating a percentage of explained variance that would be used as a threshold to keep
    components when generating dss rotation.
    :return: dss matrix, unbiased power, and biased power.
    """
    # make sure covariance matrix is symmetric_positive_definite
    c0 = nearest_symmetric_positive_definite(c0)
    c1 = nearest_symmetric_positive_definite(c1)
    # whitening and selection of components for stability
    if perc0 is not None:
        keep0 = int(c0.shape[0] * perc0)
    topcs_1, evs_1 = nt_pcarot(c0, keep0)
    evs_1 = np.abs(evs_1)
    if keep1 is not None:
        idx = np.where(evs_1 / np.max(evs_1) > keep1)[0]
        topcs_1 = topcs_1[:, idx]
        evs_1 = evs_1[idx]

    # apply PCA and whitening to the biased covariance and ensure that non-negative eigen values are produced
    n1 = np.diag(np.sqrt(1 / evs_1))
    c2 = n1.T.dot(topcs_1.T).dot(c1).dot(topcs_1).dot(n1)
    # matrix to convert PCA-whitened data to DSS
    topcs_2, evs_2 = nt_pcarot(c2, keep0)

    if perc1 is not None:
        n_evs_2 = evs_2 / np.sum(evs_2)
        _thr2 = np.argwhere(np.cumsum(n_evs_2) > perc1)
        _n2 = _thr2[0] if _thr2.size else evs_2.size - 1
        _idx_to_keep2 = np.arange(_n2 + 1)
        topcs_2 = topcs_2[:, _idx_to_keep2]
        # evs_2 = evs_2[_idx_to_keep2]

    # DSS matrix (raw data to normalized DSS)
    todss = topcs_1.dot(n1).dot(topcs_2)
    n2 = np.diagonal(todss.T.dot(c0).dot(todss))
    if np.any(n2 <= 0):
        warnings.warn("""
        Negative or zero normalization value in DSS filter.
        This is usually caused by numerical errors on very low eigenvalue components. Please check the whitening
        threshold. Usually increasing this threshold helps to overcome this issue.
        """)

    todss = todss.dot(np.diag(1 / np.sqrt(n2)))  # adjust so that components are normalized
    # number of components per rotation
    n_0 = evs_1.size
    n_1 = evs_2.size
    # power per DSS component
    pwr0 = np.sqrt(np.sum((c0.T.dot(todss) ** 2), axis=0))  # unbiased
    pwr1 = np.sqrt(np.sum((c1.T.dot(todss) ** 2), axis=0))  # biased
    return todss, pwr0, pwr1, n_0, n_1


def nt_pcarot(cov: np.array = np.array([]),
              n: int = 0):
    eigen_val, eigen_vec = np.linalg.eig(cov)
    eigen_vec = np.real(eigen_vec)
    eigen_val = np.real(eigen_val)
    idx = np.argsort(eigen_val)[::-1]
    if n:
        idx = idx[0: n]
    return eigen_vec[:, idx], eigen_val[idx]


def nt_bias_fft(x: np.array = np.array([]),
                normalized_frequencies: np.array = np.array([]),
                w: np.array = np.array([])):
    if w.size == 0:
        w = np.ones(x.shape)
    c0, _ = eo.et_covariance(x, w=w)
    c1, _ = eo.et_freq_weighted_cov(x, w=w, normalized_frequencies=normalized_frequencies)
    return c0, c1


def nt_bias_fft2(x: np.array = np.array([]),
                 normalized_frequencies: np.array = np.array([]),
                 w: np.array = np.array([])):
    if w.size == 0:
        w = np.ones(x.shape)
    w_ave = eo.w_mean(x, weights=w)
    c0, t0 = eo.et_freq_weighted_cov(x, normalized_frequencies=normalized_frequencies)
    c1, t1 = eo.et_freq_weighted_cov(w_ave, normalized_frequencies=normalized_frequencies)
    return c0, c1, t0, t1


def nearest_symmetric_positive_definite(cov: type(np.array) | None = None):
    """
    Estimate the nearest symmetric positive definite covariance matrix.
    Implementation based on https://se.mathworks.com/matlabcentral/fileexchange/42885-nearestspd?s_tid=mwa_osa_a
    :param cov: the covariance matrix
    :return: the nearest symmetric positive definite covariance matrix.
    """
    cov = set_default_unit(cov, u.dimensionless_unscaled)
    # symmetrize cov into sym_cov
    sym_cov = (cov + cov.T) / 2
    # Compute the symmetric polar factor of sym_cov as h, which is SPD
    _u, _s, _v = np.linalg.svd(sym_cov)
    _h = _v.T.dot(np.diag(_s)).dot(_v)
    # get cov_hat in the above formula
    cov_hat = (sym_cov + _h) / 2

    # ensure symmetry
    cov_hat = (cov_hat + cov_hat.T) / 2
    # test that cov_hat is in fact PD. If it is not so, then tweak it just a bit.
    is_spd = False
    k = 0
    while not is_spd:
        try:
            cholesky(cov_hat)
            is_spd = True
        except np.linalg.LinAlgError:
            is_spd = False
        k = k + 1
        if not is_spd:
            # Ahat failed the chol test. It must have been just a hair off,
            # due to floating point trash, so it is simplest now just to
            # tweak by adding a tiny multiple of an identity matrix.
            eig_val_cov = eigh(cov_hat, eigvals_only=True)
            min_eig = np.min(eig_val_cov)
            cov_hat = cov_hat + (-min_eig * k ** 2 + np.spacing(min_eig)) * np.eye(*cov.shape) * cov.unit
            print('Finding nearest symmetric positive definite matrix iter: {:}'. format(k))
    return cov_hat
