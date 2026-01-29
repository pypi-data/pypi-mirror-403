import numpy as np
import scipy.linalg
from peegy.processing.tools.template_generator.auditory_waveforms import eog_template
from peegy.processing.tools.multiprocessing.multiprocessesing_filter import filt_data, filt_filt_data
from peegy.processing.tools.math_tools import get_local_maxima, get_local_minima
from peegy.processing.tools.filters.eegFiltering import bandpass_fir_win
from scipy import signal
import astropy.units as u
from tqdm import tqdm
import numba
from numba_progress import ProgressBar
from scipy.signal import correlate, windows
# from sklearn.neighbors import KernelDensity
import matplotlib.pyplot as plt


def rms(x: type(np.array) | None = None):
    return np.sqrt(np.mean(x ** 2.0))


def crest_factor(x: type(np.array) | None = None):
    return 20.0 * np.log10(np.max(np.abs(x)) / rms(x))


def unitary_step(x: type(np.array) | None = None):
    return (x > 0).astype(float)


def generate_eog_template(eog_data: type(np.array) | None = None,
                          fs: type(u.Quantity) | None = None,
                          template_width: u.Quantity = 0.5 * u.s,
                          low_pass: u.Quantity = 20 * u.Hz,
                          crest_factor_threshold=10,
                          minimum_interval_width: u.Quantity = 0.075 * u.s,
                          eog_peak_width: u.Quantity = 0.02 * u.s,
                          n_iterations: int = 1,
                          kernel_bandwidth: float = 0.15,
                          use_initial_template=True
                          ):
    """
    This function generate an EOG template
    :param eog_data: eog data
    :param fs: sampling rate
    :param template_width: maximum width of the EOG template
    :param low_pass: lowpass frequency applied to smooth the eog template
    :param crest_factor_threshold: crest factor (in dB) used to detect and provide a first guess template from the data
    :param minimum_interval_width: minimum interval between eye blinks (only used for initial guess)
    :param eog_peak_width: empirical width of an EOG blink (only used for initial guess)
    :param n_iterations: number of iterations to improve the template estimation
    :param kernel_bandwidth: factor use to control the with of the Gaussian kernel in threshold detection
    :param use_initial_template: if true, a template eye blinking will be used as starting point to find events
    :return: template, peaks location
    """
    eog_data_to_fit = eog_data
    if low_pass is not None:
        _b = bandpass_fir_win(high_pass=None, low_pass=low_pass, fs=fs)
    _rms = rms(eog_data_to_fit)
    # we check if positive or negative dominated waveform by looking the number of events with crest factors
    # larger than crest_factor_threshold in dB
    _amp_threshold = 10 ** (crest_factor_threshold / 20) * _rms
    positive_peaks, _ = signal.find_peaks(
        (eog_data_to_fit * unitary_step(eog_data_to_fit - _amp_threshold)).squeeze(),
        prominence=_amp_threshold.to_value(eog_data_to_fit.unit),
        distance=int(fs * minimum_interval_width),
        width=int(fs * eog_peak_width))
    negative_peaks, _ = signal.find_peaks(
        (-eog_data_to_fit.value * unitary_step(-eog_data_to_fit - _amp_threshold)).squeeze(),
        prominence=_amp_threshold.to_value(eog_data_to_fit.unit),
        distance=int(fs * minimum_interval_width),
        width=int(fs * eog_peak_width))

    # first we generate a template by detecting peaks from the data
    template = np.zeros((int(template_width * fs), 1)) * u.dimensionless_unscaled
    _invert_waveform = False
    if use_initial_template:
        template, _ = eog_template(fs=fs, event_duration=template_width)
        # fit twice to find which polarity is most effective to fit data
        _idx_peak_1, _, _ = detect_blinks(eog_data=eog_data_to_fit,
                                          template=template.squeeze(),
                                          kernel_bandwidth=kernel_bandwidth)
        reconstructed_1 = reconstruct_eog(data=eog_data_to_fit.reshape(-1, 1),
                                          template=template,
                                          blink_positions=_idx_peak_1)
        _idx_peak_2, _, _ = detect_blinks(eog_data=eog_data_to_fit,
                                          template=-template.squeeze(),
                                          kernel_bandwidth=kernel_bandwidth)
        reconstructed_2 = reconstruct_eog(data=eog_data_to_fit.reshape(-1, 1),
                                          template=-template,
                                          blink_positions=_idx_peak_2)
        r1 = 0
        if _idx_peak_1.size:
            r1 = np.abs(np.corrcoef(eog_data_to_fit.squeeze(), reconstructed_1.squeeze())[0, 1])
        r2 = 0
        if _idx_peak_2.size:
            r2 = np.abs(np.corrcoef(-eog_data_to_fit.squeeze(), reconstructed_2.squeeze())[0, 1])
        if r1 > r2:
            blink_positions = _idx_peak_1
        else:
            blink_positions = _idx_peak_2
            _invert_waveform = True
        if _invert_waveform:
            template = template * -1
    else:
        if positive_peaks.size and negative_peaks.size:
            _invert_waveform = positive_peaks.size < negative_peaks.size
        elif positive_peaks.size:
            _invert_waveform = False
        elif negative_peaks.size:
            _invert_waveform = True
        _sign = (-1) ** _invert_waveform
        _idx_peak, _ = signal.find_peaks(
            (_sign * eog_data_to_fit * unitary_step(_sign * eog_data_to_fit - _amp_threshold)).squeeze(),
            distance=int(fs * minimum_interval_width),
            prominence=_amp_threshold.to_value(eog_data_to_fit.unit),
            width=int(eog_peak_width * fs))
        blink_positions = np.array([])
        if _idx_peak.size:
            blink_positions = _idx_peak - int(template_width * fs) // 2
            blink_positions = blink_positions[
                np.logical_and(blink_positions >= 0,
                               blink_positions < eog_data_to_fit.shape[0] - np.round(template_width * fs) - 1)]
            template = generate_eog_template_from_peaks(blink_pos=blink_positions,
                                                        eog_data=eog_data_to_fit,
                                                        fs=fs,
                                                        template_width=template_width,
                                                        b=_b)
    z = np.array([])
    if blink_positions.size:
        # template = generate_eog_template_from_peaks(blink_pos=blink_positions,
        #                                             eog_data=eog_data_to_fit,
        #                                             fs=fs,
        #                                             template_width=template_width,
        #                                             b=_b)
        for _i in tqdm(np.arange(n_iterations), desc='EOG template iteration'):
            blink_positions, z, threshold = detect_blinks(eog_data=eog_data_to_fit,
                                                          template=template.squeeze(),
                                                          kernel_bandwidth=kernel_bandwidth)
            if blink_positions.size:
                template = generate_eog_template_from_peaks(blink_pos=blink_positions,
                                                            eog_data=eog_data_to_fit,
                                                            fs=fs,
                                                            template_width=template_width,
                                                            b=_b)
            print('Iteration {:}; {:} blinks detected; threshold {:}'.format(
                _i,
                blink_positions.size,
                threshold
                ))
    # print final correlation
    reconstructed_final = reconstruct_eog(data=eog_data_to_fit.reshape(-1, 1), template=template,
                                          blink_positions=blink_positions)
    if np.std(reconstructed_final.squeeze()) > 0:
        _score = np.abs(np.corrcoef(eog_data_to_fit.squeeze(), reconstructed_final.squeeze())[0, 1])
        print('Correlation between reconstructed and target EOG data: {:}'.format(_score))
    else:
        print('No EOG events were found')
    return template, blink_positions, z


def generate_eog_template_from_peaks(
        eog_data: type(np.array) | None = None,
        blink_pos: type(np.array) | None = None,
        fs: type(u.Quantity) | None = None,
        template_width: u.Quantity = 0.5 * u.s,
        b: type(np.array) | None = None,
        fade_duration: u.Quantity = 0.2 * u.s
):
    """
    This function will generate a template EOG based on the peaks position provided in idx_peak.
    :param eog_data: eog data
    :param blink_pos: location of peaks (in samples)
    :param fs: sampling rate
    :param b: filter coefficients
    :param template_width: width of the EOG template
    :param fade_duration: duration of the linear fade-in and fade-out applied to template
    :return: a template generated by weighted average of data centred on the peaks with a width defined by

    template_width.
    """
    template_samples = int(fs * template_width)
    h = np.zeros((template_samples, blink_pos.shape[0])) * eog_data.unit
    _index = np.arange(template_samples)
    for _i, _ev_pos in enumerate(blink_pos):
        _current_data = eog_data[_index + _ev_pos].squeeze()
        h[:, _i] = _current_data - np.mean(_current_data, axis=0)
    h = np.sort(h, axis=1)
    i1 = round(blink_pos.shape[0] * 0.25)
    i3 = round(blink_pos.shape[0] * 0.75)
    h = h[:, i1: i3]  # Amplitudes between perc. 25 - 75
    window = windows.hamming(i3 - i1)
    window = window / sum(window)  # normalization
    template = h.dot(window)[:, None]
    if b is not None:
        template = filt_data(data=template, b=b)
    # apply window to have smooth onset and offset
    _window = np.ones((template.size, 1))
    nw = int(np.minimum(np.maximum(fade_duration * fs, 0), template.shape[0] // 2))
    _window[0: nw] = (np.arange(0, nw) / (nw - 1)).reshape(-1, 1)
    _window[_window.size - nw::] = _window[0: nw][::-1]
    template = template * _window
    # normalize
    template = template * template.unit / np.sqrt(np.sum(template ** 2))

    return template


@numba.jit(nogil=True, nopython=True)
def get_cross_correlation_norm(data: type(np.array) | None = None,
                               template: type(np.array) | None = None,
                               progress_proxy: ProgressBar | None = None) -> np.array:
    """
    This function computes the normalized correlation between two different size numpy arrays.
    The template is assumed to be shorter than the full data.
    The output will return the correlation in which case, if the template exactly matches a portion of the data,
    regardless amplitude differences, the value at that point will be 1 or -1 (if negatively correlated).
    :param data: numpy array with full data set to find matches with template.
    :param template: numpy array containing the target template to be found in the data
    :param progress_proxy: ProgressBar object to print progress of the filter
    :return: normalized correlation function
    """
    assert data.shape[0] >= template.shape[0], r'data input length must be greater or equal than template'
    norm = np.zeros(data.shape)
    # get variance of template
    n2 = np.sum(template ** 2)
    for _i in np.arange(data.shape[0]):
        _ini = _i
        _end = np.minimum(_i + template.shape[0], data.shape[0])
        x1 = data[_ini: _end]
        # get variance of each segment in the data
        norm[_i] = np.sum(x1 ** 2)
        progress_proxy.update(1)
    # compute correlation norm as sqrt(var_data * variance_template)
    norm = np.sqrt(norm * n2)
    return norm


def match_filter(data: type(np.array) | None = None,
                 template: type(np.array) | None = None) -> np.array:
    """
    This function computes the normalized correlation between two different size numpy arrays.
    The template is assumed to be shorter than the full data.
    The output will return the correlation in which case, if the template exactly matches a portion of the data,
    regardless amplitude differences, the value at that point will be 1 or -1 (if negatively correlated).
    :param data: numpy array with full data set to find matches with template.
    :param template: numpy array containing the target template to be found in the data
    :return: normalized correlation function
    """
    assert data.shape[0] >= template.shape[0], r'data input length must be greater or equal than template'
    num_iterations = data.shape[0] - template.shape[0]
    # compute cross-correlation and resize it
    corr = correlate(data, template, 'full')
    corr = corr[template.shape[0] - 1: data.shape[0] + template.shape[0]]
    # estimate the norm of the cross-correlation
    with ProgressBar(total=num_iterations, desc='Detecting peaks via template correlation') as progress:
        norm = get_cross_correlation_norm(data=data, template=template, progress_proxy=progress)
    norm_xcor = corr / norm
    return norm_xcor


def detect_blinks_2(eog_data: type(np.array) | None = None,
                    template: type(np.array) | None = None,
                    threshold: float = 0.8,
                    ):
    """
    This function will use a match filter based on normalized cross correlation to detect the position at which the
    input template matches best.
    :param eog_data: numpy array with eog data
    :param template: template generated from the eog data (see generate_eog_template)
    :param threshold: the correlation threshold to detect peaks
    :return: the time of the detected event (as unitary dirac pulses) at which the template should be located
    """

    x_corr = match_filter(data=eog_data.value.squeeze(),
                          template=template.value.squeeze())
    dirac_peaks, _ = signal.find_peaks(np.abs(x_corr),
                                       prominence=threshold,
                                       width=1)
    return dirac_peaks


def detect_blinks(eog_data: type(np.array) | None = None,
                  template: type(np.array) | None = None,
                  kernel_bandwidth: float = 0.15
                  ):
    """
    This function will use a match filter based on normalized cross correlation to detect the position at which the
    input template matches best.
    :param eog_data: numpy array with eog data
    :param template: template generated from the eog data (see generate_eog_template)
    :param kernel_bandwidth: factor use to control the with of the Gaussian kernel in threshold detection
    :return: the time of the detected event (as unitary dirac pulses) at which the template should be located and
    correlation function between eeg_data and template
    """
    z = filt_data(data=eog_data, b=template.value[::-1], mode='valid', onset_padding=False).value
    _maxima, _idx_maxima = get_local_maxima(z.squeeze())
    threshold = detect_threshold(_maxima, kernel_bandwidth=kernel_bandwidth, show_histogram=False)
    blinks_pos = blink_event_positions(local_maxima=_maxima,
                                       idx_local_maxima=_idx_maxima,
                                       threshold=threshold,
                                       n_samples=eog_data.shape[0],
                                       impulse_response_length=template.shape[0])
    return blinks_pos, z, threshold


def histc(x, bins):
    map_to_bins = np.digitize(x, bins)  # Get indices of the bins to which each value in input array belongs.
    res = np.zeros(bins.shape)
    for el in map_to_bins:
        res[el - 1] += 1  # Increment appropriate bin.
    return res


def detect_threshold(peaks: np.array,
                     kernel_bandwidth: float = 0.15,
                     show_histogram=False):
    q3, q1 = np.percentile(peaks, [75, 25])
    iqr = q3 - q1
    bw = iqr * kernel_bandwidth
    # kde = KernelDensity(bandwidth=bw, kernel='gaussian')
    # kde.fit(peaks[:, None])
    x_d = np.linspace(peaks.min() - 5 * bw,
                      peaks.max() + 5 * bw, 1000).reshape(-1, 1)

    da = x_d[1] - x_d[0]  # Step in the  axis  of  amplitudes
    # Gaussian kernel
    kernel = np.exp(-(np.arange(-4.0 * bw, 4.0 * bw, da) ** 2 / (2 * bw ** 2))) * u.dimensionless_unscaled
    kernel = kernel / np.sum(kernel)
    _histogram = histc(peaks, x_d.squeeze()) * u.dimensionless_unscaled
    _pdf = filt_filt_data(data=_histogram.reshape(-1, 1), b=kernel, onset_padding=False)
    # _pdf = np.exp(kde.score_samples(x_d))
    _minima, _minima_idx = get_local_minima(_pdf.squeeze())
    _max_idx = _pdf.argmax()
    threshold = None
    if _minima_idx[_minima_idx > _max_idx].size:
        threshold_idx = _minima_idx[_minima_idx > _max_idx][0]
        threshold = float(x_d[threshold_idx])
    if show_histogram:
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.plot(x_d, _histogram)
        ax.plot(x_d[threshold_idx], _pdf[threshold_idx], 'o')
        ax.fill(x_d, _pdf, fc="#AAAAFF")
        fig.show()
    return threshold


def blink_event_positions(local_maxima: type(np.array) | None = None,
                          idx_local_maxima: type(np.array) | None = None,
                          threshold: float | None = None,
                          impulse_response_length: int | None = None,
                          n_samples: int | None = None):
    _position = idx_local_maxima[local_maxima > threshold]
    # lag compensation
    _position = _position - (impulse_response_length - 1)
    _position = _position[np.logical_and(_position >= 0, _position < n_samples - impulse_response_length - 1)]
    return _position


def reconstruct_eog(data: type(np.array) | None = None,
                    template: np.array = np.array([]),
                    blink_positions: np.array = np.array([])):
    """
    This function will reconstruct an EOG artefact by convolving the template (scaled to maximize similarity with input
    data) with unitary impulses located at the event_times
    :param data: data where EOG will be based from.
    :param template: an estimation of the EOG artefact
    :param blink_positions: location of the EOG artefacts
    :return: reconstructed EOG scaled to match the EOG in the input data
    """
    reconstructed = np.zeros(data.shape)
    if template.size and blink_positions.size:
        k = blink_positions.shape[0]
        rh = np.zeros((k, k))
        n_template = template.shape[0]
        auto_corr_h = correlate(template, template, 'full')
        auto_corr_h = auto_corr_h[(n_template - 1)::]
        for k_1 in range(k):
            for k_2 in range(k):
                dt = np.round(np.abs(blink_positions[k_2] - blink_positions[k_1]))
                if dt < n_template:
                    rh[k_1, k_2] = auto_corr_h[dt]
        inv_rh = scipy.linalg.pinv(rh)
        convolution_matrix = np.zeros(data.shape)
        template = template.squeeze()
        for _ch in tqdm(np.arange(data.shape[1]), desc='Computing EOG amplitudes'):
            z_channel = correlate(data[:, _ch], template, 'full')
            _positions = np.minimum(blink_positions + n_template, z_channel.shape[0] - 1)
            z_channel_amps = z_channel[_positions]  # Amplitudes for that channel
            amplitudes_ch = inv_rh.dot(z_channel_amps)
            convolution_matrix[blink_positions, _ch] = amplitudes_ch.squeeze()
        # convolve source with dirac train to generate blinks signal
        for _ch_idx in tqdm(np.arange(0, convolution_matrix.shape[1]), desc='Reconstructing EOG artefacts'):
            reconstructed[:, _ch_idx] = filt_data(
                data=template[:, None],
                b=convolution_matrix[:, _ch_idx].reshape(-1, 1).flatten(),
                mode='full', onset_padding=False)[0: data.shape[0]].flatten()
    return reconstructed
