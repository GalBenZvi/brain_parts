import pathlib
from pathlib import Path

from connectome_plasticity_project.managers.analyses.analysis import Analysis


class DmriprepManager(Analysis):
    def __init__(self, base_dir: Path, longitudinal: bool = True) -> None:
        super().__init__(base_dir)
        self.longitudinal = longitudinal

    

