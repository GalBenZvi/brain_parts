"""
Definition of the :class:`Parcellation` class.
"""
import datetime
import logging
import logging.config
from pathlib import Path

import nibabel as nib
from nilearn.image import resample_to_img
from nipype.interfaces import fsl
from nipype.interfaces.ants import ApplyTransforms

from connecticity.managers.parcellation.atlases import PARCELLATION_FILES
from connecticity.managers.parcellation.utils import LOGGER_CONFIG


class Parcellation:
    #: Default KWARGS
    APPLY_TRANSFORM_KWARGS = dict(interpolation="NearestNeighbor")
    THRESHOLD_KWARGS = dict(direction="below")
    MASKING_KWARGS = dict(output_datatype="int")
    #: Default destination locations
    LOGGER_FILE = "parcellation_{timestamp}.log"

    def __init__(
        self, destination: Path, parcellations: dict = PARCELLATION_FILES
    ) -> None:
        """
        Initiate a Parcellation object

        Parameters
        ----------
        base_dir : Path
            Path to derivatives' base dir (under which there are *dmriprep*,
            *fmriprep*, etc. directories)
        parcellations : dict
            A dictionary with keys of *image* and *parcels* for each required
            parcellation scheme
        """
        self.destination = Path(destination)
        self.parcellations = parcellations
        timestamp = datetime.datetime.today().strftime("%Y-%m-%d-%H:%M:%S")
        logging.basicConfig(
            filename=self.destination
            / self.LOGGER_FILE.format(timestamp=timestamp),
            **LOGGER_CONFIG,
        )

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

    def resmaple_to_image(
        self,
        parcellation_image: Path,
        target_image: Path,
        out_file: Path,
        interpolation: str = "nearest",
        **kwargs,
    ):
        """
        A small wrapper around *nilearn.image.resample_to_img*

        Parameters
        ----------
        parcellation_image : Path
            "source_img" to be resampled
        target_image : Path
            "target_img" to resample to
        out_file : Path
            Output path for resampled image
        interpolation : str, optional
            Interpolation to use, since we mostly deal with parcellation
            images, it's by default "nearest"
        """
        resampled = resample_to_img(
            str(parcellation_image),
            str(target_image),
            interpolation=interpolation,
            **kwargs,
        )
        nib.save(resampled, out_file)

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
