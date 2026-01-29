import re
from pathlib import Path
from peegy.definitions.events import Events
from peegy.io.exporters.edf_bdf_writer import data_to_bdf
from peegy.processing.pipe.io import ReadInputData
import pandas as pd
import json
import os
import shutil
import astropy.units as u
from typing import List


class BIDS_EEG_JSON(object):
    def __init__(self,
                 TaskName: str = "Hearing sounds",
                 InstitutionName: str = "Interacoustics",
                 InstitutionAddress: str | None = None,
                 InstitutionalDepartmentName: str | None = None,
                 Manufacturer: str = "Interacoustics",
                 ManufacturersModelName: str = "Eclipse",
                 SoftwareVersions: str | None = None,
                 TaskDescription: str = "Passive experiment, the participants is not required to do anything",
                 Instructions: str = "Be relax and quiet while you hear the sounds",
                 CogAtlasID: str | None = None,
                 CogPOID: str | None = None,
                 DeviceSerialNumber: str | None = None,
                 EEGReference: str = "single electrode placed on FCz",
                 SamplingFrequency: float = 2400,
                 PowerLineFrequency: float = 50,  # number or "n/a"
                 SoftwareFilters: dict | str = "n/a",  # {"Anti-aliasing filter": {"half-amplitude cutoff (Hz)": 500,
                 # "Roll-off": "6dB/Octave"}},  # object of objects or "n/a"
                 CapManufacturer: str = "None",
                 CapManufacturersModelName: str = "None",
                 EEGChannelCount: int = 1,
                 ECGChannelCount: int = 0,
                 EMGChannelCount: int = 0,
                 EOGChannelCount: int = 0,
                 MiscChannelCount: int = 0,
                 TriggerChannelCount: int = 1,
                 RecordingDuration: float | None = None,
                 RecordingType: str = "continuous",
                 EpochLength: float | None = None,
                 EEGGround: str = "placed on participant's cheek",
                 HeadCircumference: float | None = None,
                 EEGPlacementScheme: str = "10-20 system",
                 HardwareFilters: dict | str = "n/a",  # {"ADC's decimation filter (hardware bandwidth limit)":{": str -
                 # 3dB cutoff point (Hz)":480, ": str F ilter order sinc response":5}},  # object of objects or "n/a"
                 SubjectArtefactDescription: str | None = None,
                 ):
        self.InstitutionAddress = InstitutionAddress
        self.InstitutionalDepartmentName = InstitutionalDepartmentName
        self.Manufacturer = Manufacturer
        self.ManufacturersModelName = ManufacturersModelName
        self.SoftwareVersions = SoftwareVersions
        self.TaskDescription = TaskDescription
        self.Instructions = Instructions
        self.CogAtlasID = CogAtlasID
        self.CogPOID = CogPOID
        self.DeviceSerialNumber = DeviceSerialNumber
        self.EEGReference = EEGReference
        self.SamplingFrequency = SamplingFrequency
        self.PowerLineFrequency = PowerLineFrequency
        self.SoftareFilters = SoftwareFilters
        self.CapManufacturer = CapManufacturer
        self.CapManufacturersModelName = CapManufacturersModelName
        self.EEGChannelCount = EEGChannelCount
        self.ECGChannelCount = ECGChannelCount
        self.EMGChannelCount = EMGChannelCount
        self.EOGChannelCount = EOGChannelCount
        self.MiscChannelCount = MiscChannelCount
        self.TriggerChannelCount = TriggerChannelCount
        self.RecordingDuration = RecordingDuration
        self.RecordingType = RecordingType
        self.EpochLength = EpochLength
        self.EEGGround = EEGGround
        self.HeadCircumference = HeadCircumference
        self.EEGPlacementScheme = EEGPlacementScheme
        self.HardwareFilters = HardwareFilters
        self.SubjectArtefactDescription = SubjectArtefactDescription

    def to_json_file(self,
                     file_path: str | None = None):
        json_buffer = json.dumps(self.__dict__, indent=2)
        with open(file_path,
                  mode="w+",
                  encoding="utf-8") as _f:
            _f.write(json_buffer)
        return json_buffer


class BDFParameters(object):
    def __init__(self,
                 data: u.Quantity,
                 channel_labels: List[str] = ['LeftMastoid', 'RightMastoid'],
                 transducer_label: str = 'passive electrode',
                 pre_filtering_label: str = 'HP:3; LP:410',
                 fs: type(u.quantity) | None = None,
                 events: Events | None = None,
                 triggers_code_table: pd.DataFrame | None = None,
                 recording_id: str = '',  # 80 bytes
                 start_date: str = 'dd.mm.yy',
                 start_time: str = 'hh.mm.ss',
                 physical_minimum_quantity: type(u.quantity) | None = None,
                 physical_maximum_quantity: type(u.quantity) | None = None):
        self.data = data
        self.channel_labels = channel_labels
        self.transducer_label = transducer_label
        self.pre_filtering_label = pre_filtering_label
        self.fs = fs
        self.events = events
        self.triggers_code_table = triggers_code_table
        self.recording_id = recording_id
        self.start_date = start_date
        self.start_time = start_time
        self.physical_minimum_quantity = physical_minimum_quantity
        self.physical_maximum_quantity = physical_maximum_quantity


def events_to_bids(events: Events,
                   triggers_code_table: pd.DataFrame,
                   exclude_code: List[float] | None = None):
    """
        Convert events to BIDS compatible events pandas dataframe
        :param events: Events class containing all the events
        :param triggers_code_table: pandas dataframe. It must contain the trigger_code column and any additional columns
        to be included in the output data_frame
        :param exclude_code: list of codes to be ignored
        :return: pandas dataframe ensuring onset and duration columns as required by BIDS standard.
    """
    events_pd = events.events_to_pandas(exclude_code=exclude_code)
    events_pd = events_pd.rename(columns={"time_pos": "onset",
                                          "dur": "duration",
                                          "code": "trigger_code"
                                          })
    events_pd = events_pd.merge(triggers_code_table, on='trigger_code')
    return events_pd


class BIDSEventAnnotation(object):
    def __init__(self,
                 variable_name: str | None = None,
                 LongName: str | None = None,
                 Description: str | None = None,
                 Units: str | None = None,
                 Levels: dict | None = None,
                 HED: {str} = None):
        self.variable_name = variable_name
        self.LongName = LongName
        self.Description = Description
        self.Units = Units
        self.Levels = Levels
        self.HED = HED

    def get_name_and_values(self):
        name = self.variable_name
        values = {'LongName': self.LongName,
                  'Description': self.Description,
                  'Units': self.Units,
                  'Levels': self.Levels,
                  'HED': self.HED,
                  }
        return name, values


class GeneratedBy(object):
    def __init__(self,
                 Name: str | None = None,  # Name of the pipeline or process that generated the outputs. Use "Manual" to
                 # indicate the derivatives were generated by hand, or adjusted manually after an initial run of an
                 # automated pipeline..
                 Version: str | None = None,  # Version of the pipeline
                 Description: str | None = None,  # Plain-text description of the pipeline or process that generated the
                 # outputs. RECOMMENDED if Name is "Manual".
                 CodeURL: str | None = None,  # URL where the code used to generate the dataset may be found.
                 Container: List[dict] | None = None,  # Used to specify the location and relevant attributes of
                 # software
                 # container image used to produce the dataset. Valid keys in this object include Type, Tag and URI
                 # with string values.
                 ):
        self.Name = Name
        self.Version = Version,
        self.Description = Description
        self.CodeURL = CodeURL
        self.Container = Container


class BIDSDataSetDescription(object):
    def __init__(self,
                 Name: str = "",  # Name of the dataset.
                 BIDSVersion: str = '1.10.0',  # The version of the BIDS standard that was used.
                 HEDVersion: str | None = None,  # If HED tags are used: The version of the HED schema used to validate
                 # HED tags for study. May include a single schema or a base schema and one or more library schema.
                 DatasetLinks: {str} = None,  # DatasetLinks Used to map a given <dataset-name> from a BIDS URI of the
                 # form bids:<dataset-name>:path/within/dataset to a local or remote location. The <dataset-name>: ""
                 # (an empty string) is a reserved keyword that MUST NOT be a key in DatasetLinks (example:
                 # bids::path/within/dataset).
                 DatasetType: str = 'raw',  # The interpretation of the dataset. For backwards compatibility,
                 # the default value is "raw".
                 License: str = "",  # The license for the dataset. The use of license name abbreviations is
                 # RECOMMENDED for specifying a license (see Licenses). The corresponding full license text MAY be
                 # specified in an additional LICENSE file.
                 Authors: List[str] = [""],   # 'List of individuals who contributed to the creation/curation of
                 # the dataset.'
                 HowToAcknowledge: str = "",  # Text containing instructions on how researchers using this
                 # dataset should acknowledge the original authors. This field can also be used to define a publication
                 # that should be cited in publications that use the dataset.
                 Funding: List[str] = [""],  # List of sources of funding (grant numbers).
                 EthicsApprovals: List[str] = [""],  # List of ethics committee approvals of the research protocols
                 # and/or protocol identifiers.
                 ReferencesAndLinks: List[str] = [""],  # List of references to publications that contain information
                 # on the dataset. A reference may be textual or a URI.
                 DatasetDOI: str = "",  # The Digital Object Identifier of the dataset (not the corresponding paper).
                 # DOIs SHOULD be expressed as a valid URI; bare DOIs such as 10.0.2.3/dfjj.10 are DEPRECATED.
                 GeneratedBy: List[GeneratedBy] = [{}],  # Used to specify provenance of the dataset.
                 SourceDatasets: List[str] = [""],  # Used to specify the locations and relevant attributes of all
                 # source datasets. Valid keys in each object include "URL", "DOI" (see URI), and "Version" with
                 # string values.
                 ):
        self.Name = Name
        self.BIDSVersion = BIDSVersion
        self.HEDVersion = HEDVersion
        self.DatasetLinks = DatasetLinks
        self.DatasetType = DatasetType
        self.License = License
        self.Authors = Authors
        self.HowToAcknowledge = HowToAcknowledge
        self.Funding = Funding
        self.EthicsApprovals = EthicsApprovals
        self.ReferencesAndLinks = ReferencesAndLinks
        self.DatasetDOI = DatasetDOI
        self.GeneratedBy = GeneratedBy
        self.SourceDatasets = SourceDatasets
    def to_json_file(self,
                     file_path: str | None = None):
        json_buffer = json.dumps(self.__dict__, indent=2)
        with open(file_path,
                  mode="w+",
                  encoding="utf-8") as _f:
            _f.write(json_buffer)
        return json_buffer


class BIDSParticipant(object):
    def __init__(self,
                 participant_id: str | None = None,  # A participant identifier of the form sub-<label>, matching a
                 # participant entity found in the dataset. There MUST be exactly one row for each participant.
                 # Values in participant_id MUST be unique. This column must appear first in the file.
                 species: (str | float) = 'homo sapiens',  # The species column SHOULD be a binomial species name from
                 # the NCBI Taxonomy (for example, homo sapiens, mus musculus, rattus norvegicus).
                 # For backwards compatibility, if species is absent, the participant is assumed to be homo sapiens.
                 age: (float | int) = None,  # Numeric value in years (float or integer value). It is RECOMMENDED to tag
                 # participant ages that are 89 or higher as 89+, for privacy purposes.
                 sex: str | None = None,  # String value indicating phenotypical sex, one of "male", "female", "other".
                 # For "male", use one of these values: male, m, M, MALE, Male.
                 # For "female", use one of these values: female, f, F, FEMALE, Female.
                 # For "other", use one of these values: other, o, O, OTHER, Other.
                 # This column may appear anywhere in the file.
                 handedness: str | None = None,  # String value indicating one of "left", "right", "ambidextrous".
                 # For "left", use one of these values: left, l, L, LEFT, Left.
                 # For "right", use one of these values: right, r, R, RIGHT, Right.
                 # For "ambidextrous", use one of these values: ambidextrous, a, A, AMBIDEXTROUS, Ambidextrous.
                 # This column may appear anywhere in the file.
                 strain: (str | float) = None,  # For species different from homo sapiens, string value indicating the
                 # strain of the species, for example: C57BL/6J.
                 strain_rrid: str | None = None,  # For species different from homo sapiens, research resource
                 # identifier (RRID) of the strain of the species, for example: RRID:IMSR_JAX:000664.
                 # This column may appear anywhere in the file.
                 additional_columns: dict = None  # dictionary with additional columns to include
                 ):
        self.participant_id = participant_id
        self.species = species
        self.age = age
        self.sex = sex
        self.handedness = handedness
        self.strain = strain
        self.strain_rrid = strain_rrid
        if additional_columns is not None:
            for attr, value in additional_columns.items():
                setattr(self, attr, value)

    def save_as_tvs(self, output_path: str | None = None):
        all_participants_df = pd.DataFrame()
        if os.path.exists(output_path):
            all_participants_df = pd.read_csv(filepath_or_buffer=output_path,
                                              sep='\t',
                                              dtype=str)
        current_participant_df = pd.DataFrame([self.__dict__])
        if ((all_participants_df.shape[0] > 0) and
                all_participants_df['participant_id'].isin([self.participant_id]).any()):
            return

        all_participants_df = pd.concat([all_participants_df, current_participant_df])
        all_participants_df.to_csv(
            path_or_buf=output_path,
            sep='\t',
            index=False)


class BIDSParticipantAnnotation(object):
    def __init__(self,
                 variable_name: str | None = None,
                 Description: str | None = None,
                 Units: str | None = None,
                 Levels: dict | None = None,
                 HED: {str} = None):
        self.variable_name = variable_name
        self.Description = Description
        self.Units = Units
        self.Levels = Levels

    def get_name_and_values(self):
        name = self.variable_name
        values = {'Description': self.Description,
                  'Units': self.Units,
                  'Levels': self.Levels
                  }
        return name, values


class BIDSEventDescriptionItem(list):
    def append(self, item):
        # optional processing here
        assert isinstance(item, BIDSEventAnnotation)
        super(BIDSEventDescriptionItem, self).append(item)

    def save_to_json(self, output_path: str | None = None):
        _dict = {}
        for _e in self:
            _name, _value = _e.get_name_and_values()
            _dict[_name] = _value
        json_buffer = json.dumps(_dict, indent=2)
        with open(output_path,
                  mode="w+",
                  encoding="utf-8") as _f:
            _f.write(json_buffer)
        return json_buffer


class BIDSParticipantDescriptionItem(list):
    def append(self, item):
        # optional processing here
        assert isinstance(item, BIDSParticipantAnnotation)
        super(BIDSParticipantDescriptionItem, self).append(item)

    def save_to_json(self, output_path: str | None = None):
        _dict = {}
        for _e in self:
            _name, _value = _e.get_name_and_values()
            _dict[_name] = _value
        json_buffer = json.dumps(_dict, indent=2)
        with open(output_path,
                  mode="w+",
                  encoding="utf-8") as _f:
            _f.write(json_buffer)
        return json_buffer


def check_allowed_patterh(str, pattern):
    # _matching the strings
    valid = False
    if re.search(pattern, str):
        valid = True
    return valid


class BIDSConverter(object):
    """
    This class implement several functionality to facilitate BIDS format exportation.
    https://bids-specification.readthedocs.io/en/stable/modality-specific-files/electroencephalography.html
    """
    def __init__(self,
                 output_path: Path | None = None,
                 current_eeg_file: Path | None = None,
                 bdf_parameters: BDFParameters | None = None,
                 dataset_description: BIDSDataSetDescription | None = None,
                 participant: BIDSParticipant = BIDSParticipant(),
                 eeg_json: BIDS_EEG_JSON | None = None,
                 event_column_descriptions: BIDSEventDescriptionItem = BIDSEventDescriptionItem(),
                 participant_column_descriptions: BIDSParticipantDescriptionItem = BIDSParticipantDescriptionItem(),
                 readme: str = """This is a great study with cool experiments and
                                                   excellent data"""):
        """
        Initializes the path where BIDS format will be saved
        :param output_path: path to save data using BIDS format
        :param current_eeg_file: path with current EEG data file
        :param bdf_parameters: BDFParameters class used to generate BDF files. If BDF files exists, this should not
        be used.
        :param dataset_description: BIDSDataSetDescription class with description following the BIDS standard
        :param session_id: the session ID of the current EEG file as defined in the BIDS standard
        :param task_id: : the task ID of the current EEG file
        :param participant: BIDSParticipant class with participant information as defined in the BIDS standard
        :param eeg_json: BIDS_EEG_JSON class with EEG_json information of current EEG file as defined in BIDS standard
        :param event_column_descriptions: BIDSEventDescriptionItem class defnining events as required by the BIDS
        standard
        :param readme: string with the description of the data set.
        """
        self.output_path = output_path
        self.current_eeg_file = current_eeg_file
        self.bdf_parameters = bdf_parameters
        self.dataset_description = dataset_description
        self.eeg_json = eeg_json
        self.event_column_descriptions = event_column_descriptions
        self.participant_column_descriptions = participant_column_descriptions
        self.readme = readme
        self._subject_id = None
        self._session_id = None
        self._task_id = None
        self._run_id = None

    def get_subject_id(self):
        return self._subject_id

    def set_subject_id(self, value):
        pattern = re.compile('^sub-[0-9a-zA-Z]+$')
        assert check_allowed_patterh(value, pattern), 'the label is not in compliance with BIDS (sub-[0-9a-zA-Z])'
        self._subject_id = value
    subject_id = property(get_subject_id, set_subject_id)

    def get_session_id(self):
        return self._session_id

    def set_session_id(self, value):
        pattern = re.compile('^ses-[0-9a-zA-Z]+$')
        assert check_allowed_patterh(value, pattern), 'the label is not in compliance with BIDS (ses-[0-9a-zA-Z])'
        self._session_id = value
    session_id = property(get_session_id, set_session_id)

    def get_task_id(self):
        return self._task_id

    def set_task_id(self, value):
        pattern = re.compile('^task-[0-9a-zA-Z]+$')
        assert check_allowed_patterh(value, pattern), 'the label is not in compliance with BIDS (task-[0-9a-zA-Z])'
        self._task_id = value
    task_id = property(get_task_id, set_task_id)

    def get_run_id(self):
        return self._run_id

    def set_run_id(self, value):
        pattern = re.compile('^run-[0-9]+$')
        assert check_allowed_patterh(value, pattern), 'the label is not in compliance with BIDS (run-[0-9])'
        self._run_id = value
    run_id = property(get_run_id, set_run_id)

    def _get_current_path(self):
        out = self.output_path.joinpath(
            self.subject_id).joinpath(
            self.session_id
        ).joinpath('eeg')
        return out

    def _get_current_basename(self):
        out = (self.subject_id +
               '_' +
               self.session_id +
               '_' +
               self.task_id +
               '_' +
               self.run_id +
               '_'
               )
        return out

    def save_eeg_data_as_bdf(self):
        output_file_name = self._get_current_path().joinpath(self._get_current_basename() + 'eeg.bdf')
        data_to_bdf(output_file_name=output_file_name,
                    data=self.bdf_parameters.data,
                    channel_labels=self.bdf_parameters.channel_labels,
                    transducer_label=self.bdf_parameters.transducer_label,
                    pre_filtering_label=self.bdf_parameters.pre_filtering_label,
                    fs=self.bdf_parameters.fs,
                    events=self.bdf_parameters.events,
                    subject_id=self.subject_id,
                    recording_id=self.bdf_parameters.recording_id,
                    start_date=self.bdf_parameters.start_date,
                    start_time=self.bdf_parameters.start_time,
                    physical_minimum_quantity=self.bdf_parameters.physical_minimum_quantity,
                    physical_maximum_quantity=self.bdf_parameters.physical_maximum_quantity
                    )
        self.current_eeg_file = output_file_name

    def save_eeg_events_data(self,
                             triggers_code_table: pd.DataFrame | None = None,
                             exclude_event_code: float = 0):
        # extract EEG data ####
        output_file_name = self._get_current_path().joinpath(self._get_current_basename() + 'eeg.bdf')
        if not os.path.exists(str(output_file_name)):
            shutil.copy(self.current_eeg_file, output_file_name)

        reader = ReadInputData(file_path=output_file_name)
        reader.run()

        events_tsv = events_to_bids(events=reader.output_node.events,
                                    exclude_code=exclude_event_code,
                                    triggers_code_table=self.bdf_parameters.triggers_code_table)
        events_tsv.to_csv(
            path_or_buf=self._get_current_path().joinpath(self._get_current_basename() + 'events.tsv'),
            sep='\t',
            index=False)

        self.event_column_descriptions.save_to_json(
            output_path=self._get_current_path().joinpath(self._get_current_basename() + 'events.json'))

        self.bdf_parameters.triggers_code_table.to_csv(
            path_or_buf=self._get_current_path().joinpath(self._get_current_basename() + 'triggerCodes.tsv'),
            sep='\t',
            index=False)

        self.eeg_json.SamplingFrequency = reader.output_node.fs.to('Hz').value,
        self.eeg_json.EEGChannelCount = reader.output_node.data.shape[1],
        self.eeg_json.RecordingDuration = reader.output_node.data.shape[0] / reader.output_node.fs.to('Hz').value,
        self.eeg_json.to_json_file(
            file_path=self._get_current_path().joinpath(self._get_current_basename() + 'eeg.json'))

    def readme_to_md(self, file_path: str | None = None):
        with open(file_path, "w+") as _file:
            _file.write("Dataset description \n")
            _file.write("===================== \n")
            _file.write(self.readme)

    def save_current_iteration(self):
        os.makedirs(self._get_current_path(), exist_ok=True)
        if self.bdf_parameters is not None:
            self.save_eeg_data_as_bdf()
        self.save_eeg_events_data(exclude_event_code=0)
        self.participant.save_as_tvs(self.output_path.joinpath('participants.tsv'))
        self.participant_column_descriptions.save_to_json(output_path=self.output_path.joinpath('participants.json'))
        self.dataset_description.to_json_file(self.output_path.joinpath('dataset_description.json'))
        self.readme_to_md(self.output_path.joinpath('README.md'))
