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

    def parcellate_subject_tensors(
        self,
        parcellation_scheme: str,
        parcels: pd.DataFrame,
        participant_label: str,
        session: str,
        native_atlas: Path,
        multi_column: pd.MultiIndex,
        cropped_to_gm: bool = True,
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
        subj_data = pd.Series(index=multi_column)
        reference, dwi_dir, prefix = self.data_grabber.locate_epi_references(
            participant_label, session, raise_not_found=False
        )
        out_file = self.data_grabber.search_for_file(
            dwi_dir,
            TENSOR_METRICS_OUTPUT_TEMPLATE,
            {"prefix": prefix, "parcellation_scheme": parcellation_scheme},
        )
        out_file = dwi_dir / TENSOR_METRICS_OUTPUT_TEMPLATE.format(
            participant_label=participant_label,
            session=session,
            parcellation_scheme=parcellation_scheme,
            measure=np_operation.replace("nan", ""),
        )
        if cropped_to_gm:
            out_name = out_file.name.split("_")
            out_name.insert(3, "label-GM")
            out_file = out_file.parent / "_".join(out_name)
        if out_file.exists() and not force:
            data = pd.read_csv(out_file, index_col=[0, 1], header=[0, 1])
            subj_data.loc[(participant_label, session)] = data.T.loc[
                (participant_label, session)
            ]
        else:
            for metric in multi_column.levels[-1]:
                logging.info(metric)
                metric_file = TENSOR_METRICS_FILES_TEMPLATE.format(
                    dmriprep_dir=dmriprep_dir,
                    participant_label=participant_label,
                    session=session,
                    metric=metric.lower(),
                )
                subj_data.loc[
                    (participant_label, session), (slice(None), metric)
                ] = parcellate_image(
                    image, metric_file, parcels, np_operation
                ).values
            subj_data.loc[(participant_label, session)].to_csv(out_file)
        return subj_data
