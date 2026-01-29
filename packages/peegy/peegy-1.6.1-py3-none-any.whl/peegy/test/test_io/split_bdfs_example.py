# -*- coding: utf-8 -*-
from peegy.io.exporters.edf_bdf_writer import split_bdf_by_event_code
from peegy.io.external_tools.aep_gui.dataReadingTools import get_files_and_meta_data

import matplotlib
if 'Qt5Agg' in matplotlib.rcsetup.all_backends:
    matplotlib.use('Qt5Agg')

if __name__ == "__main__":
    eeg_data_directory = r'/home/jundurraga/Documents/Measurements/peegy_data/IPM-FR/'
    to_process = get_files_and_meta_data(eeg_data_directory)

    for _, _data_links in to_process.iterrows():
        split_bdf_by_event_code(input_file_name=_data_links.data_links.data_file,
                                event_code=16.0,
                                trash_original=True)
