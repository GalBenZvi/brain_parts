from enum import Enum
from pathlib import Path


class DmriPrep(Enum):
    ANATOMICAL_TEMPLATES = [
        "ANATOMICAL_REFERENCE",
        "MNI_TO_NATIVE_TRANSFORMATION",
        "GM_PROBABILITY",
    ]
    ANATOMICAL_REFERENCE = "*desc-preproc_T1w.nii*"
    MNI_TO_NATIVE_TRANSFORMATION = "*from-MNI*_to-T1w_mode-image_xfm.h5"
    GM_PROBABILITY = "*label-GM_probseg.nii*"
    T1_TO_EPI_TRANSFORM = (
        "{session}/dwi/*from-T1w_to-epiref_mode-image_xfm.txt"
    )
    NATIVE_EPI_REFERENCE = "{session}/dwi/*space-orig_desc-preproc_epiref.nii*"


class QsiPrep(Enum):
    ANATOMICAL_TEMPLATES = [
        "ANATOMICAL_REFERENCE",
        "MNI_TO_NATIVE_TRANSFORMATION",
        "GM_PROBABILITY",
    ]
    ANATOMICAL_REFERENCE = "*desc-preproc_T1w.nii*"
    MNI_TO_NATIVE_TRANSFORMATION = "*from-MNI*_to-T1w_mode-image_xfm.h5"
    GM_PROBABILITY = "*label-GM_probseg.nii*"
    NATIVE_EPI_REFERENCE = "{session}/dwi/*dwiref.nii*"


def generate_atlas_file_name(
    reference: Path,
    parcellation_scheme: str,
    space: str = "anat",
    label: str = None,
    replacement: str = "desc-preproc_T1w",
) -> Path:
    """
    Generate a file's name for a native-space parcellation atlas

    Parameters
    ----------
    reference : Path
        A path to a reference image
    parcellation_scheme : str
        A string representing the parcellation scheme
    space : str, optional
        A notation for the space of this parcellation, by default "anat"
    desc : str, optional
        A specific description for this parcellation, by default None
    replacement : str, optional
        The string within *reference* to be replaced, by default "desc-preproc_T1w"

    Returns
    -------
    Path
        Path to a native parcellation according to input specifications.
    """
    if not label:
        return reference.with_name(
            reference.name.replace(
                replacement, f"space-{space}_desc-{parcellation_scheme}_atlas"
            )
        )
    else:
        return reference.with_name(
            reference.name.replace(
                replacement,
                f"space-{space}_label-{label}_desc-{parcellation_scheme}_atlas",
            )
        )


TEMPLATES = {"dmriprep": DmriPrep, "qsiprep": QsiPrep}
