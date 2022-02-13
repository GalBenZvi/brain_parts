import logging
from pathlib import Path

import nibabel as nib
import numpy as np
import pandas as pd

from connectome_plasticity_project.managers.analyses.utils.data_grabber import (
    DataGrabber,
)
from connectome_plasticity_project.managers.analyses.utils.parcellations import (
    PARCELLATIONS,
)
from connectome_plasticity_project.managers.analyses.utils.templates import (
    TEMPLATES,
    TENSOR_DERIVED_METRICS,
    TENSOR_METRICS_FILES_TEMPLATE,
    TENSOR_METRICS_OUTPUT_TEMPLATE,
)

DEFAULT_DESTINATION = "/home/groot/Projects/PhD/connectomeplasticity/data/analyses/{analysis_type}"

LOGGER_CONFIG = dict(
    filemode="w",
    format="%(asctime)s - %(message)s",
    level=logging.INFO,
)


class AnalysisUtils:
    def __init__(
        self,
        base_dir: Path,
        analysis_type: str,
        parcellations: dict = PARCELLATIONS,
    ) -> None:
        self.base_dir = base_dir
        self.data_grabber = DataGrabber(base_dir, analysis_type=analysis_type)
        self.parcellations = parcellations
        self.templates = TEMPLATES.get(analysis_type)

    def parcellate_image(
        self,
        atlas: Path,
        image: Path,
        parcels: pd.DataFrame,
        np_operation: str = "nanmean",
    ) -> pd.Series:
        """
        Parcellates an *image* according to *atlas*

        Parameters
        ----------
        atlas : Path
            A parcellation atlas in *image* space.
        image : Path
            An image to be parcellated
        parcels : pd.DataFrame
            A dataframe for *atlas* parcels.
        np_operation : str, optional
            A string representing a method of numpy, by default "nanmean".

        Returns
        -------
        pd.Series
            The *np_operation* value of *image* in each *atlas* parcel.
        """
        func = getattr(np, np_operation)
        atlas_data = (
            nib.load(atlas).get_fdata()
            if isinstance(atlas, Path)
            else atlas.get_fdata()
        )
        data = nib.load(image).get_fdata()
        out = pd.Series(index=parcels.index)
        for i in parcels.index:
            label = parcels.loc[i, "Label"]
            mask = atlas_data == label
            out.loc[i] = func(data[mask])

        return out

    def parcellate_session_tensors(
        self,
        parcellation_scheme: str,
        parcels: pd.DataFrame,
        participant_label: str,
        session: str,
        multi_column: pd.MultiIndex,
        native_atlas: Path = None,
        cropped_to_gm: bool = False,
        force: bool = False,
        np_operation: str = "nanmean",
    ):
        """
        Parcellates available data for *participant_label*, declared by *multi_column* levels.

        Parameters
        ----------
        dmriprep_dir : Path
            Path to *dmriprep* outputs' directory
        participant_label : str
            A label referring to an existing subject
        image : Path
            Path to subject's native-space parcellation
        multi_column : pd.MultiIndex
            A multi-column constructed by ROI * metrics.
        parcels : pd.DataFrame
            A dataframe describing the parcellation scheme.
        parcellation_scheme : str
            The name of the parcellation scheme.

        Returns
        -------
        pd.DataFrame
            A dataframe containing all of *participant_label*'s data, parcellated by *parcellation_scheme*.
        """
        logging.info(f"\t ses-{session}")
        session_data = pd.Series(index=multi_column, name=session)

        reference, _, _ = self.data_grabber.locate_epi_references(
            participant_label, session, raise_not_found=False
        )

        reference = reference.get("native_epi_reference")
        if not reference:
            return
        target_kwargs = dict(
            **TENSOR_METRICS_OUTPUT_TEMPLATE,
            atlas=parcellation_scheme,
            measure=np_operation.replace("nan", ""),
        )
        if cropped_to_gm:
            target_kwargs["label"] = "GM"
        if not native_atlas:
            native_atlas = self.locate_native_atlas(
                reference, parcellation_scheme, cropped_to_gm
            )

        out_file = self.data_grabber.build_derivatives_name(
            reference, **target_kwargs
        )
        if out_file.exists() and not force:
            session_data = pd.read_csv(out_file, index_col=[0, 1]).squeeze()

        else:
            for metric in TENSOR_DERIVED_METRICS:
                logging.info(f"\t\t {metric}")
                metric_file = self.data_grabber.build_derivatives_name(
                    reference, desc=metric, **TENSOR_METRICS_FILES_TEMPLATE
                )
                session_data.loc[slice(None), metric] = self.parcellate_image(
                    native_atlas, metric_file, parcels, np_operation
                ).values
            session_data.to_csv(out_file)
        return session_data

    def locate_native_atlas(
        self,
        reference: Path,
        parcellation_scheme: str,
        cropped_to_gm: bool = False,
        reference_type: str = "epi",
    ) -> Path:
        """
        Locates a native parcellation that corresponds to *reference* space.

        Parameters
        ----------
        reference : Path
            [description]
        cropped_to_gm : bool, optional
            [description], by default False

        Returns
        -------
        Path
            [description]
        """
        atlas_kwargs = (
            self.templates.NATIVE_PARCELLATION_NAMING_KWARGS.value.get(
                reference_type
            )
        )
        if cropped_to_gm:
            atlas_kwargs["label"] = "GM"
        return self.data_grabber.build_derivatives_name(
            reference, **atlas_kwargs, atlas=parcellation_scheme
        )

    def parcellate_subject_data(
        self,
        parcellation_scheme: str,
        parcels: pd.DataFrame,
        participant_label: str,
        sessions: list,
        multi_column: pd.MultiIndex,
        cropped_to_gm: bool = False,
        force: bool = False,
        np_operation: str = "nanmean",
    ) -> pd.DataFrame:
        logging.info(f"sub-{participant_label}")
        multi_index = pd.MultiIndex.from_product(
            [[participant_label], sessions]
        )
        data = pd.DataFrame(index=multi_index, columns=multi_column)
        for session in sessions:
            data.loc[
                (participant_label, session)
            ] = self.parcellate_session_tensors(
                parcellation_scheme,
                parcels,
                participant_label,
                session,
                multi_column,
                cropped_to_gm=cropped_to_gm,
                force=force,
                np_operation=np_operation,
            )
        return data
