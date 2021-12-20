import logging
from pathlib import Path

import nibabel as nib
import pandas as pd
from nipype.interfaces.ants import ApplyTransforms

BN_IMAGE = Path(
    "/media/groot/Data/Parcellations/MNI/BN_Atlas_274_combined_1mm.nii.gz"
)
BN_PARCELS = Path(
    "/media/groot/Data/Parcellations/MNI/BNA_with_cerebellum.csv"
)

PARCELLATIONS = {
    "brainnetome": {
        "path": BN_IMAGE,
        "image": nib.load(BN_IMAGE),
        "parcels": pd.read_csv(BN_PARCELS, index_col=0),
    }
}

DEFAULT_DESTINATION = Path(
    "/home/groot/Projects/PhD/connectomeplasticity/data/parcellations"
)

LOGGER_CONFIG = dict(
    filemode="w",
    format="%(asctime)s - %(message)s",
    level=logging.INFO,
)


def parcellate_tensors(
    dmriprep_dir: Path, df: pd.DataFrame, image: nib.Nifti1Image
) -> pd.DataFrame:
    """
    Parcellate *dmriprep* derived tensor's metrics according to ROI stated by *df*

    Parameters
    ----------
    dmriprep_dir : Path
        Path to *dmriprep* outputs
    df : pd.DataFrame
        A dataframe with subjects as index and ROI/tensor metrics multi index as columns
    image : nib.Nifti1Image
        Parcellation scheme's image to parcellate by

    Returns
    -------
    pd.DataFrame
        An updated *df*
    """
    # for i,row in df.iterrows():


def at_ants(
    in_file: Path,
    ref: Path,
    xfm: Path,
    outfile: Path,
    nn: bool,
    invert_xfm: bool = False,
    run: bool = True,
):
    """
    Apply pre-calculated transformations between images of different spaces
    Parameters
    ----------
    in_file : Path
        Path to the "moving" file
    ref : Path
        Path to the "static" file
    xfm : Path
        Path to a pre-calculated transformation
    outfile : Path
        Path to output file
    nn : bool
        Whether to use Nearest Neighbout interpolation (for atlas registrations)
    invert_xfm : bool, optional
        Whether to invert the transformation file before applying it, by default False
    """
    at = ApplyTransforms()
    at.inputs.input_image = in_file
    at.inputs.reference_image = ref
    at.inputs.transforms = xfm
    at.inputs.output_image = str(outfile)
    if nn:
        at.inputs.interpolation = "NearestNeighbor"
    if invert_xfm:
        at.inputs.invert_transform_flags = True
    if run:
        at.run()
    else:
        return at
