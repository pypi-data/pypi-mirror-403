# -*- coding: utf-8 -*-
from peegy.io.eeg.reader import eeg_reader
from peegy.io.exporters.edf_bdf_writer import change_subject_id
from peegy.io.external_tools.file_tools import get_files_and_meta_files
import os
from pathlib import Path

_path = Path(os.path.abspath(os.path.dirname(__file__)))
data_folder = _path.parent.parent.absolute().joinpath("test_data/")
eeg_data_directory = r'/home/jundurraga/Documents/Measurements/peegy_data/IPM-FR/LVY-March-9-2017/'
data_files_meta = get_files_and_meta_files(eeg_data_directory, file_types=['bdf'])
_first_file = data_files_meta.iloc[0].data_links.data_file
_reader = eeg_reader(file_name=_first_file)
print(_reader._header['subject_id'])
change_subject_id(file_name=_first_file, subject_id='S02')
_reader = eeg_reader(file_name=_first_file)
print(_reader._header['subject_id'])
