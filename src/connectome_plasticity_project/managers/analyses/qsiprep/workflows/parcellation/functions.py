def files_query(
    base_dir,
    participant_label: str,
    sessions: list,
    references_keys: list = [
        "anatomical_reference",
        "mni_to_native_transformation",
        "gm_probability",
    ],
    analysis_type: str = "qsiprep",
) -> list:
    """
    An interface for files query using custom data grabber

    Parameters
    ----------
    base_dir : Path
        Base derivatives directory
    participant_label : str
        sub-xxx identifier
    sessions : list
        A list of available ses-xxx identifiers
    references_keys : list, optional
        A list of relevent keys, by default [ "anatomical_reference", "mni_to_native_transformation", "gm_probability", ]
    analysis_type : str, optional
        The kind of derivatives stored in *base_dir*, by default "qsiprep"
    Returns
    -------
    list
        A list of paths to relevant files for parcellation
    """
    from connectome_plasticity_project.managers.analyses.utils.data_grabber import (
        DataGrabber,
    )

    data_grabber = DataGrabber(base_dir, analysis_type)
    references, _, _ = data_grabber.locate_anatomical_references(
        participant_label, sessions
    )

    return [references.get(key) for key in references_keys]


def native_parcellation_naming(
    base_dir, reference, parcellation_scheme, analysis_type: str = "qsiprep"
):
    """
    Build paths to native parcellation schemes

    Parameters
    ----------
    base_dir : Path
        Base derivatives directory
    reference : Path
        Path to a native anatomical reference file
    parcellation_scheme : str
        A string representing a parcellation atlas.
    analysis_type : str, optional
        The kind of derivatives stored in *base_dir*, by default "qsiprep"
    Returns
    -------
    list
        Paths to whole brain and GM-cropped native parcellations
    """
    from connectome_plasticity_project.managers.analyses.utils.data_grabber import (
        DataGrabber,
    )

    data_grabber = DataGrabber(base_dir, analysis_type)
    whole_brain = data_grabber.build_parcellation_naming(
        parcellation_scheme, reference
    )
    gm_cropped = data_grabber.build_parcellation_naming(
        parcellation_scheme, reference, label="GM"
    )
    return whole_brain, gm_cropped
