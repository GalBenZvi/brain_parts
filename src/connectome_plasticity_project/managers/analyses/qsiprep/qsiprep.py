from pathlib import Path

import pandas as pd
from cv2 import threshold

from connectome_plasticity_project.managers.analyses.analysis import (
    AnalysisResults,
)
from connectome_plasticity_project.managers.analyses.utils.data_grabber import (
    DataGrabber,
)
from connectome_plasticity_project.managers.analyses.utils.parcellations import (
    PARCELLATIONS,
)
from connectome_plasticity_project.managers.analyses.utils.templates import (
    generate_atlas_file_name,
)
from connectome_plasticity_project.managers.analyses.utils.utils import (
    apply_mask,
)
from connectome_plasticity_project.managers.analyses.utils.utils import at_ants
from connectome_plasticity_project.managers.analyses.utils.utils import (
    binarize_image,
)


class QsiprepResults(AnalysisResults):
    # Queries
    NATIVE_PARCELLATION_QUERY = pd.MultiIndex.from_product(
        [
            ["anatomical", "epi"],
            ["whole_brain", "gm_masked"],
        ]
    )

    def __init__(
        self,
        base_dir: Path,
        available_parcellations: dict = PARCELLATIONS,
    ) -> None:
        super().__init__(base_dir)
        self.data_grabber = DataGrabber(base_dir, analysis_type="qsiprep")
        self.available_parcellations = available_parcellations

    def register_parcellation_to_anatomical(
        self,
        parcellation_scheme: str,
        participant_label: str,
        sessions: list,
        force: bool = False,
    ) -> Path:
        """
        Register a parcellation atlas to subject's anatomical space

        Parameters
        ----------
        parcellation_scheme : str
            A string representing existing key within *self.parcellations*.
        parcellation_file : Path
            Path to a labeled image of *parcellation_scheme*
        participant_label : str
            A string representing an available subject in *self.base_dir*
        sessions : list
            A list of available sessions for *participant_label*
        force : bool, optional
            Whether to perform operation even if output exists, by default False

        Returns
        -------
        Path
            Whole-brain parcellation image in subject's anatomical space
        """
        parcellation_file = self.available_parcellations.get(
            parcellation_scheme
        ).get("path")
        references, _, _ = self.data_grabber.locate_anatomical_references(
            participant_label, sessions
        )
        whole_brain = self.data_grabber.build_parcellation_naming(
            parcellation_scheme, references
        )
        at_ants(
            in_file=parcellation_file,
            ref=references.get("anatomical_reference"),
            xfm=references.get("mni_to_native_transformation"),
            out_file=whole_brain,
            args=self.TRANSFORM_KWARGS,
            force=force,
        )
        gm_masked = self.crop_parcellation_to_gm(
            parcellation_scheme, whole_brain, references, force=force
        )
        return whole_brain, gm_masked

    def crop_parcellation_to_gm(
        self,
        parcellation_scheme: str,
        whole_brain: Path,
        references: dict,
        force: bool = False,
    ) -> Path:
        """
        Masks a whole-brain parcellation image to gray matter according to pre-calculated probabilistic segmentation.

        Parameters
        ----------
        parcellation_scheme : str
            A string representing existing key within *self.parcellations*.
        whole_brain : Path
            Whole-brain parcellation image in subject's anatomical space
        references : dict
            Subject-specific anatomical references
        force : bool, optional
            Whether to perform operation even if output exists, by default False

        Returns
        -------
        Path
            Path to gray-matter-masked parcellation atlas in subject's anatomical space.
        """
        gm_probabilsitic = references.get("gm_probability")
        gm_mask = gm_probabilsitic.with_name(
            gm_probabilsitic.name.replace("probseg", "mask")
        )
        binarize_image(
            gm_probabilsitic,
            gm_mask,
            threshold=self.PROBSEG_THRESHOLD,
            force=force,
        )
        masked_image = self.data_grabber.build_parcellation_naming(
            parcellation_scheme, references, label="GM"
        )
        apply_mask(
            whole_brain,
            gm_mask,
            masked_image,
            args=self.MASKER_KWARGS,
            force=force,
        )
        return masked_image

    def get_registered_anatomical_parcellations(
        self,
        parcellation_scheme: str,
        force: bool = False,
    ):
        """
        Register a parcellation scheme to subjects' anatomical space

        Parameters
        ----------
        parcellation_scheme : str
            A string representing existing key within *self.parcellations*.
        crop_to_gm : bool, optional
            Whether to crop the resulting register parcellation atlas to gray matter, by default True
        """
        dataset_query = pd.DataFrame(columns=self.NATIVE_PARCELLATION_QUERY)
        for participant_label, sessions in self.subjects.items():
            whole_brain, masked = self.register_parcellation_to_anatomical(
                parcellation_scheme, participant_label, sessions, force
            )
            for file, key in zip(
                [whole_brain, masked], ["whole_brain", "gm_masked"]
            ):

                if file.exists():
                    dataset_query.loc[
                        participant_label,
                        ("anatomical", key),
                    ] = True
        return dataset_query

    def to_dataframe(
        self,
        parcellation_scheme: str,
        cropped_to_gm: bool = True,
        force: bool = False,
        np_operation: str = "nanmean",
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
            analysis_type, parcellation_scheme, cropped_to_gm
        )
        multi_column = pd.MultiIndex.from_product(
            [parcels.index, self.TENSOR_METRICS]
        )
        if analysis_type == "qsiprep":
            estimate_tensors(parcellations, self.qsiprep_dir, multi_column)
        return parcellate_tensors(
            self.locate_outputs(analysis_type),
            multi_column,
            parcellations,
            parcels,
            parcellation_scheme,
            cropped_to_gm,
            force,
            np_operation,
        )
