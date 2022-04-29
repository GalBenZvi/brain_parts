"""
Definition of the :class:`Parcellation` class.
"""
import datetime
import logging
import logging.config
import warnings
from pathlib import Path
from typing import Callable

import nibabel as nib
import numpy as np
import pandas as pd
from nipype.interfaces import fsl
from nipype.interfaces.ants import ApplyTransforms

from brain_parts.parcellation.atlases import PARCELLATION_FILES


class Parcellation:
    #: Default KWARGS
    APPLY_TRANSFORM_KWARGS = dict(interpolation="NearestNeighbor")
    THRESHOLD_KWARGS = dict(direction="below")
    MASKING_KWARGS = dict(output_datatype="int")

    def __init__(self, parcellations: dict = PARCELLATION_FILES) -> None:
        """
        Initiate a Parcellation object

        Parameters
        ----------
        parcellations : dict
            A dictionary with keys of *image* and *parcels* for each required
            parcellation scheme
        """
        self.parcellations = parcellations

    def register_parcellation_scheme(
        self,
        parcellation_scheme: str,
        participant_label: str,
        reference: Path,
        mni2native_transform: Path,
        out_whole_brain: Path,
        force: bool = False,
    ):
        """
        Register a parcellation scheme to subjects' anatomical space

        Parameters
        ----------
        analysis_type : str
            A string that represents an available analysis (i.e dmriprep,
            fmriprep, etc.)

        parcellation_scheme : str
            A string representing existing key within *self.parcellations*.
        """
        if out_whole_brain.exists() and not force:
            logging.info(
                f"""{parcellation_scheme} atlas was previously registerted to
                subject {participant_label}'s individual space.\nTo re-run this
                process, pass force=True as a keyword arguement."""
            )
            return

        parcellation_image = self.parcellations.get(parcellation_scheme).get(
            "path"
        )
        logging.info(
            f"Transforming {parcellation_scheme} atlas from standard to subject {participant_label}'s individual space."  # noqa: E501
        )

        runner = ApplyTransforms(
            input_image=parcellation_image,
            reference_image=reference,
            transforms=mni2native_transform,
            output_image=str(out_whole_brain),
            **self.APPLY_TRANSFORM_KWARGS,
        )
        runner.run()

    def crop_to_probseg(
        self,
        parcellation_scheme: str,
        participant_label: str,
        whole_brain: Path,
        probseg: Path,
        out_cropped: Path,
        masking_threshold: float,
        force: bool = False,
    ):
        mask = probseg.with_name(probseg.name.replace("probseg", "mask"))
        if mask.exists() and out_cropped.exists() and not force:
            logging.info(
                f"""{parcellation_scheme} atlas was cropped to subject
                {participant_label}'s gray matter space.\nTo re-run this
                process, pass force=True as a keyword arguement."""
            )
            return
        threshold_runner = fsl.Threshold(
            in_file=probseg,
            thresh=masking_threshold,
            out_file=mask,
            **self.THRESHOLD_KWARGS,
        )
        threshold_runner.run()
        masking_runner = fsl.ApplyMask(
            in_file=whole_brain,
            mask_file=mask,
            out_file=out_cropped,
            **self.MASKING_KWARGS,
        )
        masking_runner.run()

    def parcellate_image(
        self,
        parcellation_scheme: str,
        parcellation_image: Path,
        metric_image: Path,
        metric_name: str = None,
        measure: Callable = np.nanmean,
    ) -> pd.Series:
        """
        Parcellate a metric image according to a *parcellation_scheme* in native-space.

        Parameters
        ----------
        parcellation_scheme : str
            A string representing existing key within *self.parcellations*.
        parcellation_image : Path
            A parcellation image in participantt's native space
        metric_image : Path
            AN image of specific metric to be parcellated
        metric_name : str, optional
            Metric's name, by default None

        Returns
        -------
        pd.Series
            A series of the mean value in each *parcellation_scheme*'s parcel.
        """
        parcellation = self.parcellations.get(parcellation_scheme)
        index, parcels = [
            parcellation.get(key) for key in ["index", "parcels"]
        ]
        metric_name = metric_name or Path(metric_image).name.split(".")[0]
        parcellation_data, metric_data = [
            nib.load(image).get_fdata()
            for image in [parcellation_image, metric_image]
        ]
        result = pd.Series(index=index, name=metric_name, dtype=float)
        for label in parcels["Label"]:
            mask = parcellation_data == label
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=RuntimeWarning)
                result.loc[label] = measure(metric_data[mask].ravel())
        return pd.concat({parcellation_scheme: result}, names=["Atlas"])
