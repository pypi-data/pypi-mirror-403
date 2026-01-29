import numpy as np
from peegy.processing.statistics.definitions import HotellingTSquareTest
from peegy.definitions.channel_definitions import ChannelItem
from peegy.processing.tools.eeg_epoch_operators import w_mean, effective_sampling_size
from peegy.processing.tools.epochs_processing_tools import goertzel
from peegy.tools.units.unit_tools import set_default_unit
import astropy.units as u
import scipy.stats as st
from tqdm import tqdm


def hotelling_t_square_test(samples=np.array([]),
                            weights: type(np.array) | None = None,
                            channels: np.array([ChannelItem]) = None,
                            **kwargs):
    """
    Compute Hotelling T2 test on samples
    :param samples: np.array with samples to perform the test (time x channels x trials)
    :param weights: if passed, statistics will be computed using weighted statistics
    :param channels: list of ChannelItems use to generate pandas data frame with the label of each channel
    :param kwargs:
    :return: pandas data frame with statistical tests
    """
    samples = set_default_unit(samples, u.uV)
    _test_data = []
    if not samples.size:
        return None
    if weights is None:
        weights = np.ones(samples.shape[1::]) * u.dimensionless_unscaled
    if weights.ndim == 3:
        # we assume that the same weight is use for each row
        weights = weights[0, :, :]

    mean_data = w_mean(samples, weights=weights)
    dof = effective_sampling_size(weights, axis=1)
    data_demeaned = samples - mean_data[..., None]
    with np.errstate(divide='ignore', invalid='ignore'):
        for _ch in tqdm(range(samples.shape[1]), desc="Hotelling-T2"):
            # _cov_mat = np.cov(data_ch.value.squeeze(), aweights=_weights.value.squeeze()) * data_ch.unit ** 2.0
            data_ch = data_demeaned[:, _ch, :]
            mean_ch = mean_data[:, _ch]
            _cov_mat = np.cov(data_ch.value, aweights=weights[_ch, :].value) * data_ch.unit ** 2.0
            if _cov_mat.ndim == 0:
                _t_square = dof[_ch] * mean_ch.dot(1 / _cov_mat).dot(mean_ch.T)
            else:
                _t_square = dof[_ch] * mean_ch.dot(np.linalg.pinv(_cov_mat)).dot(mean_ch.T)
            _t_square = _t_square.value
            n_p = data_ch.shape[0]
            n_n = dof[_ch]
            _f = (n_n - n_p) / (n_p * (n_n - 1.0)) * _t_square
            _d1 = n_p
            _d2 = np.maximum(n_n - n_p, 0)
            _f_95 = st.f.ppf(0.95, _d1, _d2)
            if _d2 > 0:
                p = 1 - st.f.cdf(_f, _d1, _d2)
            else:
                p = 1
                _f_95 = np.inf

            # compute residual noise from circular variance
            _rms = np.sqrt(np.mean(mean_ch ** 2.0))
            _rn = np.sqrt(np.sum(data_ch ** 2.0)) / (data_ch.shape[1] - 1)
            _snr = np.maximum(_f - 1, 0.0 * u.dimensionless_unscaled)
            if channels is not None:
                _channel = channels[_ch].label
            else:
                _channel = str(_ch)

            # _L = ((2 * (self.split_sweep_count[i] - 1) * D * F95)./(
            # self.split_sweep_count(i) * (self.split_sweep_count(i) - 2))) ** 2

            test = HotellingTSquareTest(t_square=_t_square,
                                        df_1=_d1,
                                        df_2=_d2,
                                        n_epochs=samples.shape[2],
                                        f=_f,
                                        p_value=p,
                                        mean_amplitude=_rms,
                                        mean_phase=0 * u.rad,
                                        rn=_rn,
                                        snr=_snr,
                                        snr_db=10 * np.log10(_snr) if _snr > 0.0 else
                                        -np.inf * u.dimensionless_unscaled,
                                        snr_critic_db=10 * np.log10(_f_95 - 1),
                                        snr_critic=_f_95 - 1,
                                        f_critic=_f_95,
                                        channel=_channel,
                                        **kwargs)
            _test_data.append(test)
    return _test_data


def f_test(f_values: np.array([]) = None,
           df_numerator: float = 5,
           df_noise: np.array([]) = None,
           alpha: float = 0.05
           ) -> (float, float, float, float, float):
    """
    Compute F-Test for input samples.
    The degrees of freedom for signal are from Elberling 1984.
    https://www.tandfonline.com/doi/abs/10.3109/01050398409043059
    :param df_numerator: degrees of freedom of the numerator of the F-test
    :param df_noise: The estimated degrees of freedom of the noise used to estimate the input SNR
    :param f_values: f_values to test
    :param alpha: the statistical level for significance
    :return: pandas data frame with statistical tests
    """

    df_num = df_numerator
    df_den = df_noise
    f_critic = st.f.ppf(1 - alpha, df_num, df_den)
    p_value = 1 - st.f.cdf(f_values, df_num, df_den)

    return f_critic, df_num, df_den, p_value


def phase_locking_value(
        data: type(np.array) | None = None,
        alpha: float = 0.05,
        weights: type(np.array) | None = None) -> np.array:
    """
    Compute phase-locking value (PLV) using Rayleigh test
    :param data: time x channels x trials numpy array in the time domain
    :param alpha: float indicating the alpha value for significance
    :param weights: trial by trial weights
    :return: phase-locking value (frequency x channels), z-scores (frequency x channels), z_critic (float), p_values
    (frequency x channels), mean angles (frequency x channels in rads), degrees of freedom, residual_noise estimation
    """
    if weights is None:
        weights = np.ones(data.shape)
    _dof = effective_sampling_size(weights)
    # for the moment we assume that the same weight across time is applied so that it can be factor out from fft
    dof = np.min(_dof, axis=0, keepdims=False).squeeze()[None, :]
    _weights = np.min(weights, axis=0)[None, :, :]
    yfft = np.fft.rfft(data, axis=0)
    spectral_mean = w_mean(yfft, _weights)
    diff = yfft - spectral_mean[:, :, None]
    # compute weighted standard deviation
    noise = np.sqrt(w_mean(np.abs(diff) ** 2, _weights) / dof)
    # scale to match time domain amplitudes
    spectral_amp = 2 * np.abs(spectral_mean) / data.shape[0]
    residual_noise = 2 * np.abs(noise) / data.shape[0]
    # normalize
    norm = np.sqrt(np.abs(yfft * np.conj(yfft)))
    yfft = np.divide(yfft, norm, out=np.zeros_like(yfft), where=norm != 0)
    angles = np.angle(w_mean(yfft, _weights))
    plv = np.abs(w_mean(yfft, _weights))
    z = dof * plv ** 2

    # D.Wilkie. Rayleigh Test for Randomness of Circular Data".Applied Statistics.1983.
    tmp = np.ones(z.shape)
    _idx_tmp = (dof < 50).squeeze()

    if np.any(_idx_tmp):
        _tmp_correction = 1.0 + (2.0 * z - z * z) / (4.0 * dof) - (
                24.0 * z - 132.0 * z ** 2.0 + 76.0 * z ** 3.0 - 9.0 * z ** 4.0) / (288.0 * dof * dof)
        tmp[:, _idx_tmp] = _tmp_correction
    z_crit = -np.log(alpha) - (2 * np.log(alpha) + np.log(alpha) ** 2.0) / (4 * dof)
    p_values = np.exp(-z) * tmp

    return spectral_amp, plv, z, z_crit, p_values, angles, dof, residual_noise


def discrete_phase_locking_value(
        data: type(np.array) | None = None,
        alpha: float = 0.05,
        fs: float | None = None,
        frequency: float | None = None,
        weights: type(np.array) | None = None) -> np.array:
    """
    Compute spectral amplitude, phase, and  phase-locking value (PLV) using Rayleigh test for a single frequency
    component.
    :param data: time x channels x trials numpy array in the time domain
    :param alpha: float indicating the alpha value for significance
    :param fs: float indicating the sampling rate in Hz
    :param frequency: float indicating the frequency of interest
    :param weights: trial by trial weights
    :return: phase-locking value (frequency x channels), z-scores (frequency x channels), z_critic (float), p_values
    (frequency x channels), mean angles (frequency x channels in rads), degrees of freedom, residual_noise estimation
    """
    if weights is None:
        weights = np.ones((1, data.shape[1], data.shape[2]))
    _dof = effective_sampling_size(weights)
    # for the moment we assume that the same weight across time is applied so that it can be factor out from fft
    dof = np.min(_dof, axis=0, keepdims=False).squeeze()[None, :]

    yfft, exact_frequency = goertzel(data, fs, frequency)
    spectral_amp = np.abs(np.sum(yfft * weights, axis=2) / np.sum(weights, axis=2))
    diff = yfft - spectral_amp[:, :, None]
    noise = np.sqrt(np.var(diff, ddof=1, axis=2) / dof)
    # scale to match time domain amplitudes
    spectral_amp = 2 * spectral_amp / data.shape[0]
    residual_noise = 2 * noise / data.shape[0]
    yfft = yfft / np.abs(yfft)
    angles = np.angle(np.sum(yfft * weights, axis=2) / np.sum(weights, axis=2))
    plv = np.abs(np.sum(yfft * weights, axis=2) / np.sum(weights, axis=2))
    z = dof * plv ** 2
    # D.Wilkie. Rayleigh Test for Randomness of Circular Data".Applied Statistics.1983.
    tmp = np.ones(z.shape)
    _idx_tmp = (dof < 50).squeeze()

    if np.any(_idx_tmp):
        _tmp_correction = 1.0 + (2.0 * z - z * z) / (4.0 * dof) - (24.0 * z - 132.0 * z ** 2.0 +
                                                                   76.0 * z ** 3.0 - 9.0 * z ** 4.0) / (
                                      288.0 * dof * dof)
        tmp[:, _idx_tmp] = _tmp_correction
    z_crit = -np.log(alpha) - (2 * np.log(alpha) + np.log(alpha) ** 2.0) / (4 * dof)
    p_values = np.exp(-z) * tmp

    return spectral_amp, plv, z, z_crit, p_values, angles, dof, residual_noise


def get_discrete_frequency_value(
        data: type(np.array) | None = None,
        fs: float | None = None,
        frequency: float | None = None,
        weights: type(np.array) | None = None) -> np.array:
    """
    Compute spectral amplitude for a single frequency
    component.
    :param data: time x channels x trials numpy array in the time domain
    :param alpha: float indicating the alpha value for significance
    :param fs: float indicating the sampling rate in Hz
    :param frequency: float indicating the frequency of interest
    :param weights: trial by trial weights
    :return: frequency amplitudes
    """
    if weights is None:
        weights = np.ones(data.shape[1::])
    if weights.ndim == 3:
        # we assume that the same weight is use for each row
        weights = weights[0, :, :]
    dof = effective_sampling_size(weights, axis=1)
    yfft, _exact_freq = goertzel(data, fs, frequency)

    spectral_amp = np.abs(np.sum(yfft * weights, axis=2) / np.sum(weights, axis=1))
    diff = yfft - spectral_amp[:, :, None]
    noise = np.sqrt(np.var(diff, ddof=1, axis=2) / dof)
    # scale to match time domain amplitudes
    spectral_amp = 2 * spectral_amp / data.shape[0]
    residual_noise = 2 * noise / data.shape[0]
    yfft = 2 * yfft / data.shape[0]
    return yfft, spectral_amp, residual_noise


def freq_bin_phase_locking_value(
        yfft: type(np.array) | None = None,
        alpha: float = 0.05,
        weights: type(np.array) | None = None) -> np.array:
    """
    Compute phase, and  phase-locking value (PLV) using Rayleigh test for an array of trials from a single frequency
    component.
    :param yfft: fft_bin (complex) x channels x trials numpy array in the time domain
    :param alpha: float indicating the alpha value for significance
    :param frequency: float indicating the frequency of interest
    :param weights: trial by trial weights
    :return: phase-locking value (frequency x channels), z-scores (frequency x channels), z_critic (float), p_values
    (frequency x channels), mean angles (frequency x channels in rads), degrees of freedom, residual_noise estimation
    """
    if weights is None:
        weights = np.ones(yfft.shape[1::])
    if weights.ndim == 3:
        # we assume that the same weight is use for each row
        weights = weights[0, :, :]
    dof = effective_sampling_size(weights, axis=1)
    spectral_mean = np.sum(yfft * weights, axis=2) / np.sum(weights, axis=1)
    spectral_amp = np.abs(spectral_mean)
    # subtract evoked response from all epochs
    noise_epochs = yfft - spectral_mean[:, :, None]
    noise_epochs_amp = np.abs(noise_epochs)
    noise_epochs_ang = np.angle(noise_epochs)
    mean_x = np.sum(noise_epochs_amp * np.cos(noise_epochs_ang) * weights,
                    axis=2,
                    keepdims=True) / np.sum(weights, axis=1, keepdims=True)
    mean_y = np.sum(noise_epochs_amp * np.sin(noise_epochs_ang) * weights,
                    axis=2,
                    keepdims=True) / np.sum(weights, axis=1, keepdims=True)
    var_x = np.sum(((noise_epochs_amp * np.cos(noise_epochs_ang) - mean_x) ** 2.0) * weights,
                   axis=2,
                   keepdims=True) / np.sum(weights, axis=1, keepdims=True)
    var_y = np.sum(((noise_epochs_amp * np.sin(noise_epochs_ang) - mean_y) ** 2.0) * weights,
                   axis=2,
                   keepdims=True) / np.sum(weights, axis=1, keepdims=True)
    # we assumed that variance on x and y axis are independent from each other
    # this encapsulates the variance: sigma_r^2 <= variance <= sigma_r^2 + 4 * sum(w_angular*r_i*mean(r_i))
    total_var = var_x + var_y
    noise = np.sqrt(total_var / dof[:, None])
    # the same than np.std(yfft, axis=2) / np.sqrt(yfft.shape[2])
    residual_noise = noise[:, :, 0]
    # scale to match time domain amplitudes
    yfft = yfft / np.abs(yfft)
    angles = np.angle(np.sum(yfft * weights, axis=2) / np.sum(weights, axis=1))
    plv = np.abs(np.sum(yfft * weights, axis=2) / np.sum(weights, axis=1))
    z = dof * plv ** 2

    # D.Wilkie. Rayleigh Test for Randomness of Circular Data".Applied Statistics.1983.
    tmp = np.ones(z.shape)
    _idx_tmp = (dof < 50).squeeze()

    if np.any(_idx_tmp):
        _tmp_correction = 1.0 + (2.0 * z - z * z) / (4.0 * dof) - (
                24.0 * z - 132.0 * z ** 2.0 + 76.0 * z ** 3.0 - 9.0 * z ** 4.0) / (288.0 * dof * dof)
        tmp[:, _idx_tmp] = _tmp_correction
    z_crit = -np.log(alpha) - (2 * np.log(alpha) + np.log(alpha) ** 2.0) / (4 * dof)
    p_values = np.exp(-z) * tmp

    return spectral_amp, plv, z, z_crit, p_values, angles, dof, residual_noise
