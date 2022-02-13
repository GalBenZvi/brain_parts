import logging
from pathlib import Path
from typing import List

from connectome_plasticity_project.managers.analyses.utils.data_grabber import (
    DataGrabber,
)
from connectome_plasticity_project.managers.analyses.utils.parcellations import (
    PARCELLATIONS,
)
from connectome_plasticity_project.managers.analyses.utils.utils import (
    AnalysisUtils,
)
from connectome_plasticity_project.managers.parcellation.parcellations import (
    Parcellation,
)


class QsiPrepUtils(AnalysisUtils):
    ANALYSIS_TYPE = "qsiprep"
    
    def __init__(
        self,
        base_dir: Path,
        logging_destination: Path,
        parcellations: dict = PARCELLATIONS,
    ) -> None:
        super().__init__(base_dir, self.ANALYSIS_TYPE, parcellations)
        self.parcellation_manager = Parcellation(
            logging_destination, self.parcellations
        )
        self.data_grabber = DataGrabber(
            base_dir, analysis_type=self.ANALYSIS_TYPE
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
