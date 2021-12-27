from pathlib import Path

import pandas as pd
from dwiprep.dwiprep import DmriPrepManager
from numpy import isin

from connectome_plasticity_project.utils.preprocessing import FREESURFER_DIR
from connectome_plasticity_project.utils.preprocessing import SMRIPREP_KWARGS
from connectome_plasticity_project.utils.preprocessing import (
    THE_BASE_IDENTIFIERS,
)

# bids.config.set_option("extension_initial_dot", True)


class DmriManager:
    #: default destination
    DESTINATION_NAME = "derivatives"

    def __init__(self, bids_dir: Path, destination: Path = None) -> None:
        """
        Initiate a dMRI manager object

        Parameters
        ----------
        bids_dir : Path
            Path to BIDS-compatible directory
        destination : Path, optional
            Path to *dmriprep* output destination, by default None
        """
        self.bids_dir = Path(bids_dir)
        self.destination = (
            Path(destination)
            if destination
            else self.bids_dir.parent / self.DESTINATION_NAME
        )

    def check_subject(self, participant_id: str, min_sessions: int = 2) -> bool:
        """
        Checks whether a participant have alreadt been processed or not

        Parameters
        ----------
        participant_id : str
            Participant identifier

        Returns
        -------
        bool
            Whether this participant have been processed or not.
        """
        pariticpant_raw = self.bids_dir / f"sub-{participant_id}"
        participant_destination = (
            self.destination / "dmriprep" / f"sub-{participant_id}"
        )
        sessions = [s for s in pariticpant_raw.glob("ses-*/dwi")]
        if len(sessions) < min_sessions:
            return True
        final_outputs = [
            f for f in participant_destination.glob("ses-*/dwi/*space-anat*")
        ]
        if len(final_outputs) > 0:
            return True
        return False

    def process_participant(self, participant_id: str):
        """
        Runs *participant_id* through *dmriprep* pipeline.

        Parameters
        ----------
        participant_id : str
            Participant's identifier
        """
        print(f"### Initiating workflow for participant {participant_id}... ###")
        dmriprep = DmriPrepManager(
            self.bids_dir,
            self.destination,
            participant_label=participant_id,
            smriprep_kwargs=SMRIPREP_KWARGS,
            fs_subjects_dir=FREESURFER_DIR,
            **THE_BASE_IDENTIFIERS,
        )
        dmriprep.run()

    def query_subjects(self, min_sessions: int = 2) -> pd.DataFrame:
        """
        Query available subjects (whether to process them or not)

        Returns
        -------
        pd.DataFrame
            A dataframe with subjects' identifiers and whether they have been processed.
        """
        subjects = sorted([s.name.split("-")[-1] for s in self.bids_dir.glob("sub-*")])
        manager = pd.DataFrame(index=subjects, columns=["processed"])
        for subj in subjects:
            manager.loc[subj, "processed"] = self.check_subject(subj, min_sessions)
        return manager

    def run(self, max_total: int = None, participant_label: list = None):
        """
        Run *dMRIPrep* for *max_total* subjects or specific subjects declared in *participant_label*.

        Parameters
        ----------
        max_total : int, optional
            Number of subjects to run, by default All available subjects.
        participant_label : list, optional
            Specific subjects' IDs to run, by default None
        """
        if not participant_label:
            unprocessed = self.subjects_manager[
                ~self.subjects_manager["processed"].astype(bool)
            ]
            max_total = max_total if max_total else (len(unprocessed) + 1)
            for i in sorted(unprocessed.index[:max_total]):
                self.process_participant(i)
        else:
            if not isinstance(participant_label, list):
                participant_label = [participant_label]
            for i in sorted(participant_label):
                self.process_participant(i)

    @property
    def subjects_manager(self) -> pd.DataFrame:
        """
        Generates a subjects' manager to describe which ones need to be processed

        Returns
        -------
        pd.DataFrame
            A table that describes which subjects need to be processed.
        """
        return self.query_subjects()
