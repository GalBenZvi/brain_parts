from pathlib import Path

import pandas as pd
from matplotlib.style import available
from sklearn.metrics import pair_confusion_matrix

from connecticity.managers.analyses.analysis import AnalysisResults
from connecticity.managers.analyses.utils.data_grabber import (
    DataGrabber,
)
from connecticity.managers.analyses.utils.parcellations import (
    PARCELLATIONS,
)
from connecticity.managers.analyses.utils.templates import (
    generate_atlas_file_name,
)


class DmriprepResults(AnalysisResults):
    # Queries
    NATIVE_PARCELLATION_QUERY = ["Done", "Missing"]

    def __init__(
        self,
        base_dir: Path,
        longitudinal: bool = True,
        available_parcellations: dict = PARCELLATIONS,
    ) -> None:
        super().__init__(base_dir)
        self.longitudinal = longitudinal
        self.data_grabber = DataGrabber(base_dir, analysis_type="dmriprep")
        self.available_parcellations = available_parcellations

    def register_parcellation_to_anatomical(
        self,
        parcellation_scheme: str,
        parcellation_file: Path,
        participant_label: str,
        sessions: list,
        crop_to_gm: True,
    ):
        (
            references,
            directory,
            prefix,
        ) = self.data_grabber.locate_anatomical_references(participant_label, sessions)
        out_file = generate_atlas_file_name(
            references.get("anatomical_reference"),
            parcellation_scheme,
            space="anat",
        )
        out_masked = generate_atlas_file_name(
            references.get("anatomical_reference"),
            parcellation_scheme,
            space="anat",
            desc="GM",
        )

    # def register_single_subject_parcellation(self,parcellation_file:Path,subject:str):

    def register_parcellation_scheme(
        self, parcellation_scheme: str, crop_to_gm: bool = True
    ):
        """
        Register a parcellation scheme to subjects' anatomical space

        Parameters
        ----------
        parcellation_scheme : str
            A string representing existing key within *self.parcellations*.
        crop_to_gm : bool, optional
            Whether to crop the resulting register parcellation atlas to gray matter, by default True
        """
        parcellation = self.get_parcellation(parcellation_scheme)
        parcellation_file = parcellation.get("path")
        dataset_query = pd.DataFrame(columns=self.NATIVE_PARCELLATION_QUERY)
        # for subject,sessions in self.subjects.items():
        #     for session in sessions:

        return

    def to_dataframe(
        self,
        parcellation_scheme: str,
        cropped_to_gm: bool = True,
        force: bool = False,
        np_operation: str = "nanmean",
    ) -> pd.DataFrame:
        """Parcellates tensor-derived metrics according to *parcellation_scheme*

        Parameters
        ----------
        parcellation_scheme : str
            A string representing existing key within *self.parcellations*.

        Returns
        -------
        pd.DataFrame
            A dictionary with representing subjects, and values containing paths to subjects-space parcellations.
        """
        parcels = self.parcellations.get(parcellation_scheme).get("parcels")
        parcellations = self.register_parcellation_scheme(
            analysis_type, parcellation_scheme, cropped_to_gm
        )
        multi_column = pd.MultiIndex.from_product([parcels.index, self.TENSOR_METRICS])
        if analysis_type == "qsiprep":
            estimate_tensors(parcellations, self.qsiprep_dir, multi_column)
        return parcellate_tensors(
            self.locate_outputs(analysis_type),
            multi_column,
            parcellations,
            parcels,
            parcellation_scheme,
            cropped_to_gm,
            force,
            np_operation,
        )
