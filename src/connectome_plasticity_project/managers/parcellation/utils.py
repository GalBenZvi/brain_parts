import logging
import os
import warnings
from pathlib import Path
from re import template

import nibabel as nib
import numpy as np
import pandas as pd
import tqdm
from nipype.interfaces import fsl
from nipype.interfaces.ants import ApplyTransforms
from nipype.interfaces.freesurfer import CALabel
from nipype.interfaces.freesurfer import MRIsCALabel
from nipype.interfaces.freesurfer import ParcellationStats
from nipype.interfaces.freesurfer import SegStats

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
        "gcs": "/media/groot/Data/Parcellations/MNI/Brainnetome_FS/{hemi}.BN_Atlas.gcs",
        "gcs_subcortex": "/media/groot/Data/Parcellations/MNI/Brainnetome_FS/BN_Atlas_subcortex.gca",
        "ctab": "/media/groot/Data/Parcellations/MNI/Brainnetome_FS/BN_Atlas_246_LUT.txt",
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
TENSOR_METRICS_OUTPUT_TEMPLATE = "{dmriprep_dir}/sub-{participant_label}/ses-{session}/dwi/sub-{participant_label}_ses-{session}_space-anat_desc-TensorMetrics_atlas-{parcellation_scheme}_meas-{measure}.csv"

APARCTSTATS2TABLE = "aparcstats2table --subjects {subjects} --parc={parcellation_scheme} --hemi={hemi} --measure={measure} --tablefile={out_file}"


def generate_annotation_file(
    freesurfer_dir: Path, subject: str, parcellation_scheme: str, gcs: str
):
    """
    For a single subject, produces an annotation file, in which each cortical surface vertex is assigned a neuroanatomical label.

    Parameters
    ----------
    freesurfer_dir : Path
        Path to Freesurfer's outputs directory
    subject : str
        A string representing an existing subject in *freesurfer_dir*
    parcellation_scheme : str
        The name of the parcellation scheme.
    gcs : str
        A freesurfer's .gcs template file.

    Returns
    -------
    dict
        A dictionary with keys of hemispheres and values as corresponding .annot files.
    """
    annot_files = {}
    for hemi in ["lh", "rh"]:
        reg_file = freesurfer_dir / subject / "surf" / f"{hemi}.sphere.reg"
        curv, smoothwm, sulc = [
            freesurfer_dir / subject / "surf" / f"{hemi}.{surftype}"
            for surftype in ["smoothwm", "curv", "sulc"]
        ]
        hemi_gcs = gcs.format(hemi=hemi)
        out_file = (
            freesurfer_dir
            / subject
            / "label"
            / f"{hemi}.{parcellation_scheme}.annot"
        )
        if not out_file.exists():
            logging.info(
                f"Generating annotation file for {parcellation_scheme} in {subject} {hemi} space."
            )
            calabel = MRIsCALabel(
                canonsurf=reg_file,
                subjects_dir=freesurfer_dir,
                curv=curv,
                smoothwm=smoothwm,
                sulc=sulc,
                subject_id=subject,
                hemisphere=hemi,
                out_file=out_file,
                classifier=hemi_gcs,
                seed=42,
            )
            calabel.run()
        annot_files[hemi] = out_file
    return annot_files


def generate_default_args(freesurfer_dir: Path, subject: str) -> dict:
    """
    Gather default required arguments for nipype's implementation of Freesurfer's *mris_anatomical_stats*

    Parameters
    ----------
    freesurfer_dir : Path
        Path to Freesurfer's outputs directory
    subject : str
        A string representing an existing subject in *freesurfer_dir*

    Returns
    -------
    dict
        A dictionary with keys that map to nipype's required arguements
    """
    args = {"subject_id": subject, "subjects_dir": freesurfer_dir}
    subject_dir = freesurfer_dir / subject

    for hemi in ["lh", "rh"]:
        for datatype in ["pial", "white"]:
            args[f"{hemi}_{datatype}"] = (
                subject_dir / "surf" / f"{hemi}.{datatype}"
            )
    for key, value in zip(
        ["brainmask", "aseg", "ribbon", "wm", "transform"],
        [
            "brainmask.mgz",
            "aseg.presurf.mgz",
            "ribbon.mgz",
            "wm.mgz",
            "transforms/talairach.xfm",
        ],
    ):
        args[key] = subject_dir / "mri" / value
    args["tabular_output"] = True
    return args


def map_subcortex(
    freesurfer_dir: Path,
    subject: str,
    parcellation_scheme: str,
    gcs_subcrotex: str,
):
    """
    For a single subject, produces an annotation file, in which each sub-cortical surface vertex is assigned a neuroanatomical label.

    Parameters
    ----------
    freesurfer_dir : Path
        Path to Freesurfer's outputs directory
    subject : str
        A string representing an existing subject in *freesurfer_dir*
    parcellation_scheme : str
        The name of the parcellation scheme.
    gcs_subcortex : str
        A freesurfer's .gcs template file.

    Returns
    -------
    dict
        A dictionary with keys of hemispheres and values as corresponding .annot files.
    """
    target = freesurfer_dir / subject / "mri" / f"brain.mgz"
    transform = (
        freesurfer_dir / subject / "mri" / "transforms" / "talairach.m3z"
    )
    out_file = (
        freesurfer_dir
        / subject
        / "mri"
        / f"{parcellation_scheme}_subcortex.mgz"
    )
    if not out_file.exists():
        logging.info(
            f"Generating annotation file for {parcellation_scheme}'s sub-cortex in {subject} space."
        )
        calabel = CALabel(
            subjects_dir=freesurfer_dir,
            in_file=target,
            transform=transform,
            out_file=out_file,
            template=gcs_subcrotex,
        )
        calabel.run()
    return out_file


def freesurfer_subcortical_parcellation(
    freesurfer_dir: Path,
    subject: str,
    parcellation_scheme: str,
    gcs_subcortex: str,
    color_table: str,
):
    """
    Calculates different Freesurfer-derived metrics according to subcortical parcellation

    Parameters
    ----------
    freesurfer_dir : Path
        Path to Freesurfer's outputs directory
    subject : str
        A string representing an existing subject in *freesurfer_dir*
    parcellation_scheme : str
        The name of the parcellation scheme.
    gcs_subcortex : str
        A freesurfer's .gcs template file.

    Returns
    -------
    dict
        A dictionary with keys corresponding to hemisphere's metrics acoording to *parcellation_scheme*
    """
    mapped_subcortex = map_subcortex(
        freesurfer_dir, subject, parcellation_scheme, gcs_subcortex
    )
    summary_file = (
        freesurfer_dir
        / subject
        / "stats"
        / f"subcortex.{parcellation_scheme}.stats"
    )
    if not summary_file.exists():
        ss = SegStats(
            segmentation_file=mapped_subcortex,
            subjects_dir=freesurfer_dir,
            summary_file=summary_file,
            color_table_file=color_table,
            exclude_id=0,
            # total_gray=True,
            # subcort_gm=True,
            # cortex_vol_from_surf=True,
            # wm_vol_from_surf=True,
            # args=f"--subject {subject}",
        )
        ss.run()
    return summary_file


def freesurfer_anatomical_parcellation(
    freesurfer_dir: Path, subject: str, parcellation_scheme: str, gcs: str
):
    """
    Calculates different Freesurfer-derived metrics according to .annot files

    Parameters
    ----------
    freesurfer_dir : Path
        Path to Freesurfer's outputs directory
    subject : str
        A string representing an existing subject in *freesurfer_dir*
    parcellation_scheme : str
        The name of the parcellation scheme.
    gcs : str
        A freesurfer's .gcs template file.

    Returns
    -------
    dict
        A dictionary with keys corresponding to hemisphere's metrics acoording to *parcellation_scheme*
    """
    annotations = generate_annotation_file(
        freesurfer_dir, subject, parcellation_scheme, gcs
    )
    args = generate_default_args(freesurfer_dir, subject)
    stats = {}
    for hemi, annot_file in annotations.items():
        stats[hemi] = {}
        out_color = (
            freesurfer_dir
            / subject
            / "label"
            / f"aparc.annot.{parcellation_scheme}.ctab"
        )
        out_table = (
            freesurfer_dir
            / subject
            / "stats"
            / f"{hemi}.{parcellation_scheme}.stats"
        )
        args["hemisphere"] = hemi
        args["in_annotation"] = annot_file
        args["thickness"] = (
            freesurfer_dir / subject / "surf" / f"{hemi}.thickness"
        )
        if not out_table.exists() or not out_color.exists():
            parcstats = ParcellationStats(**args)
            parcstats.run()
        stats[hemi]["table"] = out_table
        stats[hemi]["color"] = out_color
    return stats


def group_freesurfer_metrics(
    subjects: list,
    destination: Path,
    parcellation_scheme: str,
    force=True,
):
    """
    Utilizes Freesurfer's aparcstats2table to group different Freesurfer-derived across subjects according to *parcellation_scheme*

    Parameters
    ----------
    subjects : list
        A list of subjects located under *SUBJECTS_DIR*
    destination : Path
        The destination underwhich group-wise files will be stored
    parcellation_scheme : str
        The parcellation scheme (subjects must have stats/{hemi}.{parcellation_scheme}.stats file for this to work)
    """
    destination.mkdir(exist_ok=True, parents=True)
    data = {}
    for hemi in ["lh", "rh"]:
        data[hemi] = {}
        for measure in [
            "area",
            "volume",
            "thickness",
            "thicknessstd",
            "meancurv",
        ]:
            out_file = (
                destination / f"{hemi}_{parcellation_scheme}_{measure}.csv"
            )
            if not out_file.exists() or force:
                cmd = APARCTSTATS2TABLE.format(
                    subjects=" ".join(subjects),
                    parcellation_scheme=parcellation_scheme,
                    hemi=hemi,
                    measure=measure,
                    out_file=out_file,
                )
                os.system(cmd)
            data[hemi][measure] = out_file
    return data


def parcellate_image(
    atlas: Path, image: Path, parcels: pd.DataFrame, np_operation="nanmean"
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
        out.loc[i] = eval(f"np.{np_operation}(data[mask])")

    return out


def parcellate_subject_tensors(
    dmriprep_dir: Path,
    participant_label: str,
    image: Path,
    multi_column: pd.MultiIndex,
    parcels: pd.DataFrame,
    parcellation_scheme: str,
    cropped_to_gm: bool = True,
    force: bool = False,
    np_operation: str = "nanmean",
):
    """
    Parcellates available data for *participant_label*, declared by *multi_column* levels.

    Parameters
    ----------
    dmriprep_dir : Path
        Path to *dmriprep* outputs' directory
    participant_label : str
        A label referring to an existing subject
    image : Path
        Path to subject's native-space parcellation
    multi_column : pd.MultiIndex
        A multi-column constructed by ROI * metrics.
    parcels : pd.DataFrame
        A dataframe describing the parcellation scheme.
    parcellation_scheme : str
        The name of the parcellation scheme.

    Returns
    -------
    pd.DataFrame
        A dataframe containing all of *participant_label*'s data, parcellated by *parcellation_scheme*.
    """
    sessions = [
        s.name.split("-")[-1]
        for s in dmriprep_dir.glob(f"sub-{participant_label}/ses-*")
    ]
    multi_index = pd.MultiIndex.from_product([[participant_label], sessions])
    subj_data = pd.DataFrame(index=multi_index, columns=multi_column)
    for session in sessions:
        out_file = Path(
            TENSOR_METRICS_OUTPUT_TEMPLATE.format(
                dmriprep_dir=dmriprep_dir,
                participant_label=participant_label,
                session=session,
                parcellation_scheme=parcellation_scheme,
                measure=np_operation.replace("nan", ""),
            )
        )
        if cropped_to_gm:
            out_name = out_file.name.split("_")
            out_name.insert(3, "label-GM")
            out_file = out_file.parent / "_".join(out_name)
        if out_file.exists() and not force:
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
                ] = parcellate_image(
                    image, metric_file, parcels, np_operation
                ).values
            subj_data.loc[(participant_label, session)].to_csv(out_file)
    return subj_data


def parcellate_tensors(
    dmriprep_dir: Path,
    multi_column: pd.MultiIndex,
    parcellations: dict,
    parcels: pd.DataFrame,
    parcellation_scheme: str,
    cropped_to_gm: bool = True,
    force: bool = False,
    np_operation: str = "nanmean",
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
        try:
            subj_data = parcellate_subject_tensors(
                dmriprep_dir,
                participant_label,
                image,
                multi_column,
                parcels,
                parcellation_scheme,
                cropped_to_gm,
                force,
                np_operation,
            )
            data = pd.concat([data, subj_data])
        except FileNotFoundError:
            logging.warn(f"Missing files for subject {participant_label}.")
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


def apply_mask(mask: Path, target: Path, out_file: Path, threshold: float):
    """
    Apply pre-calculated mask to *target* using specified *threshold*

    Parameters
    ----------
    mask : Path
        Pre-calculated mask
    target : Path
        Target to apply mask to
    out_file : Path
        Path tp output masked image
    threshold: float
        Thresold to use for masking
    """
    if not out_file.exists():
        mask_img, target_img = [nib.load(f) for f in [mask, target]]
        bin_mask = mask_img.get_fdata() > threshold
        masked_target = target_img.get_fdata().copy()
        masked_target[~bin_mask] = 0
        masked_image = nib.Nifti1Image(masked_target, target_img.affine)
        nib.save(masked_image, out_file)
