from pathlib import Path
from typing import Pattern


class Analysis:
    """
    A "top-level" object to manage an analysis-specific derivatives' directory.
    """

    #: Suffixes and prefixes
    SUBJECT_PREFIX = "sub"
    #: Files' templates
    ANATOMICAL_REFERENCE = "sub-{participant_label}*_desc-preproc_T1w.nii.gz"
    MNI_TO_NATIVE_TRANSFORMATION = (
        "sub-{participant_label}*from-MNI*_to-T1w*_xfm.h5"
    )
    GM_PROBABILITY = "sub-{participant_label}*_label-GM_probseg.nii.gz"

    def __init__(self, base_dir: Path) -> None:
        self.base_dir = Path(base_dir)

    def query_analysis_subjects(self, pattern: str = "sub-*") -> dict:
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
            subj.name: [
                ses.name
                for ses in sorted(self.base_dir.glob(f"{subj.name}/ses-*"))
            ]
            for subj in sorted(self.base_dir.glob(pattern))
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
        participant_label = participant_label.replace(
            f"{self.SUBJECT_PREFIX}-", ""
        )
        anatomical_directory = (
            self.base_dir
            / f"{self.SUBJECT_PREFIX}-{participant_label}"
            / anatomical_derivatives_pattern
        )
        pattern = self.ANATOMICAL_REFERENCE.format(
            participant_label=participant_label
        )
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
