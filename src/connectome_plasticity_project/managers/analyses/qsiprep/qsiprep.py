from pathlib import Path
from typing import List

import nipype.pipeline.engine as pe
import pandas as pd

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
from connectome_plasticity_project.managers.parcellation.workflows.parcellation import (
    init_parcellation_wf,
)


class QsiprepResults(AnalysisResults):
    # Queries
    NATIVE_PARCELLATION_QUERY = pd.MultiIndex.from_product(
        [
            ["anatomical", "epi"],
            ["whole_brain", "gm_masked"],
        ]
    )
    #: Analysis type
    ANALYSIS_TYPE = "qsiprep"

    def __init__(
        self,
        base_dir: Path,
        available_parcellations: dict = PARCELLATIONS,
        work_dir: Path = None,
    ) -> None:
        super().__init__(base_dir)
        self.work_dir = self.initiate_working_directory(work_dir)
        self.data_grabber = DataGrabber(
            base_dir, analysis_type=self.ANALYSIS_TYPE
        )
        self.available_parcellations = available_parcellations
        self.templates = TEMPLATES.get(self.ANALYSIS_TYPE)

    def initiate_working_directory(self, work_dir: Path = None):
        """
        Initiate a working directory for analysis-relevant workflows

        Parameters
        ----------
        work_dir : Path, optional
            Path to a working directory, by default None

        Returns
        -------
        Path
            Path to a working directory to store analysis-relevant workflows
        """
        work_dir = work_dir or self.base_dir.parent / "work"
        work_dir = work_dir / self.ANALYSIS_TYPE
        work_dir.mkdir(exist_ok=True, parents=True)
        return work_dir

    def get_native_parcellation_names(
        self, parcellation_scheme: str, references: dict, reference_type: str
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
            references.get("anatomical_reference"),
            atlas=parcellation_scheme,
            **self.templates.NATIVE_PARCELLATION_NAMING_KWARGS.value.get(
                reference_type
            ),
        )
        gm_cropped = self.data_grabber.build_derivatives_name(
            references.get("anatomical_reference"),
            atlas=parcellation_scheme,
            label="GM",
            **self.templates.NATIVE_PARCELLATION_NAMING_KWARGS.value.get(
                reference_type
            ),
        )
        return whole_brain, gm_cropped

    def register_parcellation_to_individual(
        self,
        parcellation_scheme: str,
        participant_label: str,
        sessions: list,
        prob_mask_threshold: float = None,
        force: bool = False,
        write_graph: bool = True,
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
        write_graph : bool, optional
            Whether to write a graph representing the resulting workflow, by default True

        Returns
        -------
        Path
            Whole-brain parcellation image in subject's anatomical space
        """

        try:
            references, _, _ = self.data_grabber.locate_anatomical_references(
                participant_label, sessions
            )
        except FileNotFoundError:
            return Path(None), Path(None)

    def register_parcellation_to_anatomical(
        self,
        parcellation_scheme: str,
        references: dict,
        participant_label: str,
        prob_mask_threshold: float = None,
        write_graph: bool = True,
    ):
        """
        Register a parcellation atlas to subject's individual (anatomical and EPI) space(s).

        Parameters
        ----------
        parcellation_scheme : str
            A string representing existing key within *self.parcellations*.
        references : dict
            A dictionary containing relevant paths for registration of atlas to subject's anatomical space.
        participant_label : str
            A string representing an available subject in *self.base_dir*
        prob_mask_threshold : float, optional
            Probability masking threshold, by default None
        force : bool, optional
            Whether to perform operation even if output exists, by default False
        write_graph : bool, optional
            Whether to write a graph representing the resulting workflow, by default True

        Returns
        -------
        Path
            Whole-brain parcellation image in subject's anatomical space
        """
        whole_brain, gm_cropped = self.get_native_parcellation_names(
            parcellation_scheme, references, "anatomical"
        )

        parcellation_wf = self.init_parcellation_wf(
            parcellation_scheme,
            participant_label,
            references,
            whole_brain,
            gm_cropped,
            prob_mask_threshold=prob_mask_threshold,
        )
        if write_graph:
            parcellation_wf.write_graph(graph2use="colored")
        return whole_brain, gm_cropped, parcellation_wf

    def register_parcellation_to_epi(
        self,
        parcellation_scheme: str,
        references: dict,
        participant_label: str,
        sessions: list,
        write_graph: bool = True,
    ):
        """
        Register a parcellation atlas to subject's individual (anatomical and EPI) space(s).

        Parameters
        ----------
        parcellation_scheme : str
            A string representing existing key within *self.parcellations*.
        references : dict
            A dictionary containing relevant paths for registration of atlas to subject's anatomical space.
        participant_label : str
            A string representing an available subject in *self.base_dir*
        prob_mask_threshold : float, optional
            Probability masking threshold, by default None
        force : bool, optional
            Whether to perform operation even if output exists, by default False
        write_graph : bool, optional
            Whether to write a graph representing the resulting workflow, by default True

        Returns
        -------
        Path
            Whole-brain parcellation image in subject's anatomical space
        """
        parcellations = {}
        for session in sessions:
            parcellations[session] = {}
            epi_references, _, _ = self.data_grabber.locate_epi_references(
                participant_label, session
            )
            references["anatomical_reference"] = epi_references.get(
                "native_epi_reference"
            )
            whole_brain, gm_cropped = self.get_native_parcellation_names(
                parcellation_scheme, references, "epi"
            )

            parcellation_wf = self.init_parcellation_wf(
                parcellation_scheme,
                participant_label,
                references,
                whole_brain,
                gm_cropped,
                session=session,
                crop_to_gm=False,
            )
            if write_graph:
                parcellation_wf.write_graph(graph2use="colored")
            parcellations[session]["whole_brain"] = whole_brain
            parcellations[session]["gm_cropped"] = gm_cropped
            parcellations[session]["parcellation_wf"] = parcellation_wf
        return parcellations

    def init_parcellation_wf(
        self,
        parcellation_scheme: str,
        participant_label: str,
        references: dict,
        whole_brain: str,
        gm_cropped: str,
        session: str = None,
        crop_to_gm: bool = True,
        prob_mask_threshold: float = None,
    ) -> pe.Workflow:
        """
        Initiate a native parcellation workflow

        Parameters
        ----------
        parcellation_scheme : str
            A string representing existing key within *self.parcellations*.
        participant_label : str
            A string representing an available subject in *self.base_dir*
        references : dict
            A dictionary of participant's anatomical references
        prob_mask_threshold : float, optional
            Probability masking threshold, by default None


        Returns
        -------
        pe.Workflow
            An initiated workflow for native parcellation
        """
        parcellation_file = self.available_parcellations.get(
            parcellation_scheme
        ).get("path")

        if not session:
            wf_name = f"sub-{participant_label}_anatomical_parcellation_wf"
        else:
            wf_name = (
                f"sub-{participant_label}_ses-{session}_epi_parcellation_wf"
            )
        parcellation_wf = init_parcellation_wf(
            wf_name,
            crop_to_gm=crop_to_gm,
        )
        parcellation_wf.base_dir = self.work_dir / participant_label
        parcellation_wf.inputs.inputnode.set(
            out_whole_brain=str(whole_brain),
            out_gm_cropped=str(gm_cropped),
            parcellation_image=parcellation_file,
            probability_masking_threshold=prob_mask_threshold
            or self.PROBSEG_THRESHOLD,
            **references,
        )
        return parcellation_wf

    def get_registered_anatomical_parcellations(
        self,
        parcellation_scheme: str,
        prob_mask_threshold: float = None,
        force: bool = False,
        write_graphs: bool = True,
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
        prob_mask_threshold = prob_mask_threshold or self.PROBSEG_THRESHOLD
        dataset_query = pd.DataFrame(columns=self.NATIVE_PARCELLATION_QUERY)
        for participant_label, sessions in self.subjects.items():
            whole_brain, masked = self.register_parcellation_to_anatomical(
                parcellation_scheme,
                participant_label,
                sessions,
                prob_mask_threshold,
                force,
                write_graphs,
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
