import nipype.pipeline.engine as pe

from connectome_plasticity_project.managers.analyses.qsiprep.workflows.tensors.edges import (
    DWI2TENSOR_TO_TENSOR2METRIC_EDGES,
    INPUT_TO_DDS_EDGES,
    INPUT_TO_DWI2TENSOR_EDGES,
    LISTIFY_TO_DDS_EDGES,
    TENSOR2METRIC_TO_LISTIFY_EDGES,
)
from connectome_plasticity_project.managers.analyses.qsiprep.workflows.tensors.nodes import (
    DWI2TENSOR_NODE,
    INPUT_NODE,
    LISTIFY_NODE,
    TENSOR2METRIC_NODE,
    TENSOR_NAMING_WF,
)

TENSOR_ESTIMATION = [
    (INPUT_NODE, DWI2TENSOR_NODE, INPUT_TO_DWI2TENSOR_EDGES),
    (DWI2TENSOR_NODE, TENSOR2METRIC_NODE, DWI2TENSOR_TO_TENSOR2METRIC_EDGES),
    (TENSOR2METRIC_NODE, LISTIFY_NODE, TENSOR2METRIC_TO_LISTIFY_EDGES),
    (INPUT_NODE, TENSOR_NAMING_WF, INPUT_TO_DDS_EDGES),
    (LISTIFY_NODE, TENSOR_NAMING_WF, LISTIFY_TO_DDS_EDGES),
]


def init_tensor_wf(name="tensor_estimation_wf") -> pe.Workflow:
    """
    Initiates a tensor estimation workflow

    Parameters
    ----------
    name : str, optional
        Workflow's name, by default "tensor_estimation_wf"

    Returns
    -------
    pe.Workflow
        Initiated workflow for tensor and tensor-derived metrics estimation.
    """

    wf = pe.Workflow(name=name)
    wf.connect(TENSOR_ESTIMATION)
    return wf
