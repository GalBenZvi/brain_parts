"""
Nodes' configurations for *tensor estimation* pipelines.
"""
import nipype.pipeline.engine as pe
from nipype.interfaces import mrtrix3 as mrt
from nipype.interfaces import utility as niu
from niworkflows.interfaces.bids import DerivativesDataSink

from connectome_plasticity_project.managers.analyses.qsiprep.workflows.tensors.configurations import (
    DWI2TENSOR_KWARGS,
    INPUT_NODE_FIELDS,
    LISTIFY_KWARGS,
    TENSOR2METRIC_KWARGS,
    TENSOR_NAMING_KWARGS,
)


def infer_metric(in_file: str) -> str:
    """
    A simple function to infer tensor-derived metric from file's name.

    Parameters
    ----------
    in_file : str
        A string representing an existing file.

    Returns
    -------
    str
        A metric identifier/label for BIDS specification (i.e, fa, adc, rd etc.)
    """
    from pathlib import Path

    file_name = Path(in_file).name
    suffix = file_name.split(".")[0].lower()
    if "_" in suffix:
        suffix = suffix.split("_")[0]
    return suffix, in_file


#: i/o
INPUT_NODE = pe.Node(
    niu.IdentityInterface(fields=INPUT_NODE_FIELDS),
    name="inputnode",
)

#: Building blocks
DWI2TENSOR_NODE = pe.Node(mrt.FitTensor(**DWI2TENSOR_KWARGS), name="fit_tensor")
TENSOR2METRIC_NODE = pe.Node(
    mrt.TensorMetrics(**TENSOR2METRIC_KWARGS), name="tensor2metric"
)
LISTIFY_NODE = pe.Node(niu.Merge(**LISTIFY_KWARGS), name="listify_metrics")


#: Derivatives storing

INFER_METRIC_NODE = pe.MapNode(
    niu.Function(
        input_names=["in_file"],
        output_names=["metric", "in_file"],
        function=infer_metric,
    ),
    name="infer_metric",
    iterfield=["in_file"],
)

TENSOR_NAMING_NODE = pe.MapNode(
    DerivativesDataSink(**TENSOR_NAMING_KWARGS),
    name="ds_tensor",
    iterfield=["in_file", "desc"],
)

TENSOR_NAMING_WF = pe.Workflow(name="ds_tensor_wf")
TENSOR_NAMING_WF.connect(
    [
        (
            INFER_METRIC_NODE,
            TENSOR_NAMING_NODE,
            [("metric", "desc"), ("in_file", "in_file")],
        ),
    ]
)
