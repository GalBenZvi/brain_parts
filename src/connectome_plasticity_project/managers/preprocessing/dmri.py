from pathlib import Path

import bids
from bids import BIDSLayout
from dwiprep.dwiprep import DmriPrepManager
from dwiprep.utils.bids_query.bids_query import BidsQuery
from dwiprep.workflows.dmri.base import init_dwi_preproc_wf
from niworkflows.utils.spaces import Reference
from niworkflows.utils.spaces import SpatialReferences

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
            destination or self.bids_dir.parent / self.DESTINATION_NAME
        )

    def check_subject(self, participant_id: str) -> bool:
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
        participant_destination = (
            self.destination / "dmriprep" / f"sub-{participant_id}"
        )
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
        dmriprep = DmriPrepManager(
            self.bids_dir,
            self.destination,
            participant_label=participant_id,
            smriprep_kwargs=SMRIPREP_KWARGS,
            fs_subjects_dir=FREESURFER_DIR,
            **THE_BASE_IDENTIFIERS,
        )
        dmriprep.run()


# bids_query = BidsQuery(
#     bids_dir,
#     participant_label=participant_id,

# )as
# session = "202104251808"
# session_data = bids_query.collect_data(participant_id)
# kwargs = dict(
#     freesurfer=False,
#     hires=True,
#     longitudinal=False,
#     omp_nthreads=1,
#     skull_strip_mode="force",
#     skull_strip_template=Reference("OASIS30ANTs"),
#     spaces=SpatialReferences(spaces=["MNI152NLin2009cAsym", "fsaverage5"]),
# )
# for participant in sorted(Path(bids_dir).glob("sub-*")):
#     participant_id = participant.name.split("-")[-1]
#     flag = Path(out_dir) / "dmriprep" / f"sub-{participant_id}"
#     flag = [f for f in flag.glob("ses-*/dwi/*space-anat*")]
#     if len(flag) > 0:
#         print(f"Already processed {participant_id}")
#         continue
#     dmriprep = DmriPrepManager(
#         bids_dir,
#         out_dir,
#         participant_label=participant_id,
#         smriprep_kwargs=kwargs,
#         fs_subjects_dir="/media/groot/Yalla/media/MRI/derivatives/freesurfer",
#         **the_base_identifiers,
#     )
#     print(f"### Initiating workflow for participant {participant_id}... ###")
#     dmriprep.run()
