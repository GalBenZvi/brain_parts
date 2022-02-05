"""
Configurations for *parcellation* pipeline
"""

INPUT_NODE_FIELDS = [
    "base_dir",
    "participant_label",
    "sessions",
    "probability_masking_threshold",
    "parcellation_scheme",
    "parcellation_image",
]
OUTPUT_NODE_FIELDS = ["whole_brain_parcellation", "gm_cropped_parcellation"]

DATA_GRABBER_KWARGS = dict(
    input_names=["base_dir", "analysis_type"],
    output_names=["data_grabber"],
)
FILES_QUERY_KWARGS = dict(
    input_names=["data_grabber", "participant_label", "sessions"],
    output_names=[
        "anatomical_reference",
        "mni_to_native_transformation",
        "gm_probability",
    ],
)
NATIVE_PARCELLATION_NAMING_KWARGS = dict(
    input_names=[
        "data_grabber",
        "reference",
        "parcellation_scheme",
    ],
    output_names=["whole_brain", "gm_cropped"],
)

ANTS_APPLY_TRANSFORM_KWARGS = dict(interpolation="NearestNeighbor")

PROBSEG_TO_MASK_KWARGS = dict(direction="below")
