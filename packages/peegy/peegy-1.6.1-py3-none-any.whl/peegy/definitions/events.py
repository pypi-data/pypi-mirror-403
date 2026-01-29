import copy
import numpy as np
import astropy.units as u
import pandas as pd
from typing import List


class SingleEvent(object):
    def __init__(self,
                 code: float | None = None,
                 time_pos: u.quantity.Quantity | None = None,
                 dur: u.quantity.Quantity | None = None,
                 bad_event: bool = False):
        """
        Class for a single (trigger) event, which is characterized by having a numerical identifier (code), an
        associated time point [s], and a duration [s].
        Parameters
        ----------
        code: Trigger event code (usually some number)
        time_pos: Time in seconds of trigger event
        dur: Duration of trigger event in seconds
        bad_event: indicate if this event is considered bad
        """
        self.code = code
        self.time_pos = time_pos
        self.dur = dur
        self.bad_event = bad_event

    def __repr__(self):
        return (f'{self.__class__.__name__}('f'{self.code!r}, {self.time_pos!r}, {self.dur!r}')

    def __str__(self):
        return 'Single event at time {} s with code {} and duration {} s'.format(self.time_pos, self.code, self.dur)


class Events(object):
    def __init__(self, events: np.array([SingleEvent]) = None):
        """
        Defines event class
        :param events: raw events array
        """
        self._events = events
        self._mask = None

    @property
    def mask(self):
        return self._mask

    @mask.setter
    def mask(self, value: float | None = None):
        self._mask = value
        print('Event mask {:} set'.format(self.mask))
        print(self.summary().to_string(index=False))

    def __repr__(self):
        return (f'{self.__class__.__name__}('
                f'{self.events().shape!r}')

    def __str__(self):
        return 'Event array of size {}'.format(self.events().shape)

    def events(self, include_bad_events: bool = False):
        out = []
        if self.mask is not None:
            for _ev in self._events:
                new_event = copy.copy(_ev)
                new_event.code = float(int(new_event.code) & int(self.mask))
                out.append(new_event)
            out = np.array(out)
        else:
            if include_bad_events:
                out = self._events
            else:
                out = np.array([_ev for _ev in self._events if not _ev.bad_event])
        return out

    def get_events(self,  code: List[float] | None = None, include_bad_events: bool = False):
        if code is None:
            return np.array([_ev for _ev in self.events(include_bad_events=include_bad_events)])
        else:
            if not (isinstance(code, list) | isinstance(code, np.ndarray)):
                code = [code]
            return np.array([_ev for _ev in self.events(include_bad_events=include_bad_events) if _ev.code in code])

    def recode_events(self,
                      every: int = 1,
                      start_at: int = 0,
                      code: List[float] | None = None,
                      new_code: float | None = None,
                      include_bad_events: bool = False):
        all_events = np.array([_ev for _ev in self.events(include_bad_events=True)])
        if code is not None:
            if not (isinstance(code, list) | isinstance(code, np.ndarray)):
                code = [code]
            _events = np.array([_ev for _ev in self.events(include_bad_events=include_bad_events) if _ev.code in code])
        else:
            _events = np.array([_ev for _ev in self.events(include_bad_events=include_bad_events)])
        _idx = []
        if every < 0:
            _target_events = np.flip(_events)[start_at::-every]
        else:
            _target_events = _events[start_at::every]
        for _ev in _target_events:
            _idx.append(int(np.where(all_events == _ev)[0]))
            _ev.code = new_code
        all_events[_idx] = _target_events
        self._events = all_events

    def get_events_index(self,  code: List[float] | None = None, fs=None, include_bad_events: bool = False):
        if code is None:
            return np.array([int(np.round(_ev.time_pos * fs)) for
                             _ev in self.events(include_bad_events=include_bad_events)])
        else:
            if not (isinstance(code, list) | isinstance(code, np.ndarray)):
                code = [code]
            return np.array([int(np.round(_ev.time_pos * fs)) for
                             _ev in self.events(include_bad_events=include_bad_events)
                             if _ev.code in code])

    def get_events_time(self, code: List[float] | None = None, include_bad_events: bool = False):
        if code is None:
            return np.array([_ev.time_pos.to(u.s).value for
                             _ev in self.events(include_bad_events=include_bad_events)]) * u.s
        else:
            if not (isinstance(code, list) | isinstance(code, np.ndarray)):
                code = [code]
            return np.array([_ev.time_pos.to(u.s).value for _ev in self.events(include_bad_events=include_bad_events)
                             if _ev.code in code]) * u.s

    def get_events_duration(self, code: List[float] | None = None, include_bad_events: bool = False):
        if code is None:
            return np.array([_ev.dur.to(u.s).value for _ev in self.events(include_bad_events=include_bad_events)]) * u.s
        else:
            if not (isinstance(code, list) | isinstance(code, np.ndarray)):
                code = [code]
            return np.array([_ev.dur.to(u.s).value for _ev in self.events(include_bad_events=include_bad_events)
                             if _ev.code in code]) * u.s

    def get_events_code(self, code: List[float] | None = None, include_bad_events: bool = False):
        if code is None:
            return np.array([_ev.code for _ev in self.events(include_bad_events=include_bad_events)])
        else:
            if not (isinstance(code, list) | isinstance(code, np.ndarray)):
                code = [code]
            return np.array([_ev.code for _ev in self.events(include_bad_events=include_bad_events)
                             if _ev.code in code])

    def set_events_status(self,
                          event_idx: np.array,
                          bad_event: bool = False):
        for _ev in self._events[event_idx]:
            _ev.bad_event = bad_event

    def get_events_object(self,  code: List[float] | None = None, include_bad_events: bool = False):
        return Events(self.get_events(code=code, include_bad_events=include_bad_events))

    def interpolate_events_between_events(self, scaling_factor=1.0, code: List[float] | None = None, events_mask=None):
        """
        This function interpolates time events between consecutive event. The time position of new events is defined
        by the scaling factor. For example, an scaling_factor of 2.0 will add a new trigger event exactly in the middle
        time between two events
        :param scaling_factor: a float that determine the number of new events that will be generated
        :param code: list of event codes to be interpolated
        :param events_mask: integer value used to masker triggers codes. This is useful to ignore triggers inputs above
        a particular value. For example, if only the first 8 trigger inputs were used (max decimal value is 255), in a
        system with 16 trigger inputs, then the masker could be set to 255 to ignore any trigger from trigger inputs 9
        to 16.
        :return: new an Events class containing the new interpolated events
        """
        self.mask = events_mask
        _times = self.get_events_time(code=code)
        _durations = self.get_events_duration(code=code)
        _codes = self.get_events_code(code=code)
        _times_intervals = np.diff(_times)
        _times_intervals = np.append(_times_intervals, np.mean(_times_intervals))
        _new_events = []
        for _ini_time, _length, _dur, _code in zip(_times, _times_intervals, _durations, _codes):
            _new_times = np.arange(_ini_time.to(u.s).value,
                                   (_ini_time + _length).to(u.s).value,
                                   (_length / scaling_factor).to(u.s).value) * u.s
            [_new_events.append(SingleEvent(time_pos=_t, dur=_dur, code=_code)) for _t in _new_times]
        return Events(events=np.array(_new_events))

    def interpolate_events_constant_rate(self,
                                         interpolation_rate: type(u.Quantity) | None = None,
                                         code: List[float] | None = None,
                                         events_mask: int | None = None):
        """
        This function interpolates time events between consecutive events at a constant rate defined
        by the interpolation_rate. For example, an interpolation_rate of 10 * u.Hz will add a new trigger every 1 / 10
        seconds.
        :param interpolation_rate: Frequency at which events should be interpolated
        :param code: list of event codes to be interpolated
        :param events_mask: integer value used to masker triggers codes. This is useful to ignore triggers inputs above
        a particular value. For example, if only the first 8 trigger inputs were used (max decimal value is 255), in a
        system with 16 trigger inputs, then the masker could be set to 255 to ignore any trigger from trigger inputs 9
        to 16.
        :return: new an Events class containing the new interpolated events
        """
        self.mask = events_mask
        _times = self.get_events_time(code=code)
        _durations = self.get_events_duration(code=code)
        _codes = self.get_events_code(code=code)
        _times_intervals = np.diff(_times)
        _times_intervals = np.append(_times_intervals, np.mean(_times_intervals))
        _new_events = []
        for _ini_time, _length, _dur, _code in zip(_times, _times_intervals, _durations, _codes):
            _new_times = np.arange(_ini_time.to(u.s).value,
                                   (_ini_time + _length).to(u.s).value,
                                   (1 / interpolation_rate).to(u.s).value) * u.s
            [_new_events.append(SingleEvent(time_pos=_t, dur=_dur, code=_code)) for _t in _new_times]
        return Events(events=np.array(_new_events))

    def summary(self):
        out = pd.DataFrame()
        for i, _code in enumerate(np.unique(self.get_events_code())):
            out = pd.concat([out,
                             pd.DataFrame.from_dict(
                                 {'event_code': [_code],
                                  'n_events': [self.get_events_code(code=_code).size]})],
                            ignore_index=True)
        return out

    def clip(self, ini_time: u.Quantity = 0 * u.s, end_time: u.Quantity = 0 * u.s):
        self._events = np.array([_ev for _ev in self._events if _ev.time_pos >= ini_time])
        self._events = np.array([_ev for _ev in self._events if _ev.time_pos <= end_time])

    def set_offset(self, time_offset: u.Quantity = 0 * u.s):
        self._events = np.array([
            SingleEvent(time_pos=_ev.time_pos - time_offset,
                        dur=_ev.dur,
                        code=_ev.code) for _ev in self._events])

    def events_to_pandas(self, code: List[float] | None = None, exclude_code: List[float] | None = None):
        _events = self.get_events(code=code)
        if exclude_code is None:
            out = pd.DataFrame([
                {'time_pos': _event.time_pos.to(u.s).value,
                 'code': _event.code,
                 'dur': _event.dur.to(u.s).value,
                 'bad_event': _event.bad_event
                 } for _event in _events if _event.code])
        else:
            if not isinstance(exclude_code, list):
                exclude_code = [exclude_code]
            out = pd.DataFrame([
                {'time_pos': _event.time_pos.to(u.s).value,
                 'code': _event.code,
                 'dur': _event.dur.to(u.s).value,
                 'bad_event': _event.bad_event
                 } for _event in _events if _event.code not in exclude_code])
        return out

    def unique_event_codes_to_pandas(self, code: List[float] | None = None, exclude_code: List[float] | None = None):
        events_df = self.events_to_pandas(code=code,
                                          exclude_code=exclude_code)
        if events_df.shape[0]:
            events_df = events_df.drop(columns=['time_pos', 'dur', 'bad_event'])
            unique_event_codes = events_df.drop_duplicates()
        else:
            unique_event_codes = events_df
        return unique_event_codes
