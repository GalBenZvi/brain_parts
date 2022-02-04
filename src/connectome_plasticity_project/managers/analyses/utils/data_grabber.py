from pathlib import Path
from typing import Union

import bids

from connectome_plasticity_project.managers.analyses.messages import (
    INVALID_PATTERN,
)
from connectome_plasticity_project.managers.analyses.utils.templates import (
    TEMPLATES,
)
from connectome_plasticity_project.managers.analyses.utils.templates import (
    generate_atlas_file_name,
)


class DataGrabber:
    def __init__(self, base_dir: Path, analysis_type: str) -> None:
        """
        Initiates a *DataGrabber* instance for *analysis_type*, querying its *base_dir*

        Parameters
        ----------
        base_dir : Path
            Path to a derivatives' directory to be queried
        analysis_type : str
            A string representing the analysis that is stored in *base_dir*
        """
        self.base_dir = Path(base_dir)
        self.layout = bids.BIDSLayout(
            base_dir, derivatives=True, validate=False
        )
        self.templates = TEMPLATES.get(analysis_type)
        self.longitudinal_sensitive = (
            self.templates.LONGITUDINAL_SENSITIVE.value
        )

    def locate_anatomical_directory(
        self,
        participant_label: str,
        sessions: list,
    ) -> Path:
        """
        Locates subject's anatomical derivatives' directory

        Parameters
        ----------
        participant_label : str
            Participant label (an existing subject within *self.base_dir*)
        sessions : list
            A list of available sessions for *participant_label*

        Returns
        -------
        Path
            Subject's anatomical derivatives' directory
        """
        if len(sessions) > 1 or not self.longitudinal_sensitive:
            anat_dir = self.base_dir / f"sub-{participant_label}" / "anat"
            prefix = f"sub-{participant_label}" + "_"
        else:
            anat_dir = (
                self.base_dir
                / f"sub-{participant_label}"
                / f"ses-{sessions[0]}"
                / "anat"
            )
            prefix = (
                f"sub-{participant_label}" + "_" + f"ses-{sessions[0]}" + "_"
            )
        return anat_dir, prefix

    def search_for_file(
        self,
        base_dir: Path,
        pattern: str,
        format: dict = None,
        return_list: bool = False,
    ) -> Union[list, Path]:
        """
        Search for a *pattern* within *base_dir* with given a *format*.

        Parameters
        ----------
        base_dir : Path
            Base directory to search within
        pattern : str
            Pattern to locate
        format : dict
            Formatting of *pattern*.
        return_list : bool, optional
            Whether to return a list of located files or a single file, by default False

        Returns
        -------
        Union[list,Path]
            Either a list of paths to all located files or a single file

        Raises
        ------
        FileNotFoundError
            If could not locate requested pattern within *base_dir*, raise an error.
        """
        if format:
            result = [f for f in base_dir.glob(pattern.format(**format))]
        else:
            result = [f for f in base_dir.glob(pattern)]
        if not result:
            raise FileNotFoundError(
                INVALID_PATTERN.format(
                    base_dir=base_dir, pattern=pattern, format=format
                )
            )
        return result if return_list else result[0]

    def locate_anatomical_references(
        self, participant_label: str, sessions: list
    ):
        """
        Locates subjects' preprocessed anatomical reference

        Parameters
        ----------
        output_dir : Path
            An output (derivatives) directort of either *fmriprep* or *dmriprep*
        """
        anat_dir, prefix = self.locate_anatomical_directory(
            participant_label, sessions
        )
        references = {}
        for key in self.templates.ANATOMICAL_TEMPLATES.value:
            pattern = prefix + self.templates[key].value
            result = self.search_for_file(anat_dir, pattern, None)
            references[key.lower()] = result
        return references, anat_dir, prefix

    def build_parcellation_naming(
        self, parcellation_scheme: str, references: dict, label: str = None
    ):
        out_file = generate_atlas_file_name(
            references.get("anatomical_reference"),
            parcellation_scheme,
            space="anat",
            label=label,
        )
        return out_file
