"""
Messages for the :mod:`brain_parts.parcellation` module.
"""
ANNOTATION_FILE_GENERATION_START: str = "Generating annotation file for {parcellation_scheme} in {subject_label} {hemisphere_label} space."
SUBCORTICAL_ANNOTATION_FILE_GENERATION_START: str = "Generating annotation file for {parcellation_scheme}'s sub-cortex in {subject_label} space."

PARCELLATION_ALREADY_DONE = """
{parcellation_scheme} atlas was already cropped to subject {participant_label}'s gray matter space.
To re-run this process, pass force=True as a keyword arguement.
"""

REGISTRATION_WORKFLOW = """
{parcellation_scheme} atlas was previously registerted to subject {participant_label}'s individual space.
To re-run this process, pass force=True as a keyword arguement.
"""
# flake8: noqa: E501
