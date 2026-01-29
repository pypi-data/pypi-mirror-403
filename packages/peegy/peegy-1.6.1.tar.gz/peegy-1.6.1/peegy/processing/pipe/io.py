import copy
import numpy as np
import datetime
from peegy.definitions.channel_definitions import Domain, ChannelItem
from peegy.io.eeg.reader import eeg_reader
from peegy.io.readers.eclipse_tools import parse_eclipse_data
from peegy.processing.pipe.definitions import InputOutputProcess, DataNode
from peegy.layouts import layouts
import astropy.units as u
from peegy.directories.tools import DirectoryPaths
from peegy.processing.events.event_tools import detect_events, get_events
import pandas as pd
from peegy.definitions.events import Events
from peegy.tools.units.unit_tools import set_default_unit
from peegy.definitions.events import SingleEvent
from typing import List
import pyqtgraph as pg
pg.setConfigOption('leftButtonPan', False)


class ReadInputData(InputOutputProcess):
    def __init__(self,
                 file_path: str | None = None,
                 channels_idx: np.array = np.array([]),
                 ini_time: u.quantity.Quantity = 0 * u.s,
                 end_time: u.quantity.Quantity = np.inf * u.s,
                 layout_file_name: str | None = None,
                 figures_folder: str | None = None,
                 figures_subset_folder: str = '',
                 fs_col_name: str | None = None,
                 gain_col_name: str | None = None,
                 fs_unit: u.quantity.Quantity = u.Hz,
                 gain_unit: u.quantity.Quantity = u.uV,
                 gain_inverted: bool = False,
                 event_channel_label: str | None = None,
                 data_unit: u.Unit = u.uV
                 ) -> InputOutputProcess:
        """
        This pipeline class handles reading eeg data files.

        :param file_path: path to file to be read
        :param channels_idx: numpy array indicating specifics channels to be read. If empty, all channels will be read
        :param ini_time: time in seconds from where to read data
        :param end_time: time in seconds up to where to read data
        :param layout_file_name: Name of layout mapping the channel labels to a specific topographic map
        :param figures_subset_folder: string used to generate a sub-folder within the main figure path. Useful to
        generate specific folder paths in a dynamic way.
        :param fs_col_name: provide the name of the column containing the sampling rate (used when data comes in .csv
        files)
        :param gain_col_name: provide the name of the column containing the gain to scale the data (used when data comes
         in .csv files)
        :param fs_unit: unit of sampling rate
        :param gain_unit: unit of gain
        :param gain_inverted: indicates whether the data will be multiplied or divided by the gain.
        :param event_channel_label: event_channel_label: string indicating the label of the channel containing all
         events. This is usually the 'Status' channel for bdf files and 'EDF Annotations' for EDF files, however, some
        devices provide other labels, e.g. 'BDF Annotations', therefore we leave this open
        :param data_unit: defines what data will be read from the files. This allows for filtering data with mixing
        units (uV, Celciusm, uS, etcetera).
        """
        super(ReadInputData, self).__init__()
        self.reader = None
        self.file_path = file_path
        self.channels_idx = channels_idx
        self.ini_time = ini_time
        self.end_time = end_time
        self.input_node = None
        self.layout_file_name = layout_file_name
        self.figures_subset_folder = figures_subset_folder
        self.figures_folder = figures_folder
        self.fs_col_name = fs_col_name
        self.gain_col_name = gain_col_name
        self.fs_unit = fs_unit
        self.gain_unit = gain_unit
        self.gain_inverted = gain_inverted
        self.event_channel_label = event_channel_label
        self.data_unit = data_unit

    def transform_data(self):
        self.reader = eeg_reader(file_name=self.file_path,
                                 fs_col_name=self.fs_col_name,
                                 gain_col_name=self.gain_col_name,
                                 fs_unit=self.fs_unit,
                                 gain_unit=self.gain_unit,
                                 gain_inverted=self.gain_inverted,
                                 event_channel_label=self.event_channel_label,
                                 data_unit=self.data_unit)
        data, events, units, annotations = self.reader.get_data(channels_idx=self.channels_idx,
                                                                ini_time=self.ini_time,
                                                                end_time=self.end_time)
        self.output_node = DataNode(data=data,
                                    fs=self.reader.fs,
                                    domain=Domain.time,
                                    layout=self.reader.default_layout,
                                    paths=DirectoryPaths(file_path=self.reader.file_name,
                                                         delete_all=False,
                                                         delete_figures=False,
                                                         figures_folder=self.figures_folder,
                                                         figures_subset_folder=self.figures_subset_folder)
                                    )
        if self.layout_file_name is not None:
            layout = layouts.Layout(file_name=self.layout_file_name)
            self.output_node.apply_layout(layout)
        self.output_node.events = self.get_events(events)
        self.output_node.events_annotations = annotations
        if annotations[0] is not None and annotations[1] is not None:
            to_print = pd.DataFrame.from_dict(
                {'Annotation': annotations[0],
                 'Code': annotations[1]})
            print(to_print.to_string())

    def get_events(self, events):
        _events = get_events(event_channel=events, fs=self.output_node.fs)
        return _events


class MergeMultipleFiles(InputOutputProcess):
    def __init__(self,
                 file_paths: List[str] | None = None,
                 channels_idx: np.array = np.array([]),
                 layout_file_name: str | None = None,
                 figures_folder: str | None = None,
                 figures_subset_folder: str = '',
                 fs_col_name: str | None = None,
                 gain_col_name: str | None = None,
                 fs_unit: u.quantity.Quantity = u.Hz,
                 gain_unit: u.quantity.Quantity = u.uV,
                 gain_inverted: bool = False
                 ) -> InputOutputProcess:
        super(MergeMultipleFiles, self).__init__()
        self.readers = np.array([])
        for _file in file_paths:
            _reader = eeg_reader(_file,
                                 fs_col_name=fs_col_name,
                                 gain_col_name=gain_col_name,
                                 fs_unit=fs_unit,
                                 gain_unit=gain_unit,
                                 gain_inverted=gain_inverted)
            self.readers = np.append(self.readers, _reader)
        self.file_paths = file_paths
        self.channels_idx = channels_idx
        self.ini_time = 0 * u.s
        self.end_time = np.inf * u.s
        self.output_node = None
        self.layout_file_name = layout_file_name
        self.figures_folder = figures_folder
        self.figures_subset_folder = figures_subset_folder
        self.output_node = DataNode(fs=self.readers[0].fs,
                                    domain=Domain.time,
                                    layout=self.readers[0].default_layout,
                                    paths=DirectoryPaths(file_path=self.readers[0].file_name,
                                                         delete_all=False,
                                                         delete_figures=False,
                                                         figures_folder=self.figures_folder,
                                                         figures_subset_folder=figures_subset_folder)
                                    )

    def transform_data(self):
        all_data = None
        all_events = None
        # sort readers by time
        _date_format = "%d.%m.%y/%H.%M.%S"
        dates = np.array([_reader._header['start_date'] + '/' + _reader._header['start_time'] for
                          _reader in self.readers])
        sorted_idx = np.argsort([datetime.datetime.strptime(_date, _date_format) for _date in dates])
        print(dates[sorted_idx])
        for _reader in self.readers[sorted_idx]:
            data, events, units, annotations = _reader.get_data(channels_idx=self.channels_idx,
                                                                ini_time=self.ini_time,
                                                                end_time=self.end_time)

            # demean data
            data = data - np.mean(data, axis=0)
            if all_data is not None:
                all_data = np.concatenate((all_data, data))
                all_events = np.concatenate((all_events, events))
            else:
                all_data = data
                all_events = events

        self.output_node = DataNode(data=all_data,
                                    fs=self.readers[0].fs,
                                    domain=Domain.time,
                                    layout=self.readers[0].default_layout,
                                    )
        if self.layout_file_name is not None:
            self.output_node.apply_layout(layouts.Layout(file_name=self.layout_file_name))

        self.output_node.paths = self.input_node.paths
        self.get_events(all_events)

    def get_events(self, events):
        events = detect_events(event_channel=events, fs=self.output_node.fs)
        events = Events(events=np.array(events))
        for i, _code in enumerate(np.unique(events.get_events_code())):
            print('Event code:', _code, 'Number of events:', events.get_events_code(code=_code).size)
        self.output_node.events = events


class GenericInputData(InputOutputProcess):
    def __init__(self,
                 data: type(np.array) | None = None,
                 fs: u.quantity.Quantity = 16384.0 * u.Hz,
                 events_index: int | None = None,
                 event_times: type(np.array) | None = None,
                 event_code: float = 1.0,
                 figures_folder: str | None = None,
                 channel_labels: List[str] | None = None,
                 figures_subset_folder: str = '') -> InputOutputProcess:
        """
        This class allows to pass your own data without the need of having a bdf or edf file. Data will be used to
        create a compatible InoutOutputProcess that can be use straightforward in the pipeline.
        This InputOutput process takes a numpy matrix and uses it to generate a generic layout.
        :param data: numpy array (2D or 3D array; samples x channels x trials)
        :param fs: the sampling rate of the template_waveform
        :param events_index: integer in which column are the events included
        :param event_times: numpy array with the timing of the events. Events are only useful when input data is a 2D
        numpy array.
        :param event_code: desired event code to be assigned to time events
        :param figures_folder: path to save generated figures
        :param figures_subset_folder: string indicating a sub-folder name in figures_path
        """
        super(GenericInputData, self).__init__()
        events = None
        if events_index is not None:
            events = data[:, np.arange(data.shape[1]) == events_index]
            data = data[:, np.arange(data.shape[1]) != events_index]
        self.events = events
        self.data = set_default_unit(copy.copy(data), u.uV)
        self.fs = set_default_unit(fs, u.Hz)
        self.event_times = set_default_unit(event_times, u.s)
        self.event_code = event_code
        self.output_node = None
        self.figures_folder = figures_folder
        self.figures_subset_folder = figures_subset_folder

        _ch = []
        n_channels = self.data.shape[1]
        if channel_labels is None:
            [_ch.append(ChannelItem(label='CH_{:}'.format(i), idx=i)) for i in range(n_channels)]
        else:
            [_ch.append(ChannelItem(label=_label, idx=i)) for i, _label in
             zip(range(n_channels), channel_labels)]
        layout = np.array(_ch)
        self.output_node = DataNode(fs=fs,
                                    domain=Domain.time,
                                    layout=layout,
                                    paths=DirectoryPaths(delete_all=False,
                                                         delete_figures=False,
                                                         figures_folder=self.figures_folder,
                                                         figures_subset_folder=figures_subset_folder),
                                    )

    def transform_data(self):
        events = np.array([])
        if self.event_times is not None:
            for _ev in self.event_times:
                events = np.append(events, SingleEvent(code=self.event_code,
                                                       time_pos=_ev,
                                                       dur=0 * u.s))
        events = Events(events=np.array(events))
        if self.events is not None:
            events = self.get_events(self.events)
        self.output_node = DataNode(data=self.data,
                                    fs=self.fs,
                                    domain=Domain.time,
                                    layout=self.input_node.layout,
                                    )
        self.output_node.paths = self.input_node.paths
        self.output_node.events = events

    def get_events(self, events):
        _events = get_events(event_channel=events, fs=self.fs)
        return _events


class EclipseReader(InputOutputProcess):
    def __init__(self,
                 file_path: type(np.array) | None = None,
                 figures_folder: str | None = None,
                 buffer: str = 'A_&_B',
                 figures_subset_folder: str = '',
                 brick_keyword_left: str = 'LeftBricks',
                 brick_keyword_right: str = 'RightBricks',
                 ) -> InputOutputProcess:
        """
        This class will parse Eclipse data contained in buffers A or B (provided in .tex files by Eclipse software)
        :param data_path: path to the file
        :param buffer: 'A', 'B', 'A_&_B' (or None). This will return the desired buffers contained in the data
        :param figures_folder: path to save generated figures
        :param figures_subset_folder: string indicating a sub-folder name in figures_folder
        :param brick_keyword_left: string used to find if text file corresponds to left bricks
        :param brick_keyword_right: string used to find if text file corresponds to right bricks
        """
        super(EclipseReader, self).__init__()
        self.header = None
        self.output_node = None
        self.buffer = buffer
        self.brick_keyword_left = brick_keyword_left
        self.brick_keyword_right = brick_keyword_right
        self.file_path = file_path
        self.figures_folder = figures_folder
        self.figures_subset_folder = figures_subset_folder
        self.output_node = DataNode(fs=None,
                                    domain=Domain.time,
                                    layout=None,
                                    paths=DirectoryPaths(file_path=str(self.file_path),
                                                         delete_all=False,
                                                         delete_figures=False,
                                                         figures_folder=self.figures_folder,
                                                         figures_subset_folder=figures_subset_folder)
                                    )

    def transform_data(self):
        events = np.array([])
        events = Events(events=np.array(events))
        header, data, data_buffer_a, data_buffer_b = parse_eclipse_data(
            file_name=self.file_path,
            brick_keyword_left=self.brick_keyword_left,
            brick_keyword_right=self.brick_keyword_right
        )
        if self.buffer == 'A':
            _data = data_buffer_a
        elif self.buffer == 'B':
            _data = data_buffer_b
        elif self.buffer == 'A_&_B' or None:
            _data = data
            self.buffer == 'A_&_B'
        _ch = [ChannelItem(label=header['channel'])]
        layout = np.array(_ch)
        fs = header['Sample rate'] * u.Hz
        self.header = header
        self.output_node = DataNode(data=_data,
                                    fs=fs,
                                    domain=Domain.time,
                                    layout=layout,
                                    )
        self.output_node.paths = self.input_node.paths
        self.output_node.events = events
        self.output_node.x_offset = -header['Time offset in samples'] / fs
