from pathlib import Path

import nibabel as nib
import pandas as pd

BN_IMAGE = Path("/media/groot/Data/Parcellations/MNI/BN_Atlas_274_combined_1mm.nii.gz")
BN_PARCELS = Path("/media/groot/Data/Parcellations/MNI/BNA_with_cerebellum.csv")
PARCELLATIONS = {
    "brainnetome": {
        "path": BN_IMAGE,
        "image": nib.load(BN_IMAGE),
        "parcels": pd.read_csv(BN_PARCELS, index_col=0),
        "gcs": "/media/groot/Data/Parcellations/MNI/Brainnetome_FS/{hemi}.BN_Atlas.gcs",
        "gcs_subcortex": "/media/groot/Data/Parcellations/MNI/Brainnetome_FS/BN_Atlas_subcortex.gca",
        "ctab": "/media/groot/Data/Parcellations/MNI/Brainnetome_FS/BN_Atlas_246_LUT.txt",
    }
}
