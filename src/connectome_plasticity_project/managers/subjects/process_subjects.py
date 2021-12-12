import logging
import logging.config
from pathlib import Path

import pandas as pd

from connectome_plasticity_project.managers.subjects.messages import (
    LOGGER_CONFIG,
)
from connectome_plasticity_project.managers.subjects.messages import (
    SUMMARY_MESSAGE,
)
from connectome_plasticity_project.managers.subjects.utils import (
    REPLACEMENT_COLUMNS,
)
from connectome_plasticity_project.managers.subjects.utils import transform_row


class SubjectsManager:
    #: Pre-defined files' names
    MRI_TABLE_NAME = "MRI_table.xlsx"
    DATABASE_IDS_NAME = "subjects.csv"

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
    DEFAULT_DESTINATION = "processed"
    LOGGER_FILE = "query.log"

    def __init__(self, base_dir: Path, destination: Path = None) -> None:
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
        logging.basicConfig(
            filename=self.destination / self.LOGGER_FILE, **LOGGER_CONFIG
        )

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
        return pd.read_csv(database_ids, converters={"ID Number": str})

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
            notes, serial, scan = [
                row[col] for col in ["notes", "Serial", "SCAN FILE"]
            ]
            for key, value in self.GROUP_IDENTIFIERS.items():
                if ((key in str(notes)) | (key in str(serial))) & pd.notna(
                    scan
                ):
                    for raw_label, label in self.CONDITION_IDENTIFIERS.items():
                        if (raw_label in str(notes)) | (
                            raw_label in str(serial)
                        ):
                            condition = label
                            break
                        else:
                            condition = "learner"
                    transformed_row = transform_row(row, REPLACEMENT_COLUMNS)
                    transformed_row["group"] = value
                    transformed_row["condition"] = condition
                    relevant_subjects = relevant_subjects.append(
                        transformed_row
                    )
        return relevant_subjects

    def query_database_ids(
        self, relevant_subjects: pd.DataFrame
    ) -> pd.DataFrame:
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
                combined_df = combined_df.append(
                    pd.concat([row, self.databse_ids.loc[subj_id]]),
                    ignore_index=True,
                )
            else:
                missing_df = missing_df.append(row)
        return combined_df, missing_df

    def query_subjects(self, return_data: bool = False):
        relevant_subjects = self.query_mri_table()
        valid, missing = self.query_database_ids(relevant_subjects)
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
