import json
import logging
import os
from pathlib import Path

import pandas as pd

REPLACEMENT_COLUMNS = {
    "mri_table": {
        "ID": "id",
        "Questionnaire": "questionnaire_id",
        "Height": "height",
        "Weight": "weight",
        "Gender": "gender",
    },
    "database": {
        "ID": "database_id",
        "First Name": "first name",
        "Last Name": "last name",
        "Sex": "sex",
        "Date Of Birth": "dob",
        "Dominant Hand": "dominant hand",
    },
}

SUMMARY_MESSAGE = """
Found {num_valid} available subjects and {num_missing} ones.
Valids subjects' table can be found at {destination}/valid.csv.
Missing subjects' table can be found at {destination}/missing.csv.
"""


def transform_row(
    row: pd.Series,
    origin: str = "mri_table",
    replacements: dict = REPLACEMENT_COLUMNS,
) -> pd.Series:
    """
    Replaces columns according to *replacements*

    Parameters
    ----------
    row : pd.Series
        A row to be transformed
    replacements : dict, optional
        Replacements dictionary, containing columns from *row*, by default REPLACEMENT_COLUMNS

    Returns
    -------
    pd.Series
        A transformed series.
    """
    replacements = replacements.get(origin)
    transformed_row = row[[key for key in replacements.keys()]]
    transformed_row.index = [val for val in replacements.values()]
    return transformed_row


def clean_dwi(ses_dir: Path):
    """
    Delete multiple DWI series due to an error occurd in the past

    Parameters
    ----------
    ses_dir : Path
        A row to be transformed
    """
    dwi_imgs = [f for f in ses_dir.glob("dwi/*dir-FWD*run-*_dwi.nii.gz")]
    if len(dwi_imgs) > 1:
        logging.info(
            f"Found {len(dwi_imgs) - 1} DWI series images to be removed"
        )
        for dwi_img in dwi_imgs:
            template = dwi_img.name.split(".")[0]
            dwi_associated_files = [
                f for f in ses_dir.glob(f"dwi/{template}*")
            ]
            for dwi in dwi_associated_files:
                if "run-1" not in dwi.name:
                    dwi.unlink()
                else:
                    os.rename(
                        dwi, dwi.with_name(dwi.name.replace("_run-1", ""))
                    )


def fix_session(ses_dir: Path):
    """
    Perform several pre-defined issues with BIDS sturcture

    Parameters
    ----------
    ses_dir : Path
        Path to subject's session to be quaried and fixed.
    """
    clean_irepi(ses_dir)
    funcs = fix_naturalistic_func(ses_dir)
    update_func_fmap_json(ses_dir, funcs)
    clean_dwi(ses_dir)
    update_dwi_fmap_json(ses_dir)


def clean_irepi(ses_dir: Path):
    """
    Remove irrelavent IR-EPI sequences.

    Parameters
    ----------
    ses_dir : Path
        Path to subject's session to be quaried and fixed.
    """
    irepi = [f for f in ses_dir.glob("anat/*IRT1.*")]
    if irepi:
        logging.info(f"Found {len(irepi)} IR-EPI images to be removed")
        for i in irepi:
            i.unlink()


def fix_naturalistic_func(ses_dir: Path) -> list:
    """[summary]

    Parameters
    ----------
    ses_dir : Path
        Path to subject's session to be quaried and fixed.

    Returns
    -------
    list
        List of Paths representing subject's funcitonal images.
    """
    func_imgs = [f for f in ses_dir.glob("func/*")]
    if len(func_imgs) != 4:
        functionals = []
        logging.info(
            f"Found {len(func_imgs)} functional images to be renamed."
        )
        for f in func_imgs:
            parts = f.name.split("_")
            task = f.name.split("_")[-3]
            new_task = task.replace("Ap", "").replace("Sbref", "")
            parts[-3] = new_task
            new_name = "_".join(parts)
            new_f = f.parent / new_name
            os.rename(f, new_f)
            functionals.append(new_f)
        return functionals


def update_func_fmap_json(ses_dir: Path, funcs: list):
    """
    Update functional fieldmaps to account for changed functional images in *funcs*

    Parameters
    ----------
    ses_dir : Path
        Path to subject's session to be quaried and fixed.
    funcs : list
        List of Paths representing subject's funcitonal images.
    """
    if not funcs:
        return
    fmap_jsons = [f for f in ses_dir.glob("fmap/*acq-func*.json")]
    if not fmap_jsons:
        logging.warn(
            f"No fMRI-related fieldmap file found for subject {ses_dir.parent.name}!"
        )
        return
    for fmap_json in fmap_jsons:
        with open(str(fmap_json), "r+") as f:
            data = json.load(f)
            data["IntendedFor"] = list(
                set(
                    [
                        f"{ses_dir.name}/func/{i.name}"
                        for i in funcs
                        if str(i).endswith(".nii.gz")
                    ]
                )
            )
            f.seek(0)
            json.dump(data, f, indent=4)
            f.truncate()
            f.close()


def update_dwi_fmap_json(ses_dir: Path):
    """
    Update functional fieldmaps to account for changed functional images in *funcs*

    Parameters
    ----------
    ses_dir : Path
        Path to subject's session to be quaried and fixed.
    funcs : list
        List of Paths representing subject's funcitonal images.
    """
    dwis = [f for f in ses_dir.glob("dwi/*.nii.gz")]
    fmap_jsons = [f for f in ses_dir.glob("fmap/*acq-dwi*.json")]
    if not fmap_jsons:
        logging.warn(
            f"No diffusion-related fieldmap file found for subject {ses_dir.parent.name}!"
        )
        return
    for fmap_json in fmap_jsons:
        with open(str(fmap_json), "r+") as f:
            data = json.load(f)
            data["IntendedFor"] = list(
                set(
                    [
                        f"{ses_dir.name}/func/{i.name}"
                        for i in dwis
                        if str(i).endswith(".nii.gz")
                    ]
                )
            )
            f.seek(0)
            json.dump(data, f, indent=4)
            f.truncate()
            f.close()
