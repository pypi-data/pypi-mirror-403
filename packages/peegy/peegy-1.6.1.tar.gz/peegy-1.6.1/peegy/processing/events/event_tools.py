import numpy as np
from peegy.definitions.events import SingleEvent, Events
import astropy.units as u


def detect_events(event_channel: type(np.array) | None = None, fs: float | None = None):
    start_points = np.hstack((0, np.where(np.diff(event_channel, axis=0) != 0)[0] + 1))
    stop_points = np.hstack(
        (np.where(np.diff(event_channel, axis=0) != 0)[0] + 1, len(event_channel) - 1))
    trigger_duration = (stop_points - start_points) / fs
    events = np.array([])
    for _s, _d in zip(start_points, trigger_duration):
        events = np.append(events, SingleEvent(code=float(event_channel[round(_s)]),
                                               time_pos=_s / fs,
                                               dur=_d))
    return events


def join_trigger_events(all_events=np.array([])):
    code = np.array([])
    idx = np.array([])
    dur = np.array([])
    dur_samples = np.array([])
    event_table = {}
    for events in all_events:
        for _code, _idx, _dur, _dur_samples in zip(events['code'], events['idx'], events['dur'], events['dur_samples']):
            code = np.append(code, _code)
            idx = np.append(idx, _idx)
            dur = np.append(dur, _dur)
            dur_samples = np.append(dur_samples, _dur_samples)
        event_table = {'code': code,
                       'idx': idx,
                       'dur': dur,
                       'dur_samples': dur_samples}
    return event_table


def join_triggers(all_triggers=np.array([])):
    """
    this function join two or more sets of triggers passed in a numpy array
    :param all_triggers: all_triggers: array of triggers
    :return: a new trigger with joined elements
    """
    code = np.array([], dtype=int)
    idx = np.array([], dtype=int)
    dur = np.array([])
    dur_samples = np.array([], dtype=int)
    min_distance = np.array([], dtype=int)
    max_distance = np.array([], dtype=int)
    position = np.array([], dtype=int)

    for events in all_triggers:
        code = np.append(events['code'], code)
        idx = np.append(events['idx'], idx)
        dur = np.append(events['dur'], dur)
        dur_samples = np.append(events['dur_samples'], dur_samples)
        min_distance = np.append(events['min_distance'], min_distance)
        max_distance = np.append(events['max_distance'], max_distance)
        position = np.append(events['position'], position)

    s_idx = np.argsort(idx)
    triggers = {'code': code[s_idx],
                'idx': idx[s_idx],
                'dur': dur[s_idx],
                'dur_samples': dur_samples[s_idx],
                'min_distance': min_distance[s_idx],
                'max_distance': max_distance[s_idx],
                'position': position[s_idx],
                'triggers': []
                }
    return triggers


def get_events(event_channel: type(np.array) | None = None, fs: type(u.Quantity) | None = None):
    _events = detect_events(event_channel=event_channel, fs=fs)
    _new_events = Events(events=np.array(_events))
    print(_new_events.summary().to_string(index=False))
    return _new_events


def events_to_samples_array(events: Events | None = None,
                            fs: type(u.Quantity) | None = None,
                            n_samples: int | None = None,
                            event_code: float | None = None,
                            min_samples_width: int = 1,
                            include_bad_events: bool = True,
                            resolve_overlap: bool = True):
    out = np.zeros((n_samples, 1))
    samples = events.get_events_index(fs=fs,
                                      include_bad_events=include_bad_events,
                                      code=event_code)
    if resolve_overlap:
        _indexes = find_repeated_values(samples=samples)
        while _indexes.size:
            _to_shift = _indexes[1::2]
            samples[_to_shift] = samples[_to_shift] + min_samples_width
            _indexes = find_repeated_values(samples=samples)

    codes = events.get_events_code(include_bad_events=include_bad_events,
                                   code=event_code)
    durations = events.get_events_duration(include_bad_events=include_bad_events)
    for _sample, _dur, _code in zip(samples, durations, codes):
        if _sample >= n_samples:
            break
        _ini = _sample
        _end = _sample + np.maximum(min_samples_width, np.floor(_dur * fs)).astype(int)
        out[_ini: _end, :] = _code
    return out


def find_repeated_values(samples: type(np.array) | None = None):
    vals, inverse, count = np.unique(samples,
                                     return_inverse=True,
                                     return_counts=True,
                                     axis=0)
    _indexes = np.where(count[inverse] > 1)[0]
    return _indexes
