from enum import Enum
from pathlib import Path

BIDS_NAMING_TEMPLATE = {
    "subject": "sub",
    "session": "ses",
    "acquisition": "acq",
    "ceagent": "ce",
    "reconstruction": "rec",
    "run": "run",
    "space": "space",
    "cohort": "cohort",
    "resolution": "res",
    "label": "label",
    "desc": "desc",
    "atlas": "atlas",
}

TENSOR_DERIVED_METRICS = {
    "adc": "apparent diffusion coefficient",
    "fa": "fractional anisotropy",
    "ad": "axial diffusivity",
    "rd": "radial diffusivity",
    "cl": "Westing linearity",
    "cp": "Westing planarity",
    "cs": "Westing sphericity",
    "evec": "Eigenvalue",
    "eval": "Eigenvector",
}


class DmriPrep(Enum):
    ANATOMICAL_TEMPLATES = [
        "ANATOMICAL_REFERENCE",
        "MNI_TO_NATIVE_TRANSFORMATION",
        "GM_PROBABILITY",
    ]
    EPI_TEMPLATES = ["NATIVE_EPI_REFERENCE"]
    LONGITUDINAL_SENSITIVE = True
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
    EPI_TEMPLATES = ["NATIVE_EPI_REFERENCE"]
    LONGITUDINAL_SENSITIVE = False
    ANATOMICAL_REFERENCE = "*desc-preproc_T1w.nii*"
    MNI_TO_NATIVE_TRANSFORMATION = "*from-MNI*_to-T1w_mode-image_xfm.h5"
    GM_PROBABILITY = "*label-GM_probseg.nii*"
    NATIVE_EPI_REFERENCE = "*desc-preproc_dwi.nii*"
    NATIVE_PARCELLATION_NAMING_KWARGS = {
        "anatomical": {"space": "T1w", "resolution": "anat", "suffix": "dseg"},
        "epi": {"space": "T1w", "resolution": "dwi", "suffix": "dseg"},
    }


def generate_atlas_file_name(
    reference: Path,
    parcellation_scheme: str,
    space: str = "anat",
    label: str = None,
    replacement: str = "T1w",
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
    out_file = reference.with_name(reference.name.replace(replacement, "dseg"))
    if not label:
        return out_file.with_name(
            out_file.name.replace(
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
