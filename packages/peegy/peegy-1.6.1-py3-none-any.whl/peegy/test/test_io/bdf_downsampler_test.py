import matplotlib.pyplot as plt
from peegy.io.eeg.reader import eeg_reader
from peegy.io.exporters.edf_bdf_writer import bdf_resampler
from peegy.io.external_tools.file_tools import get_files_and_meta_files
import numpy as np
from peegy.processing.events.event_tools import get_events
import os
from pathlib import Path
import matplotlib
import astropy.units as u
if 'Qt5Agg' in matplotlib.rcsetup.all_backends:
    matplotlib.use('Qt5Agg')


_path = Path(os.path.abspath(os.path.dirname(__file__)))
data_folder = _path.parent.parent.absolute().joinpath("test_data/")
eeg_data_directory = r'/home/jundurraga/Documents/Measurements/peegy_data/IPM-FR/'
data_files_meta = get_files_and_meta_files(eeg_data_directory, file_types=['bdf'])

for _, _file in data_files_meta.iterrows():
    output_file_path = _path.parent.parent.absolute().joinpath('split_test')
    _file_path = _file.data_links.data_file
    bdf_resampler(input_file_name=_file_path,
                  # output_path=output_file_path,
                  new_fs=1024 * u.Hz,
                  trash_original=True)

data_files_meta = get_files_and_meta_files(eeg_data_directory, file_types=['bdf'])
_first_file = data_files_meta.iloc[0].data_links.data_file
data4 = eeg_reader(file_name=_first_file)
data_ds, events_ds, _, _ = data4.get_data(channels_idx=np.array([0]))
et_ds = get_events(event_channel=events_ds, fs=data4.fs)
et_ds.summary()
fig1 = plt.figure(figsize=(7, 6), dpi=100)
t_ds = np.arange(data_ds.shape[0]) / data4.fs
ax = fig1.add_subplot(1, 1, 1)
ax.plot(t_ds, data_ds[:, 0])
ax.plot(t_ds, events_ds)
plt.show()
