"""
Configurations for *parcellation* pipeline
"""

INPUT_NODE_FIELDS = [
    "parcellation_image",
    "anatomical_reference",
    "mni_to_native_transformation",
    "gm_probability",
    "probability_masking_threshold",
    "out_whole_brain",
    "out_gm_cropped",
]

ANTS_APPLY_TRANSFORM_KWARGS = dict(interpolation="NearestNeighbor")

PROBSEG_TO_MASK_KWARGS = dict(direction="below")
CROP_TO_MASK_KWARGS = dict(output_datatype="int")
