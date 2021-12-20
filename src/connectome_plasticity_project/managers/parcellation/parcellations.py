import datetime
import logging
import logging.config
from pathlib import Path

import pandas as pd

from connectome_plasticity_project.managers.parcellation.utils import (
    DEFAULT_DESTINATION,
)
from connectome_plasticity_project.managers.parcellation.utils import (
    LOGGER_CONFIG,
)
from connectome_plasticity_project.managers.parcellation.utils import (
    PARCELLATIONS,
)
from connectome_plasticity_project.managers.parcellation.utils import at_ants
from connectome_plasticity_project.managers.preprocessing.dmri.utils import (
    TENSOR_METRICS,
)


class Parcellation:
    #: Default output names
    DMRIPREP_NAME = "dmriprep"
    FMRIPREP_NAME = "fmriprep"
    FREESURFER_NAME = "freesurfer"

    #: Dmri tensor-derived metrics
    TENSOR_METRICS = TENSOR_METRICS

    #: Files' templates
    ANATOMICAL_REFERENCE = "sub-{participant_label}*_desc-preproc_T1w.nii.gz"
    MNI_TO_NATIVE_TRANSFORMATION = (
        "sub-{participant_label}*from-MNI*_to-T1w*_xfm.h5"
    )
    #: Default destination locations
    LOGGER_FILE = "parcellation_{timestamp}.log"

    def __init__(
        self,
        base_dir: Path,
        destination: Path = DEFAULT_DESTINATION,
        parcellations: dict = PARCELLATIONS,
    ) -> None:
        """
        Initiate a Parcellation object

        Parameters
        ----------
        base_dir : Path
            Path to derivatives' base dir (under which there are *dmriprep*, *fmriprep*, etc. directories)
        parcellations : dict
            A dictionary with keys of *image* and *parcels* for each required parcellation scheme
        """
        self.base_dir = Path(base_dir)
        self.destination = Path(destination)
        self.parcellations = parcellations
        timestamp = datetime.datetime.today().strftime("%Y-%m-%d-%H:%M:%S")
        logging.basicConfig(
            filename=self.destination
            / self.LOGGER_FILE.format(timestamp=timestamp),
            **LOGGER_CONFIG,
        )

    def locate_outputs(self, analysis_type: str) -> Path:
        """
        Locates output directories under *self.base_dir*

        Parameters
        ----------
        analysis_type : str
            A string that represents an available analysis (i.e dmriprep, fmriprep, etc.)

        Returns
        -------
        Path
            Path to the corresponding output directory under *self.base_dir*
        """
        destination = self.base_dir / getattr(
            self, f"{analysis_type.upper()}_NAME"
        )
        if not destination.exists():
            logging.warn(
                f"Could not locate {analysis_type} outputs under {destination}."
            )
        return destination

    def locate_anatomical_reference(
        self, subject_dir: Path, participant_label: str
    ):
        """
        Locates subjects' preprocessed anatomical reference

        Parameters
        ----------
        output_dir : Path
            An output (derivatives) directort of either *fmriprep* or *dmriprep*
        """
        anat_dir = subject_dir / "anat"
        if not anat_dir.exists():
            try:
                anat_dir = [d for d in subject_dir.glob("ses-*/anat")][0]
            except IndexError:
                logging.warn(
                    f"Could not locate anatomical reference for subject {participant_label}."
                )
                return
        reference = [
            f
            for f in anat_dir.glob(
                self.ANATOMICAL_REFERENCE.format(
                    participant_label=participant_label
                )
            )
        ][0]
        transformation = [
            f
            for f in anat_dir.glob(
                self.MNI_TO_NATIVE_TRANSFORMATION.format(
                    participant_label=participant_label
                )
            )
        ][0]
        return reference, transformation

    def register_parcellation_scheme(
        self, analysis_type: str, parcellation_scheme: str
    ):
        """
        Register a parcellation scheme to subjects' anatomical space

        Parameters
        ----------
        parcellation_scheme : str
            A string representing existing key within *self.parcellations*.
        """
        output_dir = self.locate_outputs(analysis_type)
        in_file = self.parcellations.get(parcellation_scheme).get("path")
        subjects_parcellations = {}
        for subject_dir in output_dir.glob("sub-*"):
            participant_label = subject_dir.name.split("-")[-1]
            reference, transformation = self.locate_anatomical_reference(
                subject_dir, participant_label
            )
            out_file = reference.with_name(
                reference.name.replace(
                    "desc-preproc_T1w",
                    f"space-anat_atlas-{parcellation_scheme}",
                )
            )
            subjects_parcellations[participant_label] = out_file
            if not out_file.exists():
                logging.info(
                    f"Transforming {parcellation_scheme} atlas from standard to subject {participant_label}'s anatomical space."
                )
                at_ants(in_file, reference, transformation, out_file, nn=True)
        return subjects_parcellations

    def collect_tensors_metrics(self, parcellation_scheme: str):
        """
        Parcellates tensor-derived metrics according to *parcellation_scheme*

        Parameters
        ----------
        parcellation_scheme : str
            A string representing existing key within *self.parcellations*.
        """
        destination = self.destination / "dmri_tensors"
        destination.mkdir(exist_ok=True, parents=True)
        image, parcels = [
            self.parcellations.get(parcellation_scheme).get(key)
            for key in ["image", "parcels"]
        ]
        subjects = [
            s.name.split("-")[-1]
            for s in sorted(self.dmriprep_dir.glob("sub-*"))
        ]
        multi_column = pd.MultiIndex.from_product(
            [parcels.index, self.TENSOR_METRICS]
        )
        df = pd.DataFrame(index=subjects, columns=multi_column)

    @property
    def dmriprep_dir(self) -> Path:
        """
        Locates the location of *dmriprep* outputs under *self.base_dir*

        Returns
        -------
        Path
            *dmriprep* outputs' directory.
        """
        return self.locate_outputs("dmriprep")

    @property
    def fmriprep_dir(self) -> Path:
        """
        Locates the location of *fmriprep* outputs under *self.base_dir*

        Returns
        -------
        Path
            *fmriprep* outputs' directory.
        """
        return self.locate_outputs("fmriprep")

    @property
    def freesurfer_dir(self) -> Path:
        """
        Locates the location of *freesurfer* outputs under *self.base_dir*

        Returns
        -------
        Path
            *freesurfer* outputs' directory.
        """
        return self.locate_outputs("freesurfer")
