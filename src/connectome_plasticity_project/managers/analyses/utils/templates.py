from enum import Enum


class DmriPrep(Enum):
    ANATOMICAL_TEMPLATES = [
        "ANATOMICAL_REFERENCE",
        "MNI_TO_NATIVE_TRANSFORMATION",
        "GM_PROBABILITY",
    ]
    ANATOMICAL_REFERENCE = "*desc-preproc_T1w.nii*"
    MNI_TO_NATIVE_TRANSFORMATION = "*from-MNI*_to-T1w_mode-image_xfm.h5"
    GM_PROBABILITY = "*label-GM_probseg.nii*"


TEMPLATES = {"dmriprep": DmriPrep}
