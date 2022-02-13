import logging
from pathlib import Path

from connectome_plasticity_project.managers.analyses.utils.data_grabber import (
    DataGrabber,
)
from connectome_plasticity_project.managers.analyses.utils.parcellations import (
    PARCELLATIONS,
)
from connectome_plasticity_project.managers.analyses.utils.templates import (
    TEMPLATES,
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
        self.data_grabber = DataGrabber(base_dir, analysis_type=analysis_type)
        self.parcellations = parcellations
        self.templates = TEMPLATES.get(analysis_type)
