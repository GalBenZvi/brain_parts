"""
Connections configurations for *parcellation* pipelines.
"""
#: Native Naming
INPUT_TO_NATIVE_NAMING_EDGES = [
    ("parcellation_scheme", "parcellation_scheme"),
    ("base_dir", "base_dir"),
    ("analysis_type", "analysis_type"),
    ("anatomical_reference", "reference"),
]

#: Apply Transform
INPUT_TO_APPLY_TRANSFORM_EDGES = [
    ("parcellation_image", "input_image"),
    ("anatomical_reference", "reference_image"),
    ("mni_to_native_transformation", "transforms"),
]
NATIVE_NAMING_TO_APPLY_TRANSFORM_EDGES = [("whole_brain", "output_image")]

#: Probseg to mask
INPUT_TO_THRESHOLD_EDGES = [
    ("probability_masking_threshold", "thresh"),
    ("gm_probability", "in_file"),
]

#: Masking parcellation
THRESHOLD_TO_APPLY_MASK_EDGES = [("out_file", "mask_file")]
APPLY_TRANSFORM_TO_APPLY_MASK_EDGES = [("output_image", "in_file")]
NATIVE_NAMING_TO_APPLY_MASK_EDGES = [("gm_cropped", "out_file")]
