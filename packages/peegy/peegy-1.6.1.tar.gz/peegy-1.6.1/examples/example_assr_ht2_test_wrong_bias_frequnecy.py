"""
.. _tut-assr-ht2-test-sim-wrong-bias:

############################################################################################
ASSR Hotelling-T2 test with spatial filtering biased with wrong frequencies(Simulated)
############################################################################################

In this example we simulate an ASSR and we assess its significance using the Hotelling's T2 test.
However, we used DSS with a bias frequency which does not correspond to the ASSR frequency. This is a wrong bias and
the example illustrates how this may significantly reduce the amplitude of the ASSR.
This method uses the real and imaginary part of the frequency bin of interest to assess whether the points from
each epoch are significantly different from zero (the center of the polar complex-plane).

"""
# Enable below for interactive backend
# import matplotlib
# if 'qt5agg' in matplotlib.backends.backend_registry.list_builtin():
#     matplotlib.use('qt5agg')
from peegy.processing.pipe.pipeline import PipePool
from peegy.processing.pipe.definitions import Events, Domain
from peegy.processing.pipe.general import ReferenceData, FilterData, AutoRemoveBadChannels
from peegy.processing.pipe.epochs import AverageEpochsFrequencyDomain, EpochData
from peegy.processing.pipe.attach import AppendGFPChannel
from peegy.processing.pipe.statistics import FTest
from peegy.processing.pipe.plot import PlotWaveforms, PlotTopographicMap
from peegy.processing.pipe.spatial_filtering import CreateAndApplySpatialFilter
from peegy.processing.pipe.simulate import GenerateInputData
from peegy.processing.tools.template_generator.auditory_waveforms import aep
from peegy.processing.pipe.storage import MeasurementInformation, SubjectInformation, SaveToDatabase
import os
import astropy.units as u
import numpy as np


# %%
# Generate some data
# ===================
# We generate some auditory steady-state response (ASSR)

fs = 256.0 * u.Hz
epoch_length = 4.0 * u.s
epoch_length = np.ceil(epoch_length * fs) / fs  # fit to fs rate
assr_frequency = 41.0 * u.Hz
assr_frequency = np.ceil(epoch_length * assr_frequency) / epoch_length  # fit to epoch length
# we select several unrelated frequencies to the ASSR to bias the filter
wrong_bias = np.array([13, 26, 39]) * u.Hz
test_frequencies = np.concatenate((
    [assr_frequency,
     2 * assr_frequency],
    wrong_bias
))
template_waveform, _ = aep(fs=fs)
n_channels = 32
event_times = np.arange(0, 360.0, 1 / assr_frequency.to(u.Hz).value) * u.s
reader = GenerateInputData(template_waveform=template_waveform,
                           fs=fs,
                           n_channels=n_channels,
                           mixing_matrix=np.diag(np.arange(n_channels))/n_channels,
                           snr=0.05,
                           layout_file_name='biosemi32.lay',
                           event_times=event_times,
                           event_code=1.0,
                           noise_attenuation=0,
                           return_noise_only=False,
                           figures_subset_folder='assr_ht2_test_wrong_bias')
reader.run()
# %%
# Resize events
# =======================
# Now we keep events at intervals that correspond to our desired epoch length


events = reader.output_node.events.get_events(code=1)
# skip events to preserve only those at each epoch point
_new_events = Events(events=events[0:-1:int(epoch_length * assr_frequency)])
reader.output_node.events = _new_events


# %%
# Start the pipeline
# ============================
# Some processing to obtain clean epochs


pipeline = PipePool()
pipeline['referenced'] = ReferenceData(reader,
                                       reference_channels=['Cz'],
                                       invert_polarity=True)
pipeline['channel_cleaned'] = AutoRemoveBadChannels(pipeline['referenced'])
pipeline['time_filtered_data'] = FilterData(pipeline['channel_cleaned'],
                                            high_pass=0.05 * u.Hz,
                                            low_pass=None)
pipeline['time_epochs'] = EpochData(pipeline['time_filtered_data'],
                                    event_code=1.0,
                                    base_line_correction=False)
pipeline.run()

# %%
# Compute and plot components in the frequency-domain
# ----------------------------------------------------
# Spatial filter is a applied in the frequency-domain

pipeline['dss_time_epochs'] = CreateAndApplySpatialFilter(pipeline['time_epochs'],
                                                          sf_join_frequencies=wrong_bias,
                                                          test_frequencies=test_frequencies,
                                                          projection_domain=Domain.frequency,
                                                          plot_y_lim=[0, 1],
                                                          return_figures=True
                                                          )
pipeline.run()

# %%
# Compute global field power (GFP)
# ----------------------------------
# We compute the GFP across channels and epochs. A new channel with the GFP is appended to the data


pipeline['dss_time_epochs_with_gfp'] = AppendGFPChannel(pipeline['dss_time_epochs'])
pipeline.run()

# %%
# Average epochs
# ----------------------------------
# We compute the average and simultaneously get statistical tests on the test_frequencies


pipeline['fft_ave'] = AverageEpochsFrequencyDomain(pipeline['dss_time_epochs_with_gfp'],
                                                   n_fft=int(epoch_length*fs),
                                                   test_frequencies=test_frequencies)

pipeline['fft_ave_f_test'] = FTest(pipeline['fft_ave'],
                                   test_frequencies=test_frequencies,
                                   delta_frequency=15 * u.Hz)

pipeline['std_fft_ave'] = AverageEpochsFrequencyDomain(pipeline['time_epochs'],
                                                       n_fft=int(epoch_length * fs),
                                                       test_frequencies=test_frequencies)

pipeline.run()

pipeline['fft_ave_f_test'].output_node.statistical_tests['f_test_freq'][
    ["test_name", "df_1", "df_2", "f", "f_critic", "p_value"]].head()

# %%
# Generate figures
# ----------------------------------
# Now we run plot the average waveforms and show the stats


pipeline['waveforms'] = PlotWaveforms(pipeline['std_fft_ave'],
                                      overlay=[pipeline['fft_ave']],
                                      plot_x_lim=[0, 90],
                                      ch_to_plot=np.array(['O2', 'T8', 'T7']),
                                      user_naming_rule='standard_and_dss',
                                      statistical_test='hotelling_t2_freq',
                                      show_following_stats=['test_name', 'f', 'frequency_tested'],
                                      return_figures=True)

pipeline['topographic_map'] = PlotTopographicMap(pipeline['fft_ave'],
                                                 topographic_channels=np.array(['O2', 'T8', 'T7', 'GFP']),
                                                 plot_x_lim=[0, 90],
                                                 plot_y_lim=[0, 6],
                                                 return_figures=True)
pipeline.run()
# %%
# Save results to a database
# ----------------------------------
# We get the measurements we are interested in and save them into a database

subject_info = SubjectInformation(subject_id='Test_Subject')
measurement_info = MeasurementInformation(
    date='Today',
    experiment='sim')

_parameters = {'Type': 'ASSR'}
database_path = reader.input_node.paths.test_path.joinpath('assr_ht2_test_wrong_bias.sqlite')
pipeline['database'] = SaveToDatabase(database_path=database_path,
                                      measurement_information=measurement_info,
                                      subject_information=subject_info,
                                      recording_information={'recording_device': 'dummy_device'},
                                      stimuli_information=_parameters,
                                      processes_list=[pipeline['fft_ave']],
                                      include_waveforms=True
                                      )
pipeline.run()

# %%
# Generate pipeline diagram
# ------------------------------------
pipeline.diagram(file_name=reader.output_node.paths.figures_current_dir + 'pipeline.png',
                 return_figure=True,
                 dpi=600)
