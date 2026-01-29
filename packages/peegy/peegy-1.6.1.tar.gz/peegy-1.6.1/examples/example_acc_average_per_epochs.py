"""
.. _tut-acc-standard-weighted-average-per-epochs-pipeline-sim:

##################################################################
ACC Standard analysis with by epochs (Simulated)
##################################################################

In this example we simulate an ACC response and average by epochs.
This is useful if you are interested in test how things improve as you collect more and more epochs
"""
# Enable below for interactive backend
# import matplotlib
# if 'Qt5Agg' in matplotlib.rcsetup.all_backends:
#     matplotlib.use('Qt5Agg')
from peegy.processing.pipe.pipeline import PipePool
from peegy.processing.pipe.simulate import GenerateInputData
from peegy.processing.tools.detection.definitions import TimeROI
from peegy.processing.tools.template_generator.auditory_waveforms import aep
from peegy.processing.pipe.general import FilterData
from peegy.processing.pipe.epochs import EpochData, AverageEpochs
from peegy.processing.pipe.epoching.epoching import EpochsByStep
from peegy.processing.pipe.storage import MeasurementInformation, SubjectInformation, SaveToDatabase
from peegy.io.storage.data_storage_reading_tools import sqlite_tables_to_pandas
import seaborn as sns
import os
import numpy as np
import astropy.units as u

# %%
# Time regions of interest
# ============================
# TimeROI are defined as time regions where different measures will be performed, e.g. SNR measure or statistical
# measures

roi_windows = np.array(
    [
        TimeROI(
            ini_time=50.0 * u.ms,
            end_time=550.0 * u.ms,
            label="analysis_window",
        )
    ]
)

# %%
# Generate some data
# ===================
# First we generate some ACC data

n_channels = 32
fs = 512.0 * u.Hz
template_waveform, _ = aep(fs=fs)
n_events = 100
event_times = np.arange(0, n_events, 1.0) * u.s
snr_db = 10
snr = 10 ** (snr_db / 10) / n_events
reader = GenerateInputData(template_waveform=template_waveform,
                           fs=fs,
                           n_channels=n_channels,
                           mixing_matrix=np.diag(np.ones(n_channels)),
                           layout_file_name='biosemi32.lay',
                           snr=snr,
                           event_times=event_times,
                           event_code=1.0,
                           figures_subset_folder='acc_test_per_epochs',
                           include_eog_events=False,
                           noise_attenuation=3,
                           noise_seed=0,
                           f_noise_low=0 * u.Hz,
                           f_noise_high=fs / 2,
                           f_var_low=2 * u.Hz,
                           f_var_high=30 * u.Hz,
                           neural_ini_time_snr=roi_windows[0].ini_time,
                           neural_end_time_snr=roi_windows[0].end_time,
                           )
reader.run()

# %%
# Start the pipeline
# ============================
# Now we proceed with our basic processing pipeline


pipeline = PipePool()
# %%
# Start the pipeline
# ------------------------------------
pipeline['time_filtered_data'] = FilterData(reader,
                                            high_pass=2.0 * u.Hz,
                                            low_pass=30.0 * u.Hz)

pipeline.run()

# %%
# Get Epochs
# ------------------------------------
# We partition the data into epochs or trials based on the event code used.


pipeline['time_epochs'] = EpochData(pipeline['time_filtered_data'],
                                    event_code=1.0)

# %%
# Start per epochs pipeline and compute average
# ------------------------------------------------

pipeline_epochs = PipePool()
pipeline_epochs['average'] = AverageEpochs(pipeline['time_epochs'],
                                           roi_windows=roi_windows,
                                           weighted_average=True,
                                           weight_across_epochs=False)

# now we save our data to a database
subject_info = SubjectInformation(subject_id='Test_Subject')
measurement_info = MeasurementInformation(
    date='Today',
    experiment='sim')

_parameters = {'Type': 'ACC'}

database_path = reader.input_node.paths.test_path.joinpath('acc_test_per_epochs.sqlite')
pipeline_epochs['database'] = SaveToDatabase(database_path=str(database_path),
                                             measurement_information=measurement_info,
                                             subject_information=subject_info,
                                             recording_information={'recording_device': 'dummy_device'},
                                             stimuli_information=_parameters,
                                             processes_list=[pipeline_epochs['average']],
                                             include_waveforms=False,
                                             )

pipeline['per_epochs'] = EpochsByStep(at_each_epoch_block_do=pipeline_epochs,
                                      epochs_step_size=2,
                                      deep_break=False,
                                      max_epochs=1000)

pipeline.run()

# %% Plots some results
df = sqlite_tables_to_pandas(database_path=str(database_path),
                             tables=['f_test_time'])['f_test_time']

fig_out = sns.lineplot(data=df,
                       x='n_epochs',
                       y='rn',
                       hue='channel')

# %%
# Generate pipeline diagram
# ------------------------------------
pipeline.diagram(file_name=reader.output_node.paths.figures_current_dir + 'pipeline.png',
                 return_figure=True,
                 dpi=600)
