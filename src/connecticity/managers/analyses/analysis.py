from pathlib import Path

import pandas as pd

from connecticity.managers.analyses.messages import PARCELLATION_ERROR
from connecticity.managers.parcellation.utils import PARCELLATIONS


class AnalysisResults:
    """
    A "top-level" object to manage an analysis-specific derivatives' directory.
    """

    #: Suffixes and prefixes
    SUBJECT_PREFIX = "sub"
    SESSION_PREFIX = "ses"

    #: Files' templates
    ANATOMICAL_REFERENCE = "sub-{participant_label}*_desc-preproc_T1w.nii.gz"
    MNI_TO_NATIVE_TRANSFORMATION = "sub-{participant_label}*from-MNI*_to-T1w*_xfm.h5"
    GM_PROBABILITY = "sub-{participant_label}*_label-GM_probseg.nii.gz"

    #: Masking threshold
    PROBSEG_THRESHOLD = 0.01

    #: Parcellation transform and masking default arguments
    TRANSFORM_KWARGS = {
        "interpolation": "NearestNeighbor",
    }
    MASKER_KWARGS = {"output_datatype": "int"}

    def __init__(
        self, base_dir: Path, available_parcellations: dict = PARCELLATIONS
    ) -> None:
        self.base_dir = Path(base_dir)
        self.available_parcellations = available_parcellations

    def get_parcellation(self, parcellation_scheme: str) -> dict:
        """
        Locates a parcellation scheme in *self.available_parcellations* and return its corresponding information

        Parameters
        ----------
        parcellation_scheme : str
            A string representing a parcellation scheme

        Returns
        -------
        dict
            A dictionary containing available information and files associated with *parcellation_scheme*
        """
        parcellation = self.available_parcellations.get(parcellation_scheme)
        if not parcellation:
            raise ValueError(
                PARCELLATION_ERROR.format(
                    parcellation_scheme=parcellation_scheme,
                    available_parcellations=", ".join(self.PARCELLATIONS.keys()),
                )
            )
        return parcellation

    def to_dataframe(self, parcellation_scheme: str) -> pd.DataFrame:
        """
        Parse available results to atlas stated as *parcellation_scheme*

        Parameters
        ----------
        parcellation_scheme : str
            A string representing an available parcellation atlas.

        Returns
        -------
        pd.DataFrame
            A Dataframe that hold parsed information derived from the analysis' results.

        Raises
        ------
        NotImplementedError
            In case *to_dataframe* method was not implemented for specific analysis.
        """
        raise NotImplementedError

    def register_parcellation_scheme(
        self,
        parcellation_scheme: str,
    ):
        """
        Register a parcellation scheme to subjects' space

        Parameters
        ----------
        parcellation_scheme : str
            A string representing an available parcellation atlas.

        Raises
        ------
        NotImplementedError
            In case *register_parcellation_scheme* method was not implemented for specific analysis.
        """
        raise NotImplementedError

    def query_analysis_subjects(
        self, subject_pattern: str = "sub-*", session_pattern: str = "ses-*"
    ) -> dict:
        """
        Query *self.base_dir* for available subjects according to *pattern*

        Parameters
        ----------
        pattern : str, optional
            Pattern of subjects' derivatives' directory, by default "sub-*"

        Returns
        -------
        dict
            A dictionary with keys of subjects and values of session\s.
        """
        subjects = {
            subj.name.replace("sub-", ""): [
                ses.name.replace("ses-", "")
                for ses in sorted(self.base_dir.glob(f"{subj.name}/{session_pattern}"))
            ]
            for subj in sorted(self.base_dir.glob(subject_pattern))
            if subj.is_dir()
        }
        return subjects

    def locate_anatomical_reference(
        self,
        participant_label: str,
        anatomical_derivatives_pattern: str = "anat/",
    ) -> Path:
        """
        Locates anatomical reference in a BIDS-compatible derivatives directory

        Parameters
        ----------
        participant_label : str
            Participant's identifier. Can be full (sub-*) or partial (without the "sub-" prefix)
        anatomical_derivatives_pattern : str, optional
            Pattern of anatomical sub-directory within subject's directory, by default "anat/"

        Returns
        -------
        Path
            Path to subject's anatomical reference
        """
        participant_label = participant_label.replace(f"{self.SUBJECT_PREFIX}-", "")
        anatomical_directory = (
            self.base_dir
            / f"{self.SUBJECT_PREFIX}-{participant_label}"
            / anatomical_derivatives_pattern
        )
        pattern = self.ANATOMICAL_REFERENCE.format(participant_label=participant_label)
        reference = [f for f in anatomical_directory.glob(pattern)]
        try:
            return reference[0]
        except IndexError:
            print(
                f"Could not locate anatomical reference for subject {participant_label}."
            )

    @property
    def subjects(self) -> dict:
        """
        All available subjects (and their related sessions) available for this analysis.

        Returns
        -------
        dict
            A dictionary with keys of subjects and values of session\s.
        """
        return self.query_analysis_subjects()
