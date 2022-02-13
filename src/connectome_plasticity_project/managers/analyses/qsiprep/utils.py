import logging
from pathlib import Path
from typing import List

import nipype.pipeline.engine as pe

from connectome_plasticity_project.managers.analyses.qsiprep.workflows.tensors.tensor_estimation import (
    init_tensor_wf,
)
from connectome_plasticity_project.managers.analyses.utils.data_grabber import (
    DataGrabber,
)
from connectome_plasticity_project.managers.analyses.utils.parcellations import (
    PARCELLATIONS,
)
from connectome_plasticity_project.managers.analyses.utils.templates import (
    TENSOR_DERIVED_METRICS,
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
        self.logging_destination = logging_destination

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

    def reset_derivatives_base(
        self, wf: pe.Workflow, new_path_base: str = None
    ) -> pe.Workflow:
        """
        Reset's *wf*'s *DerivativesDataSink* base to *new_path_base*

        Parameters
        ----------
        wf : pe.Workflow
            A workflow that includes DerivativesDataSink
        new_path_base : str, optional
            New base path for sinking, by default None

        Returns
        -------
        pe.Workflow
            A workflow with DerivativesDataSink pointing to *new_path_base* as destination.
        """
        for node in wf.list_node_names():
            if node.split(".")[-1].startswith("ds_"):
                wf.get_node(node).interface.out_path_base = (
                    new_path_base or self.ANALYSIS_TYPE
                )
        return wf

    def locate_precomputed_tensors(
        self, participant_label: str, session: str
    ) -> dict:
        """
        Locates precomputed tensor-derived metrics to avoid unneccesary computations

        Parameters
        ----------
        participant_label : str
            A string representing an available subject in *self.base_dir*
        session : str
            An available sessions for *participant_label*

        Returns
        -------
        dict
            A dictionary with "description" and "exists" keys for each tensor-derived metrics.
        """
        computed = {}
        for key, value in TENSOR_DERIVED_METRICS.items():
            computed[key] = {}
            computed[key]["description"] = value
            _, dwi_dir, prefix = self.data_grabber.locate_epi_references(
                participant_label, session
            )
            exists = self.data_grabber.search_for_file(
                dwi_dir, f"{prefix}*desc-{key}*.nii.gz", raise_not_found=False
            )
            computed[key]["exists"] = True if exists else False
        return computed

    def estimate_tensor_metrics(
        self,
        base_directory: Path,
        participant_label: str,
        sessions: list,
        work_dir: Path,
        path_base: str = None,
    ):
        """
        Initiates and runs a tensor estimation workflow for all available *sessions* under for *participant_label*

        Parameters
        ----------
        base_directory : Path
            A directory to store all derivatives of tensor estimation workflow
        participant_label : str
            A string representing an available subject in *self.base_dir*
        sessions : list
            A list of available sessions for *participant_label*
        work_dir : Path
            A working directory to store all initiated workflow's sub-derivatives
        path_base : str, optional
            Path base for DerivativesDataSink, by default None
        """
        work_dir = work_dir / f"sub-{participant_label}"
        work_dir.mkdir(exist_ok=True)
        # base_wf = init_tensor_wf()
        for session in sessions:
            computed = self.locate_precomputed_tensors(
                participant_label, session
            )
            if not all([key["exists"] for key in computed.values()]):
                references, _, _ = self.data_grabber.locate_epi_references(
                    participant_label, session
                )
                dwi_file = references.get("native_epi_reference")
                grad_file = dwi_file.with_name(
                    dwi_file.name.split(".")[0] + ".b"
                )
                wf = init_tensor_wf(f"ses-{session}_tensor_estimation_wf")
                wf.inputs.inputnode.set(
                    base_directory=base_directory,
                    dwi_file=dwi_file,
                    grad_file=grad_file,
                )
                wf.base_dir = work_dir
                wf = self.reset_derivatives_base(wf, path_base)
                wf.config["logging"]["log_to_file"] = self.logging_destination
                wf.run()
                del wf
