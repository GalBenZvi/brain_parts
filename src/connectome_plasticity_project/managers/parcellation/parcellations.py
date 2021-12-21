import datetime
import logging
import logging.config
import os
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
from connectome_plasticity_project.managers.parcellation.utils import (
    freesurfer_anatomical_parcellation,
)
from connectome_plasticity_project.managers.parcellation.utils import (
    parcellate_tensors,
)
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
        reference = transformation = None
        valid = True
        if not anat_dir.exists():
            try:
                anat_dir = [d for d in subject_dir.glob("ses-*/anat")][0]
            except IndexError:
                valid = False
        try:
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
        except IndexError:
            valid = False
        return reference, transformation, valid

    def register_parcellation_scheme(
        self, analysis_type: str, parcellation_scheme: str
    ):
        """
        Register a parcellation scheme to subjects' anatomical space

        Parameters
        ----------
        analysis_type : str
            A string that represents an available analysis (i.e dmriprep, fmriprep, etc.)

        parcellation_scheme : str
            A string representing existing key within *self.parcellations*.
        """
        output_dir = self.locate_outputs(analysis_type)
        in_file = self.parcellations.get(parcellation_scheme).get("path")
        subjects_parcellations = {}
        for subject_dir in output_dir.glob("sub-*"):
            participant_label = subject_dir.name.split("-")[-1]
            (
                reference,
                transformation,
                valid,
            ) = self.locate_anatomical_reference(
                subject_dir, participant_label
            )
            if not valid:
                logging.warn(
                    f"Could not locate anatomical reference for subject {participant_label}."
                )
                continue
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

    def generate_freesurfer_metrics(self, parcellation_scheme: str):
        """
        mris_ca_label -sdir ../../freesurfer/ sub-14 lh surf/lh.sphere.reg /media/groot/Data/Parcellations/MNI/Brainnetome_FS/lh.BN_Atlas.gcs lh.bn.annot
        mris_anatomical_stats -a label/lh.bn.annot -b sub-14 lh



        Parameters
        ----------
        parcellation_scheme : str
            A string representing existing key within *self.parcellations*.
        """
        gcs = self.parcellations.get(parcellation_scheme).get("gcs")
        if not gcs:
            raise (
                f"No available Freesurfer .gcs file located for parcellation scheme {parcellation_scheme}!"
            )
        for subj in self.freesurfer_dir.glob("sub-*"):
            stats = freesurfer_anatomical_parcellation(
                self.freesurfer_dir, subj.name, parcellation_scheme, gcs
            )

    def collect_tensors_metrics(
        self, parcellation_scheme: str
    ) -> pd.DataFrame:
        """Parcellates tensor-derived metrics according to *parcellation_scheme*

        Parameters
        ----------
        parcellation_scheme : str
            A string representing existing key within *self.parcellations*.

        Returns
        -------
        pd.DataFrame
            A dictionary with representing subjects, and values containing paths to subjects-space parcellations.
        """
        parcels = self.parcellations.get(parcellation_scheme).get("parcels")
        parcellations = self.register_parcellation_scheme(
            "dmriprep", parcellation_scheme
        )
        multi_column = pd.MultiIndex.from_product(
            [parcels.index, self.TENSOR_METRICS]
        )
        return parcellate_tensors(
            self.dmriprep_dir,
            multi_column,
            parcellations,
            parcels,
            parcellation_scheme,
        )

    def run_all(self, parcellation_scheme: str):
        """
        Run all available parcellation methods

        Parameters
        ----------
        parcellation_scheme : str
            Parcellation scheme representing an existing key in *self.parcellations*
        """
        target = self.destination / parcellation_scheme
        for out_file, function in zip(
            ["dmri/tensors.csv"], [self.collect_tensors_metrics]
        ):
            data = function(parcellation_scheme)
            destination = target / out_file
            destination.parent.mkdir(exist_ok=True, parents=True)
            data.to_csv(destination)

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
        freesurfer_dir = self.locate_outputs("freesurfer")
        if freesurfer_dir.exists():
            os.system("export SUBJECTS_DIR={freesurfer_dir}")
        return freesurfer_dir
