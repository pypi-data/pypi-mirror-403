"""
.. _tut-FFR-artefact-removal-test-sim:

########################################################
FFR Artefact removal example (Simulated)
########################################################

In this example we simulate an FFR, and we remove artefacts via a regression method.
This method attempts to regress out a reference artefact signal from any other channel by estimating the transmission
index (scalar factor) that is then applied to the reference artefact signal to then subtract the scaled signal from
each channel.

"""
# Enable below for interactive backend
# import matplotlib
# if 'qt5agg' in matplotlib.backends.backend_registry.list_builtin():
#     matplotlib.use('qt5agg')
import copy
from peegy.processing.pipe.pipeline import PipePool
from peegy.processing.pipe.general import ReferenceData, FilterData, AutoRemoveBadChannels, ReSampling
from peegy.processing.pipe.epochs import EpochData, AverageEpochsFrequencyDomain
from peegy.processing.pipe.regression import RegressOutArtifact
from peegy.processing.pipe.plot import PlotTopographicMap, PlotWaveforms
from peegy.processing.pipe.simulate import GenerateInputData
from peegy.processing.pipe.storage import MeasurementInformation, SubjectInformation, SaveToDatabase
import os
import astropy.units as u
from peegy.processing.tools.filters.resampling import eeg_resampling
import numpy as np

# %%
# Generate some data
# ========================
# We generate some artefactual and frequency-following data. In this example the stimulation source and the brain
# source have different delays


fs = 2048.0 * u.Hz
epoch_length = 1.0 * u.s
epoch_length = np.ceil(epoch_length * fs) / fs  # fit to fs rate
burst_duration = 0.375 * u.s
ffr_frequencies = np.array([60, 120, 180]) * u.Hz
ffr_frequencies = np.ceil(burst_duration * ffr_frequencies) / burst_duration  # fit to burst_duration length
alternating_polarity = False  # stimulus is alternating in polarity every presentation
# here we pick some random frequencies to test statistical detection
random_frequencies = np.unique(np.random.randint(50, 200, 3)) * u.Hz
stim_delay = 0.001 * u.s  # neural delay in secs
brain_delay = 0.0237 * u.s
time = np.arange(0, burst_duration.to(u.s).value, 1 / fs.to(u.Hz).value).reshape(-1, 1) * u.s
# stimulation waveform
_original_stimulus_waveform = np.sum(
    3 * np.sin(2 * np.pi * u.rad * ffr_frequencies * time),
    axis=1).reshape(-1, 1) * 1.0 * u.uV  # generates ffr artifacts with 1 uV amplitude

stimulus_waveform = np.pad(_original_stimulus_waveform, ((int(fs * stim_delay), int(fs * brain_delay)),
                                                         (0, 0)), 'constant', constant_values=(0, 0))
# brain response
template_waveform = np.pad(_original_stimulus_waveform, ((int(fs * stim_delay) + int(fs * brain_delay), 0), (0, 0)),
                           'constant', constant_values=(0, 0))
template_waveform *= 0.2  # 0.2 uV amplitude and a delay
template_waveform[template_waveform < 0] = 0  # rectify

n_channels = 16
event_times = np.arange(0, 360.0, epoch_length.to(u.s).value) * u.s
artefact_mixing_matrix = np.zeros(n_channels)
artefact_mixing_matrix[5:12] = 1
artefact_mixing_matrix = np.diag(artefact_mixing_matrix)
reader = GenerateInputData(template_waveform=template_waveform,
                           mixing_matrix=np.diag(np.arange(n_channels) / n_channels),
                           stimulus_waveform=stimulus_waveform,
                           alternating_polarity=alternating_polarity,
                           artefacts_mixing_matrix=artefact_mixing_matrix,
                           fs=fs,
                           n_channels=n_channels,
                           snr=0.5,
                           layout_file_name='biosemi16.lay',
                           event_times=event_times,
                           event_code=1.0,
                           figures_subset_folder='ffr_artifact_test',
                           noise_seed=0)
reader.run()

# %%
# Start the pipeline
# ========================


new_fs = fs / 2
pipeline = PipePool()
pipeline['referenced'] = ReferenceData(reader,
                                       reference_channels=['Cz'],
                                       invert_polarity=True)
pipeline['channel_cleaned'] = AutoRemoveBadChannels(pipeline['referenced'])

pipeline['down_sampled'] = ReSampling(pipeline['channel_cleaned'],
                                      new_sampling_rate=new_fs)
pipeline['time_filtered_data'] = FilterData(pipeline['down_sampled'],
                                            high_pass=2.0 * u.Hz,
                                            low_pass=None)
pipeline.run()

# replace neural data in reader to generate figures too
target = copy.copy(reader)
target.output_node.data = target.simulated_neural_response
pipeline['target_referenced'] = ReferenceData(reader,
                                              reference_channels=['Cz'],
                                              invert_polarity=True)
pipeline['down_sampled_target'] = ReSampling(pipeline['target_referenced'],
                                             new_sampling_rate=new_fs)

# %%
# Now we down sample the stimulus waveform
# ---------------------------------------------
# Here, the stimulus waveform (usually recorded as an EEG channel) is down sampled to have the same temporal resolution
# as the simulated brain data


rs_stimulus_waveform, _ = eeg_resampling(x=stimulus_waveform,
                                         new_fs=new_fs,
                                         fs=fs)

# %%
# Now regress out the stimulus waveform from the simulated EEG datagit
# --------------------------------------------------------------------


pipeline['artifact_free'] = RegressOutArtifact(pipeline['time_filtered_data'],
                                               event_code=1.0,
                                               alternating_polarity=alternating_polarity,
                                               stimulus_waveform=rs_stimulus_waveform,
                                               method='regression'
                                               )
pipeline.run()

# %%
# Comparing recorded and cleaned waveforms
# ---------------------------------------------

pipeline['artifact_free'].plot(plot_input=True,
                               plot_output=True,
                               ch_to_plot=np.array(['O2', 'T8', 'T7']),
                               interactive=False)

# %%
# Get Epochs
# ---------------------------------------------
# We partition the data into epochs or trials based on the event code used.

pipeline['time_epochs_no_artefacts'] = EpochData(pipeline['artifact_free'],
                                                 event_code=1.0,
                                                 base_line_correction=False,
                                                 post_stimulus_interval=burst_duration / 1.0)

pipeline['time_epochs_with_artefacts'] = EpochData(pipeline['time_filtered_data'],
                                                   event_code=1.0,
                                                   base_line_correction=False,
                                                   post_stimulus_interval=burst_duration / 1.0)

pipeline['time_target'] = EpochData(pipeline['down_sampled_target'],
                                    event_code=1.0,
                                    base_line_correction=False,
                                    post_stimulus_interval=burst_duration / 1.0)
pipeline.run()

# %%
# Get average in frequency-domain of data without using spatial-filtering
# ---------------------------------------------------------------------------


pipeline['fft_ave_no_artefacts'] = AverageEpochsFrequencyDomain(pipeline['time_epochs_no_artefacts'],
                                                                test_frequencies=np.concatenate((
                                                                    ffr_frequencies, random_frequencies)),
                                                                n_fft=int(burst_duration * new_fs)
                                                                )
pipeline.run()
pipeline['fft_ave_with_artefacts'] = AverageEpochsFrequencyDomain(pipeline['time_epochs_with_artefacts'],
                                                                  test_frequencies=np.concatenate((
                                                                      ffr_frequencies, random_frequencies)),
                                                                  n_fft=int(burst_duration * new_fs)
                                                                  )
pipeline.run()
pipeline['fft_target'] = AverageEpochsFrequencyDomain(pipeline['time_target'],
                                                      test_frequencies=np.concatenate((
                                                          ffr_frequencies, random_frequencies)),
                                                      n_fft=int(burst_duration * new_fs)
                                                      )
pipeline.run()


# %%
# Plot frequency-domain average of data
# ---------------------------------------------------------------------------


pipeline['plotter_1'] = PlotTopographicMap(pipeline['fft_ave_no_artefacts'],
                                           topographic_channels=np.array(['O2', 'T8', 'T7']),
                                           plot_x_lim=[50, 200],
                                           plot_y_lim=[0, 0.5],
                                           return_figures=True,
                                           user_naming_rule='fft_ave_no_artefacts')

pipeline['plotter_2'] = PlotTopographicMap(pipeline['fft_ave_with_artefacts'],
                                           topographic_channels=np.array(['O2', 'T8', 'T7']),
                                           plot_x_lim=[50, 200],
                                           plot_y_lim=[0, 0.5],
                                           return_figures=True,
                                           user_naming_rule='fft_ave_with_artefacts')

pipeline['plotter_3'] = PlotTopographicMap(pipeline['fft_target'],
                                           topographic_channels=np.array(['O2', 'T8', 'T7']),
                                           plot_x_lim=[50, 200],
                                           plot_y_lim=[0, 0.5],
                                           return_figures=True,
                                           user_naming_rule='target')

# %%
# Plot target and rescued signal
# ---------------------------------------------------------------------------

pipeline['plotter_4'] = PlotWaveforms(pipeline['fft_ave_no_artefacts'],
                                      overlay=[pipeline['fft_target']],
                                      ch_to_plot=np.array(['O2', 'T8', 'T7']),
                                      plot_x_lim=[50, 200],
                                      plot_y_lim=[-1, 0.3],
                                      return_figures=True,
                                      user_naming_rule='waves_target_rescued')

pipeline.run()

# %%
# Get generated data and save to database for data with and without dss
# ---------------------------------------------------------------------------
# We get the measurements we are interested in and save them into a database

subject_info = SubjectInformation(subject_id='Test_Subject')
measurement_info = MeasurementInformation(
    date='Today',
    experiment='sim')

_parameters = {'Type': 'FFR'}
database_path = reader.input_node.paths.test_path.joinpath('ffr_ht2_test.sqlite')
pipeline['database'] = SaveToDatabase(database_path=database_path,
                                      measurement_information=measurement_info,
                                      subject_information=subject_info,
                                      recording_information={'recording_device': 'dummy_device'},
                                      stimuli_information=_parameters,
                                      processes_list=[pipeline['fft_ave_no_artefacts'],
                                                      pipeline['fft_ave_with_artefacts']],
                                      include_waveforms=False
                                      )
pipeline.run()

# %%
# Generate pipeline diagram
# ------------------------------------
pipeline.diagram(file_name=reader.output_node.paths.figures_current_dir + 'pipeline.png',
                 return_figure=True,
                 dpi=600)
