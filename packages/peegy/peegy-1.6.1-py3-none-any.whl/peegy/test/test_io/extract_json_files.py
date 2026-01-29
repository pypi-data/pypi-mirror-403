# -*- coding: utf-8 -*-
import os
from peegy.io.external_tools.aep_gui.dataReadingTools import get_files_and_meta_data
from peegy.io.external_tools.aep_gui.extsys_tools import extsys_to_json
import matplotlib
if 'Qt5Agg' in matplotlib.rcsetup.all_backends:
    matplotlib.use('Qt5Agg')

if __name__ == "__main__":
    eeg_data_directory = r'/home/jundurraga/Documents/Measurements/peegy_data/IPM-FR/'
    to_process = get_files_and_meta_data(eeg_data_directory)

    for _, _data_links in to_process.iterrows():
        _, _name = os.path.split(_data_links.data_links.data_file)
        extsys_to_json(input_file_name=_data_links.data_links.parameters_file,
                       output_file_name=_name,
                       trash_original=True)
