import nipype.pipeline.engine as pe

from connectome_plasticity_project.managers.parcellation.workflows.parcellation.edges import (
    APPLY_TRANSFORM_TO_APPLY_MASK_EDGES,
    INPUT_TO_APPLY_MASK_EDGES,
    INPUT_TO_APPLY_TRANSFORM_EDGES,
    INPUT_TO_THRESHOLD_EDGES,
    THRESHOLD_TO_APPLY_MASK_EDGES,
)
from connectome_plasticity_project.managers.parcellation.workflows.parcellation.nodes import (
    ANTS_APPLY_TRANSFORM_NODE,
    CROP_TO_MASK_NODE,
    INPUT_NODE,
    PROBSEG_TO_MASK_NODE,
)

PARCELLATION = [
    (INPUT_NODE, ANTS_APPLY_TRANSFORM_NODE, INPUT_TO_APPLY_TRANSFORM_EDGES),
]
CROP_TO_GM = [
    (INPUT_NODE, PROBSEG_TO_MASK_NODE, INPUT_TO_THRESHOLD_EDGES),
    (PROBSEG_TO_MASK_NODE, CROP_TO_MASK_NODE, THRESHOLD_TO_APPLY_MASK_EDGES),
    (
        ANTS_APPLY_TRANSFORM_NODE,
        CROP_TO_MASK_NODE,
        APPLY_TRANSFORM_TO_APPLY_MASK_EDGES,
    ),
    (INPUT_NODE, CROP_TO_MASK_NODE, INPUT_TO_APPLY_MASK_EDGES),
]


def init_parcellation_wf(
    name="parcellation_wf", crop_to_gm: bool = True
) -> pe.Workflow:
    """
    Initiates a preprocessing workflow.

    Parameters
    ----------
    name : str, optional
        Workflow's name, by default "preprocess_wf"

    Returns
    -------
    pe.Workflow
        Initiated workflow for preprocessing.
    """

    wf = pe.Workflow(name=name)
    wf.connect(PARCELLATION)
    if crop_to_gm:
        wf.connect(CROP_TO_GM)
    return wf
