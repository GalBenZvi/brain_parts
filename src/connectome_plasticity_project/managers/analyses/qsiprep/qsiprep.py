import logging
import logging.config
from pathlib import Path
from typing import List

import nipype.pipeline.engine as pe
import pandas as pd
import tqdm

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
    TEMPLATES,
)
from connectome_plasticity_project.managers.analyses.utils.utils import (
    DEFAULT_DESTINATION,
)
from connectome_plasticity_project.managers.parcellation.parcellations import (
    Parcellation,
)


class QsiprepResults(AnalysisResults):
    # Queries
    NATIVE_PARCELLATION_QUERY = ["anat", "epi"]
    LOGGING_DESTINATION = DEFAULT_DESTINATION
    LOGGER_FILE = "parcellation_{timestamp}.log"
    #: Analysis type
    ANALYSIS_TYPE = "qsiprep"

    def __init__(
        self,
        base_dir: Path,
        available_parcellations: dict = PARCELLATIONS,
    ) -> None:
        super().__init__(base_dir)
        self.data_grabber = DataGrabber(
            base_dir, analysis_type=self.ANALYSIS_TYPE
        )
        self.logging_destination = Path(
            self.LOGGING_DESTINATION.format(analysis_type=self.ANALYSIS_TYPE)
        )
        self.available_parcellations = available_parcellations
        self.templates = TEMPLATES.get(self.ANALYSIS_TYPE)
        self.parcellation_manager = Parcellation(
            self.logging_destination, self.available_parcellations
        )

    def get_native_parcellation_names(
        self, parcellation_scheme: str, reference: Path, reference_type: str
    ) -> List[Path]:
        """
        Construct native parcellation scheme's file names according to given inputs *references*.

        Parameters
        ----------
        parcellation_scheme : str
            A string representing existing key within *self.parcellations*.
        references : dict
            A dictionary containing relevant paths for registration of atlas to subject's individual space.
        reference_type : str
            A string of either "anatomical" or "epi", representing the type of reference in subject's space.
        Returns
        -------
        List[Path]
            Path to whole-brain a GM-cropped parcellation schemes in subject's individual space.
        """
        whole_brain = self.data_grabber.build_derivatives_name(
            reference,
            atlas=parcellation_scheme,
            **self.templates.NATIVE_PARCELLATION_NAMING_KWARGS.value.get(
                reference_type
            ),
        )
        gm_cropped = self.data_grabber.build_derivatives_name(
            reference,
            atlas=parcellation_scheme,
            label="GM",
            **self.templates.NATIVE_PARCELLATION_NAMING_KWARGS.value.get(
                reference_type
            ),
        )
        return whole_brain, gm_cropped

    def register_parcellation_scheme(
        self,
        parcellation_scheme: str,
        participant_label: str,
        sessions: list,
        prob_mask_threshold: float = None,
        force: bool = False,
    ) -> Path:
        """
        Register a parcellation atlas to subject's individual (anatomical and EPI) space(s).

        Parameters
        ----------
        parcellation_scheme : str
            A string representing existing key within *self.parcellations*.
        participant_label : str
            A string representing an available subject in *self.base_dir*
        sessions : list
            A list of available sessions for *participant_label*
        prob_mask_threshold : float, optional
            Probability masking threshold, by default None
        force : bool, optional
            Whether to perform operation even if output exists, by default False

        Returns
        -------
        Tuple[bool,bool]
            Whether registration of atlas to anatomical and EPI (accordingly) spaces was successful
        """
        anat = self.register_parcellation_to_anatomical(
            parcellation_scheme,
            participant_label,
            sessions,
            prob_mask_threshold,
            force,
        )
        if anat:
            epi = self.register_parcellation_to_epi(
                parcellation_scheme, participant_label, sessions, force
            )
        else:
            epi = False
        return anat, epi

    def register_parcellation_to_anatomical(
        self,
        parcellation_scheme: str,
        participant_label: str,
        sessions: list,
        prob_mask_threshold: float = None,
        force: bool = False,
    ) -> bool:
        """
        Register *parcellation_scheme* to *participant_label*'s anatomical space, and crop to gray matter.

        Parameters
        ----------
        parcellation_scheme : str
            A string representing existing key within *self.parcellations*.
        participant_label : str
            A string representing an available subject in *self.base_dir*
        sessions : list
            A list of available sessions for *participant_label*
        prob_mask_threshold : float, optional
            Probability masking threshold, by default None
        force : bool, optional
            Whether to perform operation even if output exists, by default False

        Returns
        -------
        bool
            Whether registration was successful
        """
        try:
            references, _, _ = self.data_grabber.locate_anatomical_references(
                participant_label, sessions
            )
        except FileNotFoundError:
            logging.warning(
                f"""Found missing required files for participant {participant_label}. 
            Can't register parcellation to its native space."""
            )
            return False
        prob_mask_threshold = prob_mask_threshold or self.PROBSEG_THRESHOLD
        reference, mni2native_transform, probseg = [
            references.get(key.lower())
            for key in self.templates.ANATOMICAL_TEMPLATES.value
        ]
        whole_brain, gm_cropped = self.get_native_parcellation_names(
            parcellation_scheme,
            references.get("anatomical_reference"),
            "anatomical",
        )
        self.parcellation_manager.register_parcellation_scheme(
            parcellation_scheme,
            participant_label,
            reference,
            mni2native_transform,
            whole_brain,
            force,
        )
        self.parcellation_manager.crop_to_probseg(
            parcellation_scheme,
            participant_label,
            whole_brain,
            probseg,
            gm_cropped,
            prob_mask_threshold,
            force,
        )
        return True

    def register_parcellation_to_epi(
        self,
        parcellation_scheme: str,
        participant_label: str,
        sessions: list,
        force: bool = False,
    ) -> bool:
        """
        Register *parcellation_scheme* to *participant_label*'s EPI space

        Parameters
        ----------
        parcellation_scheme : str
            A string representing existing key within *self.parcellations*.
        participant_label : str
            A string representing an available subject in *self.base_dir*
        sessions : list
            A list of available sessions for *participant_label*
        force : bool, optional
            Whether to perform operation even if output exists, by default False

        Returns
        -------
        bool
            Whether registration was successful
        """
        (
            anatomical_references,
            _,
            _,
        ) = self.data_grabber.locate_anatomical_references(
            participant_label, sessions
        )
        for session in sessions:
            try:
                reference, _, _ = self.data_grabber.locate_epi_references(
                    participant_label, session
                )
            except FileNotFoundError:
                logging.warning(
                    f"""Found missing required files for participant {participant_label}. 
                Can't register parcellation to its native space."""
                )
                return False
            reference = reference.get("native_epi_reference")
            mni2native_transform = anatomical_references.get(
                "mni_to_native_transformation"
            )

            whole_brain, _ = self.get_native_parcellation_names(
                parcellation_scheme,
                reference,
                "epi",
            )
            self.parcellation_manager.register_parcellation_scheme(
                parcellation_scheme,
                participant_label,
                reference,
                mni2native_transform,
                whole_brain,
                force,
            )
        return True

    def get_registered_anatomical_parcellations(
        self,
        parcellation_scheme: str,
        prob_mask_threshold: float = None,
        force: bool = False,
    ):
        """
        Register a parcellation scheme to subjects' anatomical space

        Parameters
        ----------
        parcellation_scheme : str
            A string representing existing key within *self.parcellations*.
        """
        dataset_query = pd.DataFrame(columns=self.NATIVE_PARCELLATION_QUERY)
        for participant_label, sessions in tqdm.tqdm(self.subjects.items()):
            epi, anat = self.register_parcellation_scheme(
                parcellation_scheme,
                participant_label,
                sessions,
                prob_mask_threshold,
                force,
            )
            for flag, key in zip([anat, epi], ["anat", "epi"]):
                dataset_query.loc[
                    participant_label,
                    key,
                ] = flag
        return dataset_query

    # def to_dataframe(
    #     self,
    #     parcellation_scheme: str,
    #     cropped_to_gm: bool = True,
    #     force: bool = False,
    #     np_operation: str = "nanmean",
    # ) -> pd.DataFrame:
    #     """Parcellates tensor-derived metrics according to *parcellation_scheme*

    #     Parameters
    #     ----------
    #     parcellation_scheme : str
    #         A string representing existing key within *self.parcellations*.

    #     Returns
    #     -------
    #     pd.DataFrame
    #         A dictionary with representing subjects, and values containing paths to subjects-space parcellations.
    #     """
    #     parcels = self.parcellations.get(parcellation_scheme).get("parcels")
    #     parcellations = self.register_parcellation_scheme(
    #         analysis_type, parcellation_scheme, cropped_to_gm
    #     )
    #     multi_column = pd.MultiIndex.from_product(
    #         [parcels.index, self.TENSOR_METRICS]
    #     )
    #     if analysis_type == "qsiprep":
    #         estimate_tensors(parcellations, self.qsiprep_dir, multi_column)
    #     return parcellate_tensors(
    #         self.locate_outputs(analysis_type),
    #         multi_column,
    #         parcellations,
    #         parcels,
    #         parcellation_scheme,
    #         cropped_to_gm,
    #         force,
    #         np_operation,
    #     )
