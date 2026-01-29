import matplotlib.pyplot as plt
from peegy.io.eeg.reader import eeg_reader
from peegy.io.exporters.edf_bdf_writer import data_to_bdf
from peegy.io.external_tools.file_tools import get_files_and_meta_files
import numpy as np
from peegy.processing.events.event_tools import get_events, events_to_samples_array
import os
from pathlib import Path

_path = Path(os.path.abspath(os.path.dirname(__file__)))
data_folder = _path.parent.parent.absolute().joinpath("test_data/")
data_folder = r'/home/jundurraga/Documents/Measurements/ITD-FR-Pilots/JU/'
data_files_meta = get_files_and_meta_files(data_folder, file_types=['bdf'])
_first_file = data_files_meta.iloc[0].data_links.data_file
data_1 = eeg_reader(file_name=_first_file)
header = data_1._header
data_ori, events_ori, units_ori, annotations_ori = data_1.get_data()
et = get_events(event_channel=events_ori, fs=data_1.fs)
events_array = events_to_samples_array(events=et, fs=data_1.fs, n_samples=data_1.shape[0])

data_to_bdf(output_file_name=_path.parent.parent.absolute().joinpath('deleteme_resampled.bdf'),
            data=data_ori,
            events=events_array,
            header=header,
            fs=data_1.fs)

data_2 = eeg_reader(file_name=_path.parent.parent.absolute().joinpath('deleteme_resampled.bdf'))
data_copy, events_copy, _, _ = data_2.get_data()
et_copy = get_events(event_channel=events_copy, fs=data_2.fs)
et_copy.summary()
fig1 = plt.figure(figsize=(7, 6), dpi=100)
t_original = np.arange(data_ori.shape[0]) / data_1.fs
t_copy = np.arange(data_copy.shape[0]) / data_2.fs
ax = fig1.add_subplot(1, 1, 1)
ax.plot(t_original, data_ori[:, 0])
ax.plot(t_original, events_ori)
ax.plot(t_copy, data_copy[:, 0])
ax.plot(t_copy, events_copy)
plt.show()
