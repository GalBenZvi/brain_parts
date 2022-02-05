import nipype.pipeline.engine as pe
from nipype.interfaces import ants, fsl
from nipype.interfaces import utility as niu

from connectome_plasticity_project.managers.analyses.qsiprep.workflows.parcellation.configuration import (
    ANTS_APPLY_TRANSFORM_KWARGS,
    DATA_GRABBER_KWARGS,
    FILES_QUERY_KWARGS,
    INPUT_NODE_FIELDS,
    NATIVE_PARCELLATION_NAMING_KWARGS,
    OUTPUT_NODE_FIELDS,
)
from connectome_plasticity_project.managers.analyses.qsiprep.workflows.parcellation.functions import (
    files_query,
    initiate_data_graber,
    native_parcellation_naming,
)

#: i/o
INPUT_NODE = pe.Node(niu.IdentityInterface(fields=INPUT_NODE_FIELDS), name="inputnode")
OUTPUT_NODE = pe.Node(
    niu.IdentityInterface(fields=OUTPUT_NODE_FIELDS), name="outputnode"
)

#: building blocks
DATA_GRABBER_NODE = pe.Node(
    niu.Function(**DATA_GRABBER_KWARGS, function=initiate_data_graber),
    name="files_query",
)

FILES_QUERY_NODE = pe.Node(
    niu.Function(**FILES_QUERY_KWARGS, function=files_query),
    name="files_query",
)

NATIVE_PARCELLATION_NAMING_NODE = pe.Node(
    niu.Function(
        **NATIVE_PARCELLATION_NAMING_KWARGS, function=native_parcellation_naming
    ),
    name="native_parcellation_naming",
)

ANTS_APPLY_TRANSFORM_NODE = pe.Node(
    ants.ApplyTransforms(**ANTS_APPLY_TRANSFORM_KWARGS), name="apply_transform"
)
