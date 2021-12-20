import logging
import warnings
from pathlib import Path

import nibabel as nib
import pandas as pd
import tqdm
from nipype.interfaces.ants import ApplyTransforms
from nltools.data import Brain_Data
from nltools.mask import expand_mask

warnings.filterwarnings("ignore")
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

TENSOR_METRICS_FILES_TEMPLATE = "{dmriprep_dir}/sub-{participant_label}/ses-{session}/dwi/sub-{participant_label}_ses-{session}_dir-FWD_space-anat_desc-{metric}_epiref.nii.gz"
TENSOR_METRICS_OUTPUT_TEMPLATE = "{dmriprep_dir}/sub-{participant_label}/ses-{session}/dwi/sub-{participant_label}_ses-{session}_space-anat_desc-TensorMetrics_atlas-{parcellation_scheme}.csv"


def parcellate_image(
    atlas: Path, image: Path, parcels: pd.DataFrame
) -> pd.Series:
    """
    Parcellates an image according to *atlas*

    Parameters
    ----------
    atlas : Path
        A parcellation atlas in *image* space.
    image : Path
        An image to be parcellated
    parcels : pd.DataFrame
        A dataframe for *atlas* parcels.

    Returns
    -------
    pd.Series
        The mean value of *image* in each *atlas* parcel.
    """
    atlas_data = nib.load(atlas).get_fdata()
    data = nib.load(image).get_fdata()
    out = pd.Series(index=parcels.index)
    for i in parcels.index:
        label = parcels.loc[i, "Label"]
        mask = atlas_data == label
        out.loc[i] = data[mask].mean()

    return out


def parcellate_subject_tensors(
    dmriprep_dir: Path,
    participant_label: str,
    image: Path,
    multi_column: pd.MultiIndex,
    parcels: pd.DataFrame,
    parcellation_scheme: str,
):
    sessions = [
        s.name.split("-")[-1]
        for s in dmriprep_dir.glob(f"sub-{participant_label}/ses-*")
    ]
    multi_index = pd.MultiIndex.from_product([[participant_label], sessions])
    mask = Brain_Data(image)
    subj_data = pd.DataFrame(index=multi_index, columns=multi_column)
    for session in sessions:
        out_file = Path(
            TENSOR_METRICS_OUTPUT_TEMPLATE.format(
                dmriprep_dir=dmriprep_dir,
                participant_label=participant_label,
                session=session,
                parcellation_scheme=parcellation_scheme,
            )
        )
        if out_file.exists():
            data = pd.read_csv(out_file, index_col=[0, 1], header=[0, 1])
            subj_data.loc[(participant_label, session)] = data.T.loc[
                (participant_label, session)
            ]
        else:
            for metric in multi_column.levels[-1]:
                logging.info(metric)
                metric_file = TENSOR_METRICS_FILES_TEMPLATE.format(
                    dmriprep_dir=dmriprep_dir,
                    participant_label=participant_label,
                    session=session,
                    metric=metric.lower(),
                )
                subj_data.loc[
                    (participant_label, session), (slice(None), metric)
                ] = parcellate_image(image, metric_file, parcels).values
            subj_data.loc[(participant_label, session)].to_csv(out_file)

    return subj_data


def parcellate_tensors(
    dmriprep_dir: Path,
    multi_column: pd.MultiIndex,
    parcellations: dict,
    parcels: pd.DataFrame,
    parcellation_scheme: str,
) -> pd.DataFrame:
    """
    Parcellate *dmriprep* derived tensor's metrics according to ROI stated by *df*

    Parameters
    ----------
    dmriprep_dir : Path
        Path to *dmriprep* outputs
    multi_column : pd.MultiIndex
        A multi-level column with ROI/tensor metrics combinations
    parcellations : dict
        A dictionary with representing subjects, and values containing paths to subjects-space parcellations.

    Returns
    -------
    pd.DataFrame
        An updated *df*
    """
    data = pd.DataFrame()
    for participant_label, image in tqdm.tqdm(parcellations.items()):
        logging.info(
            f"Averaging tensor-derived metrics according to {parcellation_scheme} parcels, in subject {participant_label} anatomical space."
        )
        subj_data = parcellate_subject_tensors(
            dmriprep_dir,
            participant_label,
            image,
            multi_column,
            parcels,
            parcellation_scheme,
        )
        data = pd.concat([data, subj_data])
    return data


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
