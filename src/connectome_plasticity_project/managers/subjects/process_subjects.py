import datetime
import json
import logging
import logging.config
import shutil
from pathlib import Path

import pandas as pd
from nipype.interfaces import fsl

from connectome_plasticity_project.managers.subjects.messages import (
    LOGGER_CONFIG,
)
from connectome_plasticity_project.managers.subjects.messages import (
    SUMMARY_MESSAGE,
)
from connectome_plasticity_project.managers.subjects.utils import (
    REPLACEMENT_COLUMNS,
)
from connectome_plasticity_project.managers.subjects.utils import fix_session
from connectome_plasticity_project.managers.subjects.utils import transform_row


class SubjectsManager:
    #: Pre-defined files' names
    MRI_TABLE_NAME = "raw/MRI_table.xlsx"
    DATABASE_IDS_NAME = "raw/subjects.csv"

    #: TheBase sheet name
    THE_BASE_SHEET = "THE BASE"

    #: Relevant groups' identifiers and corresponding labels
    GROUP_IDENTIFIERS = {
        "ג'יו גיטסו": "bjj",
        "טיפוס": "climbing",
        "AMIR MANO": "music",
    }
    CONDITION_IDENTIFIERS = {
        "ביקורת": "control",
        "מקצועי": "professional",
        "AMIR MANO": "control",
    }

    #: Default destination locations
    DEFAULT_DESTINATION = "subjects/processed"
    LOGGER_FILE = "query_{timestamp}.log"

    def __init__(
        self,
        base_dir: Path,
        destination: Path = None,
        bids_dir: Path = None,
        validate_fieldmaps: bool = True,
        fix_bids: bool = True,
    ) -> None:
        """
        Initiates a SubjectManager object

        Parameters
        ----------
        base_dir : Path
            Path to a directory that contains *MRI_TABLE_NAME* and *DATABASE_IDS_NAME* files.
        """
        self.base_dir = Path(base_dir)
        self.destination = (
            destination or self.base_dir.parent / self.DEFAULT_DESTINATION
        )
        self.bids_dir = Path(bids_dir) if bids_dir else None
        timestamp = datetime.datetime.today().strftime("%Y-%m-%d-%H:%M:%S")
        logging.basicConfig(
            filename=self.destination / self.LOGGER_FILE.format(timestamp=timestamp),
            **LOGGER_CONFIG,
        )
        if validate_fieldmaps and self.bids_dir.exists():
            self.fix_fieldmaps()
        if fix_bids and self.bids_dir.exists():
            self.validate_and_fix_bids()

    def get_mri_table(self) -> pd.DataFrame:
        """
        Locates the MRI table excel file and loads the relevent sheet

        Returns
        -------
        pd.DataFrame
            A Dataframe that holds all participant's data

        Raises
        ------
        FileNotFoundError
            Upon missing file.
        """
        mri_table = self.base_dir / self.MRI_TABLE_NAME
        if not mri_table.exists():
            raise FileNotFoundError(
                f"Unable to file MRI subjects' table at {mri_table}."
            )
        return pd.read_excel(
            mri_table,
            engine="openpyxl",
            sheet_name=self.THE_BASE_SHEET,
            converters={"ID": str},
        )

    def get_database_ids(self) -> pd.DataFrame:
        """
        Locates and reads the table that hold subjects' IDs and corresponding database's.

        Returns
        -------
        pd.DataFrame
            A table that contains subjects' IDs and their database's identifiers.

        Raises
        ------
        FileNotFoundError
            Upon missing file.
        """
        database_ids = self.base_dir / self.DATABASE_IDS_NAME
        if not database_ids.exists():
            raise FileNotFoundError(
                f"Unable to file MRI subjects' table at {database_ids}."
            )
        return pd.read_csv(database_ids, converters={"ID": str})

    def query_mri_table(self) -> pd.DataFrame:
        """
        Locates relevant subjects' (according to *GROUP_IDENTIFIERS*)

        Returns
        -------
        pd.DataFrame
            A dataframe that only hold relevant subjects' information.
        """
        relevant_subjects = pd.DataFrame()
        for _, row in self.mri_table.iterrows():
            notes, serial, scan = [row[col] for col in ["notes", "Serial", "SCAN FILE"]]
            for key, value in self.GROUP_IDENTIFIERS.items():
                if ((key in str(notes)) | (key in str(serial))) & pd.notna(scan):
                    for raw_label, label in self.CONDITION_IDENTIFIERS.items():
                        if (raw_label in str(notes)) | (raw_label in str(serial)):
                            condition = label
                            break
                        else:
                            condition = "learner"
                    transformed_row = transform_row(
                        row,
                        origin="mri_table",
                        replacements=REPLACEMENT_COLUMNS,
                    )
                    transformed_row["group"] = value
                    transformed_row["condition"] = condition
                    relevant_subjects = relevant_subjects.append(transformed_row)
        return relevant_subjects

    def query_database_ids(self, relevant_subjects: pd.DataFrame) -> pd.DataFrame:
        """
        Combines *self.mri_table* and *self.databse_ids* to hold only data for relevant subjects.

        Parameters
        ----------
        relevant_subjects : pd.DataFrame
            A queried *self.mri_table* part that only hold partial information for relevant subjects.

        Returns
        -------
        pd.DataFrame
            A combination of *self.mri_table* and *self.database_ids* for relevant subjects.
        """
        combined_df = pd.DataFrame()
        missing_df = pd.DataFrame()
        for _, row in relevant_subjects.iterrows():
            subj_id = row["id"]
            if subj_id in self.databse_ids.index:
                transformed_row = transform_row(
                    self.databse_ids.loc[subj_id],
                    origin="database",
                    replacements=REPLACEMENT_COLUMNS,
                )
                combined_df = combined_df.append(
                    pd.concat([row, transformed_row]),
                    ignore_index=True,
                )
            else:
                missing_df = missing_df.append(row)
        return combined_df, missing_df

    def query_bids(self, valids_subject: pd.DataFrame):
        """
        Combines available subjects with *self.bids_dir* if given.


        Parameters
        ----------
        valids_subject : pd.DataFrame
            A dataframe of available subjects
        """
        bids_available = [
            sub.name.split("-")[-1] for sub in self.bids_dir.glob("sub-*")
        ]
        for i in valids_subject.index:
            database_id = valids_subject.loc[i, "database_id"]
            if database_id in bids_available:
                valids_subject.loc[i, "rawdata"] = True
            else:
                valids_subject.loc[i, "rawdata"] = False
        return valids_subject

    def validate_and_fix_bids(self):
        """
        Fixes pre-defined issues with the BIDS structure.
        """
        for subj in self.bids_dir.glob("sub-*"):
            for ses in subj.glob("ses-*"):
                fix_session(ses)

    def query_subjects(self, return_data: bool = False):
        """
        A method to query both main tables (MRI table and database's IDs)

        Parameters
        ----------
        return_data : bool, optional
            Whether to return valid and missing dataframes or not, by default False

        Returns
        -------
        pd.DataFrame
            Dataframes with valid and missing participants.
        """
        relevant_subjects = self.query_mri_table()
        valid, missing = self.query_database_ids(relevant_subjects)
        if self.bids_dir:
            valid = self.query_bids(valid)
        msg = SUMMARY_MESSAGE.format(
            num_valid=len(valid.index),
            num_missing=len(missing.index),
            destination=self.destination,
        )
        logging.info(msg)
        print(msg)
        self.destination.mkdir(exist_ok=True, parents=True)
        for df, file_name in zip([valid, missing], ["valid", "missing"]):
            df.to_csv(self.destination / f"{file_name}.csv")
        if return_data:
            return valid, missing

    def register_fmap_between_sessions(
        self,
        fmap: Path,
        reference: Path,
        origin_sessions: str,
        target_session: str,
    ):
        """
        Perform linear registratio between different sessions of the same subjects in order to be able to use the "good" fieldmaps

        Parameters
        ----------
        fmap : Path
            Path to an opposite-directed DWI series
        reference : Path
            Path to a reference DWI series
        origin_sessions : str
            *fmap*'s original session ("good" session)
        target_session : str
            A string representing the session that is missing a fieldmap
        """
        out_file = Path(str(fmap).replace(origin_sessions, target_session))
        if not out_file.exists():
            flt = fsl.FLIRT()
            flt.inputs.in_file = fmap
            flt.inputs.reference = reference
            flt.inputs.out_file = out_file
            flt.inputs.cost = "mutualinfo"
            flt.run()

    def update_json(self, fmap: Path, origin_session: str, target_session: Path):
        """
        Copies the json related to the fieldmap and edits it according to BIDS specifications.

        Parameters
        ----------
        fmap : Path
            Path to opposite-directed DWI series
        target_session : Path
            A string representing the session that is missing a fieldmap
        """
        target_dwi = [str(d) for d in target_session.glob("dwi/*_dwi.nii*")]
        out_file = Path(str(fmap).replace(origin_session, target_session.name))
        if out_file.exists():
            return
        shutil.copy(fmap, out_file)
        with open(out_file, "r+") as f:
            data = json.load(f)
            data["IntendedFor"] = target_dwi
            f.seek(0)
            json.dump(data, f, indent=4)
            f.truncate()

    def use_other_fieldmap(self, session: Path):
        """
        In case there's only a single (out of several) session with valid fieldmap, use it for all sessions.

        Parameters
        ----------
        session : Path
            Path to a session that is missing a valid fieldmap.
        """
        try:
            good_session = [
                s for s in session.parent.glob("ses-*") if session.name not in s.name
            ][0]
        except IndexError:
            logging.warning(
                f"No available session with valid fieldmap found for {session.parent.name}."
            )
            return
        reference = [r for r in session.glob("dwi/*_dwi.nii.gz")][0]
        good_fmaps = [f for f in good_session.glob("fmap/*acq-dwi*")]
        for fmap in good_fmaps:
            print(fmap)
            if fmap.name.endswith(".nii.gz"):
                self.register_fmap_between_sessions(
                    fmap, reference, good_session.name, session.name
                )
            elif fmap.name.endswith(".json"):
                self.update_json(fmap, good_session.name, session)

    def fix_fieldmaps(self):
        """
        Fixes an issue with the DWI fieldmap that occured during November/December 2020.
        """
        for subj in self.bids_dir.glob("sub-*"):
            sessions = [s for s in subj.glob("ses-*")]
            if len(sessions) < 2:
                continue
            for ses in sessions:
                dwi_fmap = [f for f in ses.glob("fmap/*acq-dwi*.nii.gz")]
                if not dwi_fmap:
                    logging.info(
                        f"Using single-session's fieldmap for all available ones for {subj.name}"
                    )
                    logging.info(
                        f"Original valid fieldmap was available through {ses.name}"
                    )
                    self.use_other_fieldmap(ses)

    @property
    def mri_table(self) -> pd.DataFrame:
        """
        Loads the MRI table.

        Returns
        -------
        pd.DataFrame
            A Dataframe with all subjects' MRI-related data.
        """
        return self.get_mri_table()

    @property
    def databse_ids(self) -> pd.DataFrame:
        """
        Loads the database's IDs table.

        Returns
        -------
        pd.DataFrame
            A dataframe with subjects' database-related identifiers
        """
        return self.get_database_ids().set_index("ID Number")
