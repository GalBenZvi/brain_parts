"""
Nodes' configurations for *parcellation* pipelines.
"""
import nipype.pipeline.engine as pe
from nipype.interfaces import ants, fsl
from nipype.interfaces import utility as niu

from connectome_plasticity_project.managers.parcellation.workflows.parcellation.configuration import (
    ANTS_APPLY_TRANSFORM_KWARGS,
    CROP_TO_MASK_KWARGS,
    INPUT_NODE_FIELDS,
    PROBSEG_TO_MASK_KWARGS,
)

#: i/o
INPUT_NODE = pe.Node(
    niu.IdentityInterface(fields=INPUT_NODE_FIELDS), name="inputnode"
)

#: building blocks
ANTS_APPLY_TRANSFORM_NODE = pe.Node(
    ants.ApplyTransforms(**ANTS_APPLY_TRANSFORM_KWARGS), name="apply_transform"
)

PROBSEG_TO_MASK_NODE = pe.Node(
    fsl.Threshold(**PROBSEG_TO_MASK_KWARGS), name="probseg_to_mask"
)

CROP_TO_MASK_NODE = pe.Node(
    fsl.ApplyMask(**CROP_TO_MASK_KWARGS), name="crop_to_mask"
)
