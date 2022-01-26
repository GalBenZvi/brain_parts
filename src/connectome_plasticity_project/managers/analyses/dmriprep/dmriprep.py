from pathlib import Path

import pandas as pd

from connectome_plasticity_project.managers.analyses.analysis import (
    AnalysisResults,
)


class DmriprepResults(AnalysisResults):
    def __init__(self, base_dir: Path, longitudinal: bool = True) -> None:
        super().__init__(base_dir)
        self.longitudinal = longitudinal

    def locate_anatomical_references(
        self, participant_label: str, sessions: list
    ):
        """
        Locates subjects' preprocessed anatomical references

        Parameters
        ----------
        output_dir : Path
            An output (derivatives) directory of *dmriprep*
        """
        anat_dir = (
            self.base_dir / participant_label / "anat"
            if len(sessions) > 1
            else self.base_dir / participant_label / sessions[0] / "anat"
        )
        reference = transformation = gm_mask = None
        valid = True
        if not anat_dir.exists():
            try:
                anat_dir = [d for d in subject_dir.glob("ses-*/anat")][0]
            except IndexError:
                valid = False
        try:
            reference = [
                f
                for f in anat_dir.glob(
                    self.ANATOMICAL_REFERENCE.format(
                        participant_label=participant_label
                    )
                )
            ][0]
            transformation = [
                f
                for f in anat_dir.glob(
                    self.MNI_TO_NATIVE_TRANSFORMATION.format(
                        participant_label=participant_label
                    )
                )
            ][0]
            gm_mask = [
                f
                for f in anat_dir.glob(
                    self.GM_PROBABILITY.format(
                        participant_label=participant_label
                    )
                )
            ][0]
        except IndexError:
            valid = False
        return reference, transformation, gm_mask, valid

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
        multi_column = pd.MultiIndex.from_product(
            [parcels.index, self.TENSOR_METRICS]
        )
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
