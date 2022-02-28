"""
Definition of the Brainnetome atlas parcellation dictionary.
"""
from pathlib import Path
from typing import Any, Dict

import nibabel as nib
import pandas as pd

#: MNI-based atlases directory.
MNI_PATH: Path = Path("/media/groot/Data/Parcellations/MNI")

#
# Volume
#
#: Name of the Brainnetome atlas volume image file.
BRAINNETOME_VOLUME_NAME: str = "BN_Atlas_274_combined_1mm.nii.gz"
#: Path to the Brainnetome atlas volume.
BRAINNETOME_VOLUME_PATH: Path = MNI_PATH / BRAINNETOME_VOLUME_NAME
#
# Parcels
#
#: Name of the Brainnetome atlas parcels CSV file.
BRAINNETOME_PARCELS_NAME: str = "BNA_with_cerebellum.csv"
#: Path to the brainnetome parcels CSV.
BRAINNETOME_PARCELS_PATH: Path = MNI_PATH / BRAINNETOME_PARCELS_NAME
#
# GCS
#
#: Brainnetome FreeSurfer directory path.
BRAINNETOME_FS_PATH: Path = MNI_PATH / "Brainnetome_FS"
#: GCS file name template.
GCS_NAME_TEMPLATE: str = "{hemi}.BN_Atlas.gcs"
#: GCS file path template.
GCS_PATH_TEMPLATE: str = str(BRAINNETOME_FS_PATH / GCS_NAME_TEMPLATE)
#: Subcortex GCS file name.
SUBCORTEX_GCS_NAME: str = "BN_Atlas_subcortex.gca"
#: Subcortex GCS path.
SUBCORTEX_GCS_PATH: Path = BRAINNETOME_FS_PATH / SUBCORTEX_GCS_NAME
#
# ctab
#
#: ctab file name.
CTAB_FILE_NAME: str = "BN_Atlas_246_LUT.txt"
#: ctab file path.
CTAB_FILE_PATH: Path = BRAINNETOME_FS_PATH / CTAB_FILE_NAME

#: Parcellation's tabled information
PARCELS = pd.read_csv(BRAINNETOME_PARCELS_PATH, index_col=0)

#: Label column's name
INDEX_COLUMNS = ["Label"]

#: Brainnetome atlas parcellation dictionary.
BRAINNETOME: Dict[str, Any] = {
    "path": BRAINNETOME_VOLUME_PATH,
    "image": nib.load(BRAINNETOME_VOLUME_PATH),
    "parcels": PARCELS,
    "gcs": GCS_PATH_TEMPLATE,
    "gcs_subcortex": SUBCORTEX_GCS_PATH,
    "ctab": CTAB_FILE_PATH,
    "index": pd.MultiIndex.from_frame(pd.DataFrame(PARCELS[INDEX_COLUMNS])),
}
