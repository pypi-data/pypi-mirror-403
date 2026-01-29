from peegy.processing.events.event_tools import events_to_samples_array
from peegy.definitions.events import Events
from peegy.processing.tools.filters.resampling import eeg_resampling
import numpy as np
import logging
import astropy.units as u
import soundfile as sf
log = logging.getLogger()


def data_to_wav(data: np.array(u.Quantity) = None,
                events: Events | None = None,
                output_file_name: str | None = None,
                fs: type(u.Quantity) | None = None,
                fs_wav: type(u.Quantity) | None = None,
                normalize: bool = False,
                gain: float = 0.99):

    data_resampled, _factor = eeg_resampling(x=data,
                                             new_fs=fs_wav,
                                             fs=fs)

    events_samples = events_to_samples_array(events=events, fs=fs_wav, n_samples=data_resampled.shape[0])
    if normalize:
        _data = data_resampled / np.max(np.abs(data_resampled), axis=0)
    else:
        _data = data_resampled
    _data = gain * _data.value
    if np.max(np.abs(_data)) >= 1:
        print('your file is clipping')
    events_samples = events_samples / np.max(np.abs(events_samples))
    _data = np.hstack((_data, events_samples))
    sf.write(file=output_file_name,
             data=_data,
             samplerate=int(fs_wav.to('Hz').value))
    return _data, fs_wav
