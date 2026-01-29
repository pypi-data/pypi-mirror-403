import astropy.units as u
import numpy as np
from peegy.definitions.events import Events, SingleEvent


def de_epoch(data: np.array(u.Quantity) = None,
             demean_edges=True,
             edge_duration: type(u.Quantity) | None = None,
             event_code: int | None = None,
             event_duration: type(u.Quantity) | None = None,
             fs: type(u.Quantity) | None = None,
             ):
    if demean_edges:
        if edge_duration is None or edge_duration == 0 * u.s:
            _edge_samples = 1
        else:
            _edge_samples = int(edge_duration * fs)

        for _i in range(1, data.shape[2]):
            _previous_edge = np.mean(data[-_edge_samples::, :, _i - 1], axis=0, keepdims=True)
            _current_edge = np.mean(data[0:_edge_samples, :, _i], axis=0, keepdims=True)
            data[:, :, _i] = data[:, :, _i] - (_current_edge - _previous_edge)

    output_data = np.reshape(np.transpose(data, [0, 2, 1]), [-1, data.shape[1]], order='F')
    events = []
    if event_code is None:
        event_code = 1
    if event_duration is None:
        # ensure at least 3 samples
        event_duration = 3 / fs
    for _i in range(data.shape[2]):
        events.append(SingleEvent(code=event_code,
                                  time_pos=_i * data.shape[0] / fs,
                                  dur=event_duration))
    events = Events(events=np.array(events))
    return output_data, events
