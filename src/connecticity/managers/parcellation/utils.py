import logging
import os
import warnings
from pathlib import Path
from typing import Dict, Iterable, Union

import nibabel as nib
import numpy as np
import pandas as pd
import tqdm
from nilearn.image import resample_to_img
from nipype.interfaces.ants import ApplyTransforms
from nipype.interfaces.freesurfer import (CALabel, MRIsCALabel,
                                          ParcellationStats, SegStats)

from connecticity.managers.parcellation import messages

warnings.filterwarnings("ignore")


#: Default parcellation logging configuration.
LOGGER_CONFIG = dict(
    filemode="w",
    format="%(asctime)s - %(message)s",
    level=logging.INFO,
)

#: Command template to be used to run dwi2tensor.
DWI2TENSOR_COMMAND_TEMPLATE: str = "dwi2tensor -grad {grad} {dwi} {out_file}"
#: Custom mapping of dwi2tensor keyword arguments.
TENSOR2METRIC_KWARGS_MAPPING: Dict[str, str] = {"eval": "value"}
#: QSIPrep DWI file template.
QSIPREP_DWI_TEMPLATE = "{qsiprep_dir}/sub-{participant_label}/ses-{session}/dwi/sub-{participant_label}_ses-{session}_space-T1w_desc-preproc_dwi.{extension}"  # noqa
#: Tensor metric file template.
TENSOR_METRICS_FILES_TEMPLATE = "{dmriprep_dir}/sub-{participant_label}/ses-{session}/dwi/sub-{participant_label}_ses-{session}_dir-FWD_space-anat_desc-{metric}_epiref.nii.gz"  # noqa
#: Parcellated tensor metrics file template.
TENSOR_METRICS_OUTPUT_TEMPLATE = "{dmriprep_dir}/sub-{participant_label}/ses-{session}/dwi/sub-{participant_label}_ses-{session}_space-anat_desc-TensorMetrics_atlas-{parcellation_scheme}_meas-{measure}.csv"  # noqa: E501
#: Command template to be used to run aparcstats2table.
APARCTSTATS2TABLE_TEMPLATE = "aparcstats2table --subjects {subjects} --parc={parcellation_scheme} --hemi={hemi} --measure={measure} --tablefile={out_file}"  # noqa: E501
#: Hemisphere labels in file name templates.
HEMISPHERE_LABELS: Iterable[str] = ["lh", "rh"]
#: Surface labels in file name templates.
SURFACES: Iterable[str] = ["smoothwm", "curv", "sulc"]
#: Data types in file name templates.
DATA_TYPES: Iterable[str] = ["pial", "white"]
#: Registered file name template.
REG_FILE_NAME_TEMPLATE: str = "{hemisphere_label}.sphere.reg"
#: FreeSurfer's surfaces directory name.
SURFACES_DIR_NAME: str = "surf"
#: FreeSurfer's MRI directory name.
MRI_DIR_NAME: str = "mri"
#: FreeSurfer's labels directory name.
LABELS_DIR_NAME: str = "label"
#: FreeSurfer's stats directory name.
STATS_DIR_NAME: str = "stats"
#: mris_anatomical_stats parameter keys.
STATS_KEYS: Iterable[Union[str, bool]] = [
    "brainmask",
    "aseg",
    "ribbon",
    "wm",
    "transform",
    "tabular_output",
]
#: mris_anatomical_stats parameter values.
STATS_VALUES: Iterable[str] = [
    "brainmask.mgz",
    "aseg.presurf.mgz",
    "ribbon.mgz",
    "wm.mgz",
    "transforms/talairach.xfm",
    True,
]
STATS_MEASURES: Iterable[str] = [
    "area",
    "volume",
    "thickness",
    "thicknessstd",
    "meancurv",
]
STATS_NAME_TEMPLATE: str = (
    "{hemisphere_label}_{parcellation_scheme}_{measure}.csv"
)
SUBCORTICAL_STATS_NAME_TEMPLATE: str = "subcortex.{parcellation_scheme}.stats"


def generate_annotation_file(
    subject_dir: Path,
    hemisphere_label: str,
    parcellation_scheme: str,
    gcs_template: str,
):
    surfaces_dir = subject_dir / SURFACES_DIR_NAME
    labels_dir = subject_dir / LABELS_DIR_NAME
    # Check for existing file in expected output path.
    out_file_name = f"{hemisphere_label}.{parcellation_scheme}.annot"
    out_file = labels_dir / out_file_name
    if out_file.exists():
        return out_file
    # If no existing output is found, create mris_ca_label input
    # configuration.
    reg_file_name = REG_FILE_NAME_TEMPLATE.format(
        hemisphere_label=hemisphere_label
    )
    reg_file = surfaces_dir / reg_file_name
    curv, smoothwm, sulc = [
        surfaces_dir / f"{hemisphere_label}.{surface_label}"
        for surface_label in SURFACES
    ]
    hemi_gcs = gcs_template.format(hemi=hemisphere_label)
    # Log annotation file generation start.
    message = messages.ANNOTATION_FILE_GENERATION_START.format(
        parcellation_scheme=parcellation_scheme,
        subject_label=subject_dir.name,
        hemisphere_label=hemisphere_label,
    )
    logging.info(message)
    # Create interface instance, run, and return the result.
    ca_label = MRIsCALabel(
        canonsurf=reg_file,
        subjects_dir=subject_dir.parent,
        curv=curv,
        smoothwm=smoothwm,
        sulc=sulc,
        subject_id=subject_dir.parent.name,
        hemisphere=hemisphere_label,
        out_file=out_file,
        classifier=hemi_gcs,
        seed=42,
    )
    ca_label.run()
    return out_file


def generate_annotations(
    freesurfer_dir: Path,
    subject_label: str,
    parcellation_scheme: str,
    gcs_template: str,
):
    """
    For a single subject, produces an annotation file, in which each cortical
    surface vertex is assigned a neuroanatomical label.

    Parameters
    ----------
    freesurfer_dir : Path
        Path to Freesurfer's outputs directory
    subject_label : str
        A string representing an existing subject in *freesurfer_dir*
    parcellation_scheme : str
        The name of the parcellation scheme
    gcs_template : str
        A freesurfer's .gcs template file

    Returns
    -------
    dict
        A dictionary with keys of hemispheres and values as corresponding
        *.annot* files
    """
    subject_dir = freesurfer_dir / subject_label
    return {
        hemisphere_label: generate_annotation_file(
            subject_dir, hemisphere_label, parcellation_scheme, gcs_template
        )
        for hemisphere_label in HEMISPHERE_LABELS
    }


def generate_default_args(freesurfer_dir: Path, subject_label: str) -> dict:
    """
    Gather default required arguments for nipype's implementation of
    FreeSurfer's *mris_anatomical_stats*.

    Parameters
    ----------
    freesurfer_dir : Path
        Path to Freesurfer's outputs directory
    subject_label : str
        A string representing an existing subject in *freesurfer_dir*

    Returns
    -------
    dict
        A dictionary with keys that map to nipype's required arguements
    """
    subject_dir = freesurfer_dir / subject_label
    surface_dir = subject_dir / SURFACES_DIR_NAME
    mri_dir = subject_dir / MRI_DIR_NAME
    args = {"subject_id": subject_label, "subjects_dir": freesurfer_dir}
    for hemi in HEMISPHERE_LABELS:
        for datatype in DATA_TYPES:
            key = f"{hemi}_{datatype}"
            file_name = f"{hemi}.{datatype}"
            args[key] = surface_dir / file_name
    for key, value in zip(STATS_KEYS, STATS_VALUES):
        args[key] = mri_dir / value
    return args


def map_subcortex(
    freesurfer_dir: Path,
    subject_label: str,
    parcellation_scheme: str,
    gcs_subcrotex: str,
):
    """
    For a single subject, produces an annotation file, in which each
    sub-cortical surface vertex is assigned a neuroanatomical label.

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
        A dictionary with keys of hemispheres and values as corresponding
        *.annot* files.
    """
    # Check for an existing annotations file.
    subject_dir = freesurfer_dir / subject_label
    mri_dir = subject_dir / MRI_DIR_NAME
    out_file = mri_dir / f"{parcellation_scheme}_subcortex.mgz"
    if out_file.exists():
        return out_file
    # Create a subcortical annotations file if none was found.
    target = mri_dir / "brain.mgz"
    transform = mri_dir / "transforms" / "talairach.m3z"
    # Log subcortical annotations file generation start.
    message = messages.SUBCORTICAL_ANNOTATION_FILE_GENERATION_START.format(
        parcellation_scheme=parcellation_scheme,
        subject_label=subject_label,
    )
    logging.info(message)
    # Create interface instance, run, and return result.
    ca_label = CALabel(
        subjects_dir=freesurfer_dir,
        in_file=target,
        transform=transform,
        out_file=out_file,
        template=gcs_subcrotex,
    )
    ca_label.run()
    return out_file


def freesurfer_subcortical_parcellation(
    freesurfer_dir: Path,
    subject_label: str,
    parcellation_scheme: str,
    gcs_subcortex: str,
    color_table: str,
):
    """
    Calculates different Freesurfer-derived metrics according to subcortical
    parcellation

    Parameters
    ----------
    freesurfer_dir : Path
        Path to Freesurfer's outputs directory
    subject_label : str
        A string representing an existing subject in *freesurfer_dir*
    parcellation_scheme : str
        The name of the parcellation scheme
    gcs_subcortex : str
        A freesurfer's .gcs template file

    Returns
    -------
    dict
        A dictionary with keys corresponding to hemisphere's metrics acoording
        to *parcellation_scheme*
    """
    mapped_subcortex = map_subcortex(
        freesurfer_dir, subject_label, parcellation_scheme, gcs_subcortex
    )
    subject_dir = freesurfer_dir / subject_label
    stats_dir = subject_dir / STATS_DIR_NAME
    file_name = SUBCORTICAL_STATS_NAME_TEMPLATE.format(
        parcellation_scheme=parcellation_scheme
    )
    summary_file = stats_dir / file_name
    if not summary_file.exists():
        ss = SegStats(
            segmentation_file=mapped_subcortex,
            subjects_dir=freesurfer_dir,
            summary_file=summary_file,
            color_table_file=color_table,
            exclude_id=0,
        )
        ss.run()
    return summary_file


def freesurfer_anatomical_parcellation(
    freesurfer_dir: Path,
    subject_label: str,
    parcellation_scheme: str,
    gcs: str,
):
    """
    Calculates different Freesurfer-derived metrics according to .annot files

    Parameters
    ----------
    freesurfer_dir : Path
        Path to Freesurfer's outputs directory
    subject_label : str
        A string representing an existing subject in *freesurfer_dir*
    parcellation_scheme : str
        The name of the parcellation scheme.
    gcs : str
        A freesurfer's .gcs template file.

    Returns
    -------
    dict
        A dictionary with keys corresponding to hemisphere's metrics acoording
        to *parcellation_scheme*
    """
    annotations = generate_annotations(
        freesurfer_dir, subject_label, parcellation_scheme, gcs
    )
    args = generate_default_args(freesurfer_dir, subject_label)
    stats = {}
    subject_dir = freesurfer_dir / subject_label
    labels_dir = subject_dir / LABELS_DIR_NAME
    stats_dir = subject_dir / STATS_DIR_NAME
    surfaces_dir = subject_dir / SURFACES_DIR_NAME
    for hemisphere_label, annotations_path in annotations.items():
        stats[hemisphere_label] = {}
        out_color = labels_dir / f"aparc.annot.{parcellation_scheme}.ctab"
        out_table = (
            stats_dir / f"{hemisphere_label}.{parcellation_scheme}.stats"
        )
        args["hemisphere"] = hemisphere_label
        args["in_annotation"] = annotations_path
        args["thickness"] = surfaces_dir / f"{hemisphere_label}.thickness"
        if not out_table.exists() or not out_color.exists():
            parcstats = ParcellationStats(**args)
            parcstats.run()
        stats[hemisphere_label]["table"] = out_table
        stats[hemisphere_label]["color"] = out_color
    return stats


def group_freesurfer_metrics(
    subjects: list,
    destination: Path,
    parcellation_scheme: str,
    force=True,
):
    """
    Utilizes FreeSurfer's aparcstats2table to group different
    FreeSurfer-derived across subjects according to *parcellation_scheme*.

    Parameters
    ----------
    subjects : list
        A list of subjects located under *SUBJECTS_DIR*
    destination : Path
        The destination underwhich group-wise files will be stored
    parcellation_scheme : str
        The parcellation scheme (subjects must have
        *stats/{hemi}.{parcellation_scheme}.stats* file for this to work)
    """
    destination.mkdir(exist_ok=True, parents=True)
    data = {}
    for hemisphere_label in HEMISPHERE_LABELS:
        data[hemisphere_label] = {}
        for measure in STATS_MEASURES:
            out_file_name = STATS_NAME_TEMPLATE.format(
                hemisphere_label=hemisphere_label,
                parcellation_scheme=parcellation_scheme,
                measure=measure,
            )
            out_file = destination / out_file_name
            if not out_file.exists() or force:
                cmd = APARCTSTATS2TABLE_TEMPLATE.format(
                    subjects=" ".join(subjects),
                    parcellation_scheme=parcellation_scheme,
                    hemi=hemisphere_label,
                    measure=measure,
                    out_file=out_file,
                )
                os.system(cmd)
            data[hemisphere_label][measure] = out_file
    return data


def parcellate_image(
    atlas: Path, image: Path, parcels: pd.DataFrame, np_operation="nanmean"
) -> pd.Series:
    """
    Parcellates an image according to *atlas*.

    Parameters
    ----------
    atlas : Path
        A parcellation atlas in *image* space
    image : Path
        An image to be parcellated
    parcels : pd.DataFrame
        A dataframe for *atlas* parcels

    Returns
    -------
    pd.Series
        The mean value of *image* in each *atlas* parcel
    """
    out = pd.Series(index=parcels.index)
    try:
        for i in parcels.index:
            # TODO: Remove?
            # callable = getattr(np, np_operation)
            # out.loc[i] = callable(data[mask])
            continue
        return out
    except IndexError:
        atlas = resample_to_img(
            nib.load(atlas),
            nib.load(image),
            interpolation="nearest",
        )
        return parcellate_image(atlas, image, parcels, np_operation)


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
    Parcellates available data for *participant_label*, declared by
    *multi_column* levels.

    Parameters
    ----------
    dmriprep_dir : Path
        Path to *dmriprep* outputs' directory
    participant_label : str
        A label referring to an existing subject
    image : Path
        Path to subject's native-space parcellation
    multi_column : pd.MultiIndex
        A multi-column constructed by ROI * metrics
    parcels : pd.DataFrame
        A dataframe describing the parcellation scheme
    parcellation_scheme : str
        The name of the parcellation scheme

    Returns
    -------
    pd.DataFrame
        A dataframe containing all of *participant_label*'s data, parcellated
        by *parcellation_scheme*
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


def dwi2tensor(in_file: Path, grad: Path, out_file: Path):
    """
    Estimate diffusion's tensor via *mrtrix3*'s *dwi2tensor*.

    Parameters
    ----------
    in_file : Path
        DWI series
    grad : Path
        DWI gradient table in *mrtrix3*'s format.
    out_file : Path
        Output template

    Returns
    -------
    Path
        Refined output in *mrtrix3*'s .mif format.
    """
    out_name = out_file.name.split(".")[0]
    out_file = out_file.with_name("." + out_name + ".mif")
    if not out_file.exists():
        cmd = DWI2TENSOR_COMMAND_TEMPLATE.format(
            grad=grad, dwi=in_file, out_file=out_file
        )
        os.system(cmd)
    return out_file


def tensor2metric(
    tensor: Path,
    derivatives: Path,
    participant_label: str,
    session: str,
    metrics: list,
):
    """[summary]

    Parameters
    ----------
    tensor : Path
        [description]
    derivatives : Path
        [description]
    participant_label : str
        [description]
    session : str
        [description]
    metrics : list
        [description]
    """
    cmd = "tensor2metric"
    flag = []
    for metric in metrics:
        metric_file = TENSOR_METRICS_FILES_TEMPLATE.format(
            dmriprep_dir=derivatives,
            participant_label=participant_label,
            session=session,
            metric=metric.lower(),
        )
        if Path(metric_file).exists():
            flag.append(False)
        else:
            flag.append(True)
        metric = metric.lower()
        cmd += f" -{TENSOR2METRIC_KWARGS_MAPPING.get(metric, metric)} {metric_file}"  # noqa: E501
    cmd += f" {tensor}"
    if any(flag):
        os.system(cmd)


def estimate_tensors(
    parcellations: dict,
    derivatives_dir: Path,
    multi_column: pd.MultiIndex,
):
    """

    Parameters
    ----------
    parcellation_scheme : str
        A string representing a parcellation atlas
    parcellations : dict
        A dictionary with subjects as keys and their corresponding
        *parcellation_scheme* in native space
    derivatives_dir : Path
        Path to derivatives, usually *qsiprep*'s

    Returns
    -------
    [type]
        [description]
    """
    metrics = multi_column.levels[-1]
    for participant_label, image in tqdm.tqdm(parcellations.items()):
        logging.info(
            f"Estimating tensor-derived metrics in subject {participant_label} anatomical space."  # noqa: E501
        )
        for ses in derivatives_dir.glob(f"sub-{participant_label}/ses-*"):
            ses_id = ses.name.split("-")[-1]
            dwi, grad = [
                QSIPREP_DWI_TEMPLATE.format(
                    qsiprep_dir=derivatives_dir,
                    participant_label=participant_label,
                    session=ses_id,
                    extension=extension,
                )
                for extension in ["nii.gz", "b"]
            ]
            tensor = TENSOR_METRICS_FILES_TEMPLATE.format(
                dmriprep_dir=derivatives_dir,
                participant_label=participant_label,
                session=ses_id,
                metric="tensor",
            )
            tensor = dwi2tensor(dwi, grad, Path(tensor))
            tensor2metric(
                tensor, derivatives_dir, participant_label, ses_id, metrics
            )


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
    Parcellate *dmriprep* derived tensor's metrics according to ROI stated by
    *df*.

    Parameters
    ----------
    dmriprep_dir : Path
        Path to *dmriprep* outputs
    multi_column : pd.MultiIndex
        A multi-level column with ROI/tensor metrics combinations
    parcellations : dict
        A dictionary with representing subjects, and values containing paths
        to subjects-space parcellations

    Returns
    -------
    pd.DataFrame
        An updated *df*
    """
    data = pd.DataFrame()
    for participant_label, image in tqdm.tqdm(parcellations.items()):
        logging.info(
            f"Averaging tensor-derived metrics according to {parcellation_scheme} parcels, in subject {participant_label} anatomical space."  # noqa: E501
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
        Whether to use Nearest Neighbout interpolation (for atlas
        registrations)
    invert_xfm : bool, optional
        Whether to invert the transformation file before applying it, by
        default False
    """
    at = ApplyTransforms()
    at.inputs.input_image = in_file
    at.inputs.reference_image = ref
    at.inputs.transforms = xfm
    at.inputs.output_image = str(outfile)
    # if nn:
    #     at.inputs.interpolation = "NearestNeighbor"
    # if invert_xfm:
    #     at.inputs.invert_transform_flags = True
    # if run:
    #     at.run()
    # else:
    #     return at


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
