import nipype.pipeline.engine as pe

from connectome_plasticity_project.managers.parcellation.workflows.parcellation.edges import (
    APPLY_TRANSFORM_TO_APPLY_MASK_EDGES,
    INPUT_TO_APPLY_TRANSFORM_EDGES,
    INPUT_TO_NATIVE_NAMING_EDGES,
    INPUT_TO_THRESHOLD_EDGES,
    NATIVE_NAMING_TO_APPLY_MASK_EDGES,
    NATIVE_NAMING_TO_APPLY_TRANSFORM_EDGES,
    THRESHOLD_TO_APPLY_MASK_EDGES,
)
from connectome_plasticity_project.managers.parcellation.workflows.parcellation.nodes import (
    ANTS_APPLY_TRANSFORM_NODE,
    CROP_TO_MASK_NODE,
    INPUT_NODE,
    NATIVE_PARCELLATION_NAMING_NODE,
    PROBSEG_TO_MASK_NODE,
)

PARCELLATION = [
    (
        INPUT_NODE,
        NATIVE_PARCELLATION_NAMING_NODE,
        INPUT_TO_NATIVE_NAMING_EDGES,
    ),
    (INPUT_NODE, ANTS_APPLY_TRANSFORM_NODE, INPUT_TO_APPLY_TRANSFORM_EDGES),
    (
        NATIVE_PARCELLATION_NAMING_NODE,
        ANTS_APPLY_TRANSFORM_NODE,
        NATIVE_NAMING_TO_APPLY_TRANSFORM_EDGES,
    ),
    (INPUT_NODE, PROBSEG_TO_MASK_NODE, INPUT_TO_THRESHOLD_EDGES),
    (PROBSEG_TO_MASK_NODE, CROP_TO_MASK_NODE, THRESHOLD_TO_APPLY_MASK_EDGES),
    (
        ANTS_APPLY_TRANSFORM_NODE,
        CROP_TO_MASK_NODE,
        APPLY_TRANSFORM_TO_APPLY_MASK_EDGES,
    ),
    (
        NATIVE_PARCELLATION_NAMING_NODE,
        CROP_TO_MASK_NODE,
        NATIVE_NAMING_TO_APPLY_MASK_EDGES,
    ),
]


def init_parcellation_wf(name="parcellation_wf") -> pe.Workflow:
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
    return wf
