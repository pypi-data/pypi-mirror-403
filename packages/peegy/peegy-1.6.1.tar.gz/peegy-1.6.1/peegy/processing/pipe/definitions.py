import copy
from peegy.definitions.channel_definitions import Domain, ChannelItem, ChannelType
from peegy.processing.tools.epoch_tools.transform import de_epoch
from peegy.definitions import tables
from peegy.directories.tools import DirectoryPaths
from peegy.definitions.events import Events, SingleEvent
from peegy.tools.units.unit_tools import set_default_unit
from peegy.io.exporters import wav_writer
import inspect
import tempfile
import base64
from PIL import Image
import pandas as pd
import io
import gc
import astropy.units as u
import abc
import matplotlib.pyplot as plt
import numpy as np
from tqdm import tqdm
import pyqtgraph as pg
import pyqtgraph.exporters
import time
from typing import List
pg.setConfigOption('leftButtonPan', False)


class DataNode(object):
    """
    Core data object used to keep data. During the creation, it requires the sampling rate and the actual data.
    Data is passed in a numpy array of n * m or n * m * t, where n represent samples, m channels, and t trials.
    Units are passed via unit kargs (default units is microVolts)
    """
    def __init__(self,
                 fs=None,
                 data: np.array = np.array([]),
                 domain=Domain.time,
                 x_offset=0.0 * u.s,
                 n_fft=None,
                 layout: np.array([ChannelItem]) = None,
                 process_history: List = [],
                 events: Events | None = None,
                 events_annotations: () = None,
                 paths: DirectoryPaths = DirectoryPaths(),
                 rn: type(np.array) | None = None,
                 rn_df: type(np.array) | None = None,
                 cum_rn: type(np.array) | None = None,
                 snr: type(np.array) | None = None,  # it may content snr for different ROIs
                 cum_snr: type(np.array) | None = None,
                 s_var=None,
                 alpha=0.05,
                 n: int | None = None,
                 w: type(np.array) | None = None,
                 # statistical_tests: tables.Tables = tables.Tables(),
                 processing_tables_global: tables.Tables = tables.Tables(),
                 # processing_tables_local: tables.Tables = tables.Tables(),
                 peaks=None,
                 # peak_frequency=None,
                 # peak_to_peak_amplitudes=None,
                 peak_time_windows=None,
                 roi_windows=None,
                 markers=None,
                 frequency_resolution=None
                 ):
        # n * m * t data array
        # if data represent time or frequency
        # time offset from origin
        # layout
        # list used to store processing history that resulted in the current data

        self._data = set_default_unit(data, u.dimensionless_unscaled)
        self.fs = fs
        self.domain = domain
        self.x_offset = x_offset
        self.layout = layout
        self.events = events
        self.events_annotations = events_annotations
        self.process_history = process_history
        self.paths = paths
        # signal statistics
        self.rn = rn
        self.cum_rn = cum_rn
        self.snr = snr
        self.cum_snr = cum_snr
        self.s_var = s_var
        self.n = n
        self.rn_df = rn_df
        self.w = w
        self.alpha = alpha
        # statistical data
        self._statistical_tests = tables.Tables()
        # other processing tables
        self._processing_tables_global = processing_tables_global
        self._processing_tables_local = tables.Tables()
        # peak measures
        self.peaks = peaks
        self.peak_time_windows = peak_time_windows
        self.roi_windows = roi_windows
        self.markers = markers
        self.n_fft = n_fft
        self.frequency_resolution = frequency_resolution
        if self.layout is None and data.size:
            self.layout = np.array([ChannelItem() for _ in range(self.data.shape[1])])  # default channel information

        self._x = None
        self._y = None

    def get_x(self):
        if self.domain == Domain.time:
            out = np.arange(self.data.shape[0]) / self.fs - self.x_offset
            out = out.to(u.s)
        if self.domain == Domain.frequency:
            out = np.arange(self.data.shape[0]) * self.fs / self.n_fft
            out = out.to(u.Hz)
        if self.domain == Domain.time_frequency:
            out = self._x
        return out

    def set_x(self, value):
        self._x = value
    x = property(get_x, set_x)

    def get_y(self):
        return self._y

    def set_y(self, value):
        self._y = value

    y = property(get_y, set_y)

    def get_processing_tables_global(self):
        return self._processing_tables_global

    def set_processing_tables_global(self, value: tables.Tables() = None):
        self._processing_tables_global.append(value)

    processing_tables_global = property(get_processing_tables_global, set_processing_tables_global)

    def get_processing_tables_local(self):
        return self._processing_tables_local

    def set_processing_tables_local(self, value: tables.Tables() = None):
        self._processing_tables_local.append(value)

    processing_tables_local = property(get_processing_tables_local, set_processing_tables_local)

    def get_statistical_tests(self):
        return self._statistical_tests

    def set_get_statistical_tests(self, value: tables.Tables() = None):
        self._statistical_tests.append(value)

    statistical_tests = property(get_statistical_tests, set_get_statistical_tests)

    def apply_layout(self, layout=None):
        for _s_i in layout.layout:
            for _i, _l in enumerate(self.layout):
                if _l.idx == _s_i.idx:
                    self.layout[_i] = _s_i
                    break

    def delete_channel_by_idx(self, idx: np.array = np.array([])):
        labels = '/'.join([_ch.label for _ch in self.layout[idx]])
        self.data = np.delete(self.data, idx, 1)
        self.layout = np.delete(self.layout, idx)
        print('removed channels: ' + ''.join(labels))

    def delete_channel_by_label(self, label=''):
        _idx = np.array([_i for _i, _lay in enumerate(self.layout) if _lay.label == label])
        if _idx.size:
            self.delete_channel_by_idx(idx=_idx)

    def get_channel_idx_by_label(self, labels: np.array([str]) = None):
        if labels is None:
            labels = np.array([_channel.label for _channel in self.layout])
        if isinstance(labels, list):
            labels = np.array(labels)
        # ensure unique labels and remove repeated in same order
        _, idx_labels = np.unique(labels, return_index=True)
        labels = labels[np.sort(idx_labels)]
        all_labels = np.array([_channel.label for _idx, _channel in enumerate(self.layout)])
        idx = []
        for _label in labels:
            _idx = np.argwhere(_label == all_labels)
            if _idx.size:
                idx.append(_idx.squeeze())
        idx = np.array(idx)
        return idx

    def get_channel_idx_by_type(self, channel_type=ChannelType.Event):
        all_idx = np.array([_idx for _idx, _channel in enumerate(self.layout) if _channel.type == channel_type])
        idx = np.unique(all_idx)
        return idx

    def get_channel_label_by_idx(self, idx: np.array = np.array([])) -> [str]:
        if idx.size == 0:
            idx = np.arange(self.layout.size)
        labels = [_ch.label for _ch in self.layout[idx]]
        return labels

    def set_data(self, value=np.array):
        self._data = value

    def get_data(self):
        return self._data
    data = property(get_data, set_data)

    def data_slice(self, ini_sample: int = 0, end_sample: int = np.inf, axis: int = 0):
        # obtain data from ini_sample until but not including the end_sample
        ini_sample = np.maximum(ini_sample, 0)
        end_sample = np.minimum(self._data.shape[axis], end_sample)
        indices = np.arange(ini_sample, end_sample).astype(int)
        out = np.take(self._data, indices=indices, axis=axis)
        return out

    def get_max_snr_per_channel(self):
        if self.snr is not None:
            max_snr = np.nanmax(np.atleast_2d(self.snr), axis=0)
        else:
            max_snr = np.array([None] * self._data.shape[1])
        return np.atleast_1d(np.squeeze(max_snr))

    def get_max_s_var_per_channel(self):
        max_var = np.nanmax(self.s_var, axis=0)
        return np.atleast_1d(np.squeeze(max_var))

    def x_to_samples(self,
                     value: type(np.array) | None = None,
                     ) -> np.array:
        out = np.array([], dtype=int)
        if self.domain == Domain.time:
            _offset = self.x_offset
            _scaling = self.fs
        if self.domain == Domain.frequency:
            _offset = 0 * u.Hz
            _scaling = 1 / self.frequency_resolution
        for _v in value:
            if np.isinf(_v):
                out = np.append(out, self.data.shape[0] - 1)
            else:
                # out = np.append(out, np.argmin(np.abs(self.x.value - np.array(_value)))).astype(int)
                sample = np.round(((_v + _offset) * _scaling).to(u.dimensionless_unscaled))
                sample = np.minimum(sample, self.data.shape[0] - 1)
                sample = np.maximum(sample, 0)
                out = np.append(out, int(sample.value))
        return out

    def x_range_to_samples(self,
                           ini_time: type(u.Quantity) | None = None,
                           end_time: type(u.Quantity) | None = None,
                           ) -> np.array:
        if ini_time is None:
            ini_time = self.x[0]
        if end_time is None:
            end_time = self.x[-1]
        ini_sample = self.x_to_samples([ini_time])
        end_sample = self.x_to_samples([end_time])
        out = np.arange(ini_sample, end_sample + 1).astype(int)
        return out

    def samples_to_x(self, value: np.array(int)) -> np.array(u.Quantity):
        out = np.array([]) * 1 / self.fs.unit
        for _v in value:
            out = np.append(out, _v / self.fs - self.x_offset)
        return out

    def data_to_pandas(self):
        _row_test = []
        if self._data is not None and self._data.size:
            for i in range(self._data.shape[1]):
                data_binary_x = io.BytesIO()
                np.save(data_binary_x, self.x.value)
                data_binary_y = io.BytesIO()
                np.save(data_binary_y, self.data[:, i].value)
                data_binary_x.seek(0)
                data_binary_y.seek(0)
                _row_time_data = {'domain': self.domain,
                                  'channel': self.layout[i].label,
                                  'fs': self.fs,
                                  'x': data_binary_x.read(),
                                  'y': data_binary_y.read(),
                                  'x_unit': self.x.unit.to_string(),
                                  'y_unit': self.data[:, i].unit.to_string(),
                                  'snr': self.get_max_snr_per_channel()[i]}
                _row_test.append(_row_time_data)
        _data_pd = pd.DataFrame(_row_test)
        return _data_pd

    def append_new_channel(self, new_data: type(np.array) | None = None, layout_label: str = ''):
        new_channel = ChannelItem(label=layout_label)
        self.layout = np.append(self.layout, new_channel)
        self.data = np.append(self.data.value, new_data.to_value(self.data.unit), axis=1) * self.data.unit
        self.rn = np.append(self.rn, np.nan)
        if self.snr is not None:
            self.snr = np.append(self.snr, np.nan)
        if self.s_var is not None:
            self.s_var = np.append(self.s_var, np.nan)

    def clip(self, ini_time: u.Quantity = 0 * u.s, end_time: u.Quantity = np.inf * u.s):
        ini_time = set_default_unit(ini_time, u.s)
        end_time = set_default_unit(end_time, u.s)
        if np.isinf(end_time):
            end_time = self.x[-1]
        samples = self.x_to_samples(np.array([ini_time.to(u.s).value,
                                              end_time.to(u.s).value]) * u.s)
        _extact_time_offset = self.x[samples[0]]
        self._data = self._data[samples[0]: samples[-1], ::]
        self.events.clip(ini_time=ini_time, end_time=end_time)
        # apply offset
        self.events.set_offset(time_offset=_extact_time_offset)

    def randomize_events(self, epoch_length: type(u.Quantity) | None = None,
                         n_events: int | None = None,
                         event_code: float = 1,
                         dur: u.Quantity = 100 * u.us,
                         min_time: type(u.Quantity) | None = None,
                         max_time: type(u.Quantity) | None = None):
        """
        Generate random time events.
        :param epoch_length: Time of epoch length. This value will only affect the maximum timing of the random events
        so that when the data is epoched with the desired epoch length the last event position will not be beyond the
        total timing of the data minus the epoch length. In this way ensuring that all random event will be used when
        epoching the data.
        :param n_events: Number of random events to be generated. If empty the original event number is used
        :param event_code: float with the event code that will be used to generate/assign new random events
        :param dur: time duration that will be assigned to the new random events
        :param min_time: minimum time of new events
        :param max_time: maximum time of new events
        :return: None
        """
        # generate random events based on original number of events or given number of events
        _n_events = None
        _min_time, _max_time = None, None
        if self.events.get_events_code(code=event_code).size:
            _n_events = self.events.get_events_code(code=event_code).size
            _min_time = self.events.get_events_time(code=event_code).min()
            _max_time = self.events.get_events_time(code=event_code).max()
        if n_events is None:
            n_events = _n_events
        if min_time is not None:
            _min_time = min_time

        if max_time is not None:
            _max_time = max_time

        if _min_time is None:
            _min_time = 0 * u.s
        if _max_time is None:
            _max_time = self._data.shape[0] / self.fs

        if n_events:
            if epoch_length is None:
                epoch_length = ((_max_time - _min_time) / n_events)
            new_event_times = np.sort(
                _min_time + np.random.rand(n_events) * (_max_time - _min_time - epoch_length), kind='quicksort')
            events = np.empty(new_event_times.size, dtype=SingleEvent)
            for i, _s, in enumerate(new_event_times):
                events[i] = SingleEvent(code=event_code,
                                        time_pos=_s,
                                        dur=dur)
            self.events = Events(events=np.array(events))


class InputOutputQtFigure(object):
    """
    This class is a wrapper to allow sphinx showing qt figures
    """
    def __init__(self, figure: pg.GraphicsView | None = None):
        self.figure = figure

    def _repr_html_(self):
        # self.figure.scene().setSceneRect(0, 0, 600, 300)
        # ex = pg.exporters.SVGExporter(self.figure.scene())
        _file = tempfile.NamedTemporaryFile(delete=False,
                                            suffix='.png')
        ex = pg.exporters.ImageExporter(self.figure.scene())
        target_width_inches = 6
        target_dpi = 300
        ex.parameters()['width'] = target_width_inches * target_dpi
        # ex.parameters()['height'] = 300
        ex.export(_file.name)
        # html__figure_exporter = out.decode("utf-8")
        img = Image.open(_file.name)
        byte_arr = io.BytesIO()
        img.save(byte_arr, format='PNG')  # Save image to the buffer
        png_data = base64.b64encode(byte_arr.getvalue()).decode('utf-8')
        out = f'<img src="data:image/png;base64, {png_data}"/>'
        return out


class InputOutputProcess(metaclass=abc.ABCMeta):
    """
    Core abstract input-output function. Each inherit class must provide an input data, a process function and and
    output data set
    """
    def __init__(self, input_process: object | None = None,
                 keep_input_node=True,
                 **kwargs):
        self.input_process: InputOutputProcess = input_process if input_process is not None else self  # Input data
        # must be InputOutputProcess class
        self.function_args: dict = kwargs
        self.input_node: DataNode | None = None
        self.output_node: DataNode | None = None
        self._process_parameters: dict = kwargs  # dict with all the parameters used in process function
        self._keep_input_node: bool = keep_input_node
        self._figures: List[plt.Figure] | None = None
        self._name: str | None = None
        self._ready = False
        if self._name is None:
            self._name = self.__class__.__name__
        self._calling_parameters = None
        self._figures_path = None
        if 'calling_parameters' in kwargs.keys():
            self._calling_parameters = kwargs['calling_parameters']

    def get_process_parameters(self):
        return self._process_parameters

    def set_process_parameters(self, value):
        self._process_parameters = value
    process_parameters = property(get_process_parameters, set_process_parameters)

    def get_keep_input_node(self):
        return self._keep_input_node

    def set_keep_input_node(self, value):
        self._keep_input_node = value
    keep_input_node = property(get_keep_input_node, set_keep_input_node)

    def get_figures(self):
        return self._figures

    def set_figures(self, value):
        self._figures = value
    figures = property(get_figures, set_figures)

    def get_figures_path(self):
        return self._figures_path

    def set_figures_path(self, value):
        self._figures_path = value
    figures_path = property(get_figures_path, set_figures_path)

    def get_name(self):
        return self._name

    def set_name(self, value):
        self._name = value
    name = property(get_name, set_name)

    def get_ready(self):
        return self._ready

    def set_ready(self, value):
        self._ready = value
    ready = property(get_ready, set_ready)

    def transform_data(self):
        return 'core method to generate output data'

    def run(self):
        if (isinstance(self.input_process, InputOutputProcess) and self != self.input_process and
                not self.input_process.ready):
            self.input_process.run()
        self.input_node = self.input_process.output_node
        callable_list = [_i for _i in dir(DataNode) if callable(getattr(DataNode, _i))]
        properties_list = [_i[0] for _i in inspect.getmembers(DataNode, lambda o: isinstance(o, property))]
        attributes = [a for a in dir(self.input_node) if not (a.startswith('__') or a.startswith('_')) and
                      a not in callable_list and a not in properties_list]
        pars = {_a: getattr(self.input_node, _a) for _a in attributes}
        self.output_node = DataNode(data=np.array([]),
                                    **pars
                                    )  # Output data must be DataNode class
        start = time.time()
        self.transform_data(**self.function_args)
        end = time.time()
        print('Elapsed time - {:}: {:.3f}s'.format(self.name, end - start))
        self.ready = True

        if not self.keep_input_node:
            if isinstance(self.input_node, DataNode):
                self.input_node.data = None
            self.input_node = None
            gc.collect()
        return

    def plot(self,
             plot_input: bool = False,
             plot_output: bool = True,
             ch_to_plot: List[str] | None = None,
             interactive: bool = True,
             show_events: bool = True,
             channels_offset: type(u.Quantity) | None = None):
        """
        This method will plot data in the input and/or the output node.
        :param plot_input: bool indicating if input_node data should be plotted
        :param plot_output: bool indicating if output_node data should be plotted
        :param ch_to_plot: list of strings indicating the labels of the channels to be shown. If empty, all channels
        will be shown.
        :param interactive: boolean indicating if plot should be interactive or not
        :param show_events: if True, events will be shown
        :param channels_offset: offset in vertical units to separate channels in figure
        """
        win = plot_input_output_process(input_output_process=self,
                                        plot_input=plot_input,
                                        plot_output=plot_output,
                                        ch_to_plot=ch_to_plot,
                                        channels_offset=channels_offset,
                                        show_events=show_events
                                        )
        out = InputOutputQtFigure(figure=win)
        if interactive:
            win.show()
            pg.QtGui.QGuiApplication.instance().exec_()
        return out

    def get_input_parameters(self):
        all_input_variables = list(inspect.signature(self.__init__).parameters.keys())
        # all_locals = self.__init__.__code__.co_varnames
        # attributes = [a for a in dir(self.input_node) if not (a.startswith('__') or a.startswith('_')) and
        #               a not in callable_list and a not in properties_list]
        parameters = {key: self.__dict__[key] for key in all_input_variables if key in self.__dict__.keys()}

        return parameters

    def to_wav(self,
               file_name: str | None = None,
               channel_labels: List[str] | None = None,
               fs: u.Quantity = 48000 * u.Hz,
               event_code: float | None = None,
               event_duration: type(u.Quantity) | None = None,
               normalize: bool = False,
               demean_edges=True,
               edge_duration: type(u.Quantity) | None = None,
               gain: float = 0.99,
               ):
        _idx_ch = self.output_node.get_channel_idx_by_label(labels=channel_labels)
        if _idx_ch.size:
            selected_data = self.output_node.data[:, _idx_ch, ...]
            if np.ndim(selected_data) == 2:
                _events = Events(events=self.output_node.events.get_events(code=event_code))
                _data = selected_data
            if np.ndim(selected_data) == 3:
                _data, _events = de_epoch(data=selected_data,
                                          demean_edges=demean_edges,
                                          edge_duration=edge_duration,
                                          event_code=event_code,
                                          event_duration=event_duration,
                                          fs=self.input_node.fs)
            wav_writer.data_to_wav(data=_data,
                                   fs=self.output_node.fs,
                                   fs_wav=fs,
                                   events=_events,
                                   output_file_name=file_name,
                                   normalize=normalize,
                                   gain=gain)


def plot_input_output_process(input_output_process: InputOutputProcess | None = None,
                              plot_input: bool = False,
                              plot_output: bool = True,
                              ch_to_plot: List[str] | None = None,
                              de_mean: bool = False,
                              show_events: bool = True,
                              channels_offset: type(u.Quantity) | None = None):
    """
    This method will plot data in the input and/or the output node.
    :param input_output_process: InputOutputProcess for which plot will be generated.
    :param plot_input: bool indicating if input_node data should be plotted
    :param plot_output: bool indicating if output_node data should be plotted
    :param ch_to_plot: list of strings indicating the labels of the channels to be shown. If empty, all channels
    will be shown.
    :param de_mean: if True, lines will be centred around the mean and then offset
    :param show_events: if True, events will be shown
    :param channels_offset: offset in vertical units to separate channels in figure
    """
    if not plot_input and not plot_output:
        return
    data_in = None
    if input_output_process.input_node is not None:
        data_in = copy.copy(input_output_process.input_node.data)
        name_in = input_output_process.input_process.name
        if input_output_process.input_node.domain == Domain.frequency:
            data_in = np.abs(data_in)
    data_out = None
    if input_output_process.output_node is not None:
        name_out = input_output_process.name
        data_out = copy.copy(input_output_process.output_node.data)
        if input_output_process.output_node.domain == Domain.frequency:
            data_out = np.abs(data_out)

    if data_in is not None or data_out is not None:
        win = pg.GraphicsLayoutWidget()
        win.setWindowTitle(input_output_process.name + '/' + input_output_process.name)
        ax = win.addPlot(row=1, col=1)
        ax.addLegend()
    else:
        return

    offset_in, offset_out = 0, 0
    channels_in, channels_out = [], []
    if data_in is not None and plot_input:
        offset_in = (np.max(np.abs(data_in.flatten() - np.mean(data_in.flatten()))) +
                     np.min(np.abs(data_in.flatten() - np.mean(data_in.flatten())))) / 2
        channels_in = [_l.label for _l in input_output_process.input_node.layout]
    if data_out is not None and plot_output:
        offset_out = (np.max(np.abs(data_out.flatten() - np.mean(data_out.flatten()))) +
                      np.min(np.abs(data_out.flatten() - np.mean(data_out.flatten())))) / 2
        channels_out = [_l.label for _l in input_output_process.output_node.layout]

    if ch_to_plot is not None:
        channels_in = list(set(ch_to_plot) & set(channels_in))
        channels_out = list(set(ch_to_plot) & set(channels_out))

    channels = np.unique(channels_in + channels_out)
    if channels_offset is None:
        offset = np.maximum(offset_in, offset_out)
    else:
        offset = channels_offset
    if plot_input and data_in is not None:
        x_in = input_output_process.input_node.x
        ax.setDownsampling(auto=True, mode='peak')
        ax.showGrid(True, True)
        if de_mean:
            data_in = data_in - np.mean(data_in, axis=0)
        _color = (255, 0, 0)
        for _i, _label in enumerate(tqdm(channels_in, desc='Generating input plot')):
            _name = name_in if _i == 0 else None
            _pos = np.argwhere(channels == _label).squeeze()
            if not _pos.size:
                continue
            text_item = pg.TextItem(_label, anchor=(0.0, 0.0))
            text_item.setPos(0, offset.value * _pos)
            if data_in.ndim == 2:
                ax.plot(x_in, data_in[:, _i] +
                        offset * _pos, pen=_color, name=_name)

            if data_in.ndim == 3:
                data_in[:, _i, :] = data_in[:, _i, :] + offset * _pos
                for _t in tqdm(range(data_in.shape[2]),
                               desc='Generating input plot per epochs for channel {:}'.format(_label)):
                    ax.plot(x_in, data_in[:, _i, _t], pen=_color, name=_name if _t == 0 else None)
                    pg.QtCore.QCoreApplication.processEvents()
            ax.addItem(text_item)

            if show_events and input_output_process.input_node.events is not None:
                _codes = np.unique(input_output_process.input_node.events.get_events_code(include_bad_events=True))
                for _code in _codes:
                    _events = input_output_process.input_node.events.get_events(code=_code, include_bad_events=True)
                    _good_events = np.array([])
                    _bad_events = np.array([])
                    for _ev in _events:
                        if _ev.bad_event:
                            _bad_events = np.append(_bad_events, _ev.time_pos.value)
                        else:
                            _good_events = np.append(_good_events, _ev.time_pos.value)
                    if _good_events.size:
                        _pvl = plotVerticalLines()
                        ax.addItem(_pvl)
                        _pvl.setVerticalLines(_good_events, pen=_color)
                    if _bad_events.size:
                        _pvl = plotVerticalLines()
                        ax.addItem(_pvl)
                        _pvl.setVerticalLines(_bad_events, pen='r')

        if input_output_process.input_node.domain == Domain.time:
            ax.setLabel('bottom', "Time [{:}]".format(input_output_process.input_node.x.unit))
            ax.setLabel('left', "Amplitude [{:}]".format(input_output_process.input_node.data.unit))
        if input_output_process.input_node.domain == Domain.frequency:
            ax.setLabel('bottom', "Frequency [{:}]".format(input_output_process.input_node.x.unit))
            ax.setLabel('left', "Amplitude [{:}]".format(input_output_process.input_node.data.unit))

    if plot_output and data_out is not None:
        _color = (0, 0, 255)
        x_out = input_output_process.output_node.x
        ax.setDownsampling(ds=100, mode='peak')
        ax.showGrid(True, True)
        if de_mean:
            data_out = data_out - np.mean(data_out, axis=0)
        for _i, _label in enumerate(tqdm(channels_out, desc='Generating output plot')):
            _name = name_out if _i == 0 else None
            _pos = np.argwhere(channels == _label).squeeze()
            if not _pos.size:
                continue
            text_item = pg.TextItem(_label, anchor=(0.0, 0.0))
            text_item.setPos(0, offset.value * _pos)
            if data_out.ndim == 2:
                ax.plot(x_out, data_out[:, _i] + offset * _pos, pen=_color, name=_name)
            if data_out.ndim == 3:
                data_out[:, _i, :] = data_out[:, _i, :] + offset * _pos
                for _t in tqdm(range(data_out.shape[2]),
                               desc='Generating output plot per epochs for channel {:}'.format(_label)):
                    ax.plot(x_out, data_out[:, _i, _t], pen=_color, name=_name if _t == 0 else None)
                    pg.QtCore.QCoreApplication.processEvents()

            ax.addItem(text_item)
            if show_events and input_output_process.output_node.events is not None:
                _codes = np.unique(input_output_process.output_node.events.get_events_code())
                for _code in _codes:
                    _events = input_output_process.output_node.events.get_events(code=_code, include_bad_events=True)
                    _good_events = np.array([])
                    _bad_events = np.array([])
                    for _ev in _events:
                        if _ev.bad_event:
                            _bad_events = np.append(_bad_events, _ev.time_pos.value)
                        else:
                            _good_events = np.append(_good_events, _ev.time_pos.value)
                    if _good_events.size:
                        _pvl = plotVerticalLines()
                        ax.addItem(_pvl)
                        _pvl.setVerticalLines(_good_events, pen=_color)

                    if _bad_events.size:
                        _pvl = plotVerticalLines()
                        ax.addItem(_pvl)
                        _pvl.setVerticalLines(_bad_events, pen='r')

        if input_output_process.output_node.domain == Domain.time:
            ax.setLabel('bottom', "Time [{:}]".format(input_output_process.output_node.x.unit))
            ax.setLabel('left', "Amplitude [{:}]".format(input_output_process.output_node.data.unit))
        if input_output_process.output_node.domain == Domain.frequency:
            ax.setLabel('bottom', "Frequency [{:}]".format(input_output_process.output_node.x.unit))
            ax.setLabel('left', "Amplitude [{:}]".format(input_output_process.output_node.data.unit))
    pg.QtCore.QCoreApplication.processEvents()
    return win


class plotVerticalLines(pg.PlotDataItem):
    def __init__(self, container: pg.PlotItem | None = None):
        super(plotVerticalLines, self).__init__()
        self.pen = None

    def dataBounds(self, ax, frac=1.0, orthoRange=None):
        return [None, None]

    def setVerticalLines(self, x, pen=None):
        self.pen = pen
        x = np.vstack((x, x)).T.astype(float)
        y = np.zeros_like(x)
        vb = self.getViewBox()
        xr, yr = vb.viewRange()
        y[:, 0] = yr[0]
        y[:, 1] = yr[1]
        self.setData(x.ravel(), y.ravel(), connect='pairs', pen=self.pen)
        vb.sigYRangeChanged.connect(self._y_range_changed)

    def _y_range_changed(self, viewbox):
        xr, yr = viewbox.viewRange()
        # get the original not transformed clipped etc.
        x = self.xData
        y = self.yData
        y[0::2] = yr[0]
        y[1::2] = yr[1]
        self.setData(x, y, connect='pairs', pen=self.pen)
