import logging
import logging.config
from pathlib import Path
from typing import List

import pandas as pd
import tqdm

from connecticity.managers.analyses.analysis import (
    AnalysisResults,
)
from connecticity.managers.analyses.qsiprep.utils import (
    QsiPrepUtils,
)
from connecticity.managers.analyses.utils.parcellations import (
    PARCELLATIONS,
)
from connecticity.managers.analyses.utils.templates import (
    TENSOR_DERIVED_METRICS,
)
from connecticity.managers.analyses.utils.utils import (
    DEFAULT_DESTINATION,
)


class QsiprepResults(AnalysisResults):
    # Queries
    NATIVE_PARCELLATION_QUERY = ["anat", "epi"]
    LOGGING_DESTINATION = DEFAULT_DESTINATION
    LOGGER_FILE = "parcellation_{timestamp}.log"

    #: Analysis type
    ANALYSIS_TYPE = "qsiprep"

    #: Workflows
    TENSOR_ESTIMATION_NAME = "tensor_estimation"

    def __init__(
        self,
        base_dir: Path,
        work_dir: Path = None,
        available_parcellations: dict = PARCELLATIONS,
    ) -> None:
        super().__init__(base_dir)
        self.logging_destination = Path(
            self.LOGGING_DESTINATION.format(analysis_type=self.ANALYSIS_TYPE)
        )
        self.utils = QsiPrepUtils(
            base_dir, self.logging_destination, available_parcellations
        )
        self.work_dir = work_dir or self.base_dir.parent.parent / "work"

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
        prob_mask_threshold = prob_mask_threshold or self.PROBSEG_THRESHOLD
        anat = self.utils.register_parcellation_to_anatomical(
            parcellation_scheme,
            participant_label,
            sessions,
            prob_mask_threshold,
            force=force,
        )
        if anat:
            epi = self.utils.register_parcellation_to_epi(
                parcellation_scheme, participant_label, sessions, force=force
            )
        else:
            epi = False
        return anat, epi

    def get_registered_parcellations(
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
                force=force,
            )
            for flag, key in zip([anat, epi], ["anat", "epi"]):
                dataset_query.loc[
                    participant_label,
                    key,
                ] = flag
        return dataset_query

    def get_tensor_work_directory(self) -> Path:
        """
        Initiates a working directory to store all tensor estimation workflows.

        Returns
        -------
        Path
            Path to a working directory
        """
        work_dir = self.work_dir / self.TENSOR_ESTIMATION_NAME
        work_dir.mkdir(exist_ok=True, parents=True)
        return work_dir

    def estimate_tensor_metrics(self):
        """
        Performs tensor estimation and metrics' computation for all available subjects.
        """
        for participant_label, sessions in tqdm.tqdm(self.subjects.items()):
            self.utils.estimate_tensor_metrics(
                self.base_dir.parent,
                participant_label,
                sessions,
                self.tensor_work_directory,
            )

    def collect_additional_derivatives(
        self,
        parcellation_scheme: str = "brainnetome",
        prob_mask_threshold: float = None,
        force: bool = False,
    ):
        """
        Collects all additional derivatives for *qsiprep*, including registered-to-native *parcellation_scheme* and tensor-derived metrics.

        Parameters
        ----------
        parcellation_scheme : str, optional
            A string representing existing key within *self.parcellations*., by default "brainnetome"
        prob_mask_threshold : float, optional
            Probability masking threshold, by default None
        force : bool, optional
            Whether to perform operation even if output exists, by default False
        """

        q = self.get_registered_parcellations(
            parcellation_scheme, prob_mask_threshold, force=force
        )
        self.estimate_tensor_metrics()

    def to_dataframe(
        self,
        parcellation_scheme: str,
        cropped_to_gm: bool = False,
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
        parcels = self.available_parcellations.get(parcellation_scheme).get(
            "parcels"
        )
        multi_column = pd.MultiIndex.from_product(
            [parcels.index, TENSOR_DERIVED_METRICS.keys()]
        )
        data = pd.DataFrame()
        logging.info(
            f"Parcellating participants' tensor-derived data according to {parcellation_scheme}..."
        )
        for participant_label, sessions in tqdm.tqdm(self.subjects.items()):
            tmp = self.utils.parcellate_subject_data(
                parcellation_scheme,
                parcels,
                participant_label,
                sessions,
                multi_column=multi_column,
                cropped_to_gm=cropped_to_gm,
                force=force,
                np_operation=np_operation,
            )
            data = pd.concat([data, tmp])
        return data

    @property
    def tensor_work_directory(self) -> Path:
        """
        Path to a working directory to store all tensor estimation workflows

        Returns
        -------
        Path
            a working directory to store all tensor estimation workflows
        """
        return self.get_tensor_work_directory()
