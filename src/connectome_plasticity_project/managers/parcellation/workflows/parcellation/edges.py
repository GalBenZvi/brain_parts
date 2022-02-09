"""
Connections configurations for *parcellation* pipelines.
"""

#: Apply Transform
INPUT_TO_APPLY_TRANSFORM_EDGES = [
    ("parcellation_image", "input_image"),
    ("anatomical_reference", "reference_image"),
    ("mni_to_native_transformation", "transforms"),
    ("out_whole_brain", "output_image"),
]

#: Probseg to mask
INPUT_TO_THRESHOLD_EDGES = [
    ("probability_masking_threshold", "thresh"),
    ("gm_probability", "in_file"),
]

#: Masking parcellation
THRESHOLD_TO_APPLY_MASK_EDGES = [("out_file", "mask_file")]
APPLY_TRANSFORM_TO_APPLY_MASK_EDGES = [("output_image", "in_file")]
INPUT_TO_APPLY_MASK_EDGES = [("out_gm_cropped", "out_file")]
