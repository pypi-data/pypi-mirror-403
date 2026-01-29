from peegy.io.paths.defaults import default_path
from peegy.io.eeg.reader import eeg_reader
from peegy.io.exporters.wav_writer import data_to_wav
from peegy.tools.signal_generator.noise_functions import generate_modulated_noise
import numpy as np
from peegy.processing.events.event_tools import Events, SingleEvent
import matplotlib.pyplot as plt
import astropy.units as u
import matplotlib
if 'Qt5Agg' in matplotlib.rcsetup.all_backends:
    matplotlib.use('Qt5Agg')


fs = 1000 * u.Hz
duration = 10 * u.s
n_channels = 1
data = generate_modulated_noise(
    fs=fs.to(u.Hz).value,
    duration=duration.to(u.s). value,
    n_channels=n_channels)
events = Events(events=np.array([SingleEvent(code=1,
                                             time_pos=_i * duration / 20,
                                             dur=1 * u.ms) for _i in range(10)]))

output_file_path = str(default_path.joinpath('test.wav'))
_file_path = ''
reader = eeg_reader(file_name=_file_path)

_wav_data, _wav_fs = data_to_wav(data=data,
                                 events=events,
                                 fs=fs,
                                 fs_wav=10000 * u.Hz,
                                 output_file_name=output_file_path)
#
fig1 = plt.figure(figsize=(7, 6), dpi=100)
t_original = np.arange(data.shape[0]) / fs
t_wav = np.arange(_wav_data.shape[0]) / _wav_fs
ax = fig1.add_subplot(1, 1, 1)
ax.plot(t_original, data)
ax.plot(t_wav, _wav_data)
plt.show()
