def initiate_data_graber(base_dir, analysis_type: str = "qsiprep"):
    """
    Instanciates a DataGraber instance for files query

    Parameters
    ----------
    base_dir : Path
        Base derivatives directory
    analysis_type : str, optional
        The kind of derivatives stored in *base_dir*, by default "qsiprep"

    Returns
    -------
    DataGrabber
        Instanciated DataGraber instance
    """
    from connectome_plasticity_project.managers.analyses.utils.data_grabber import (
        DataGrabber,
    )

    return DataGrabber(base_dir, analysis_type)


def files_query(
    data_grabber,
    participant_label: str,
    sessions: list,
    references_keys: list = [
        "anatomical_reference",
        "mni_to_native_transformation",
        "gm_probability",
    ],
) -> list:
    """
    An interface for files query using custom data grabber

    Parameters
    ----------

    participant_label : str
        sub-xxx identifier
    sessions : list
        A list of available ses-xxx identifiers

    references_keys : list, optional
        A list of relevent keys, by default [ "anatomical_reference", "mni_to_native_transformation", "gm_probability", ]

    Returns
    -------
    list
        A list of paths to relevant files for parcellation
    """

    references, _, _ = data_grabber.locate_anatomical_references(
        participant_label, sessions
    )

    return [references.get(key) for key in references_keys]


def native_parcellation_naming(data_grabber, reference, parcellation_scheme):
    """
    Build paths to native parcellation schemes

    Parameters
    ----------
    data_grabber : DataGrabber
        Instanciated DataGraber instance
    reference : Path
        Path to a native anatomical reference file
    parcellation_scheme : str
        A string representing a parcellation atlas.

    Returns
    -------
    list
        Paths to whole brain and GM-cropped native parcellations
    """
    whole_brain = data_grabber.build_parcellation_naming(parcellation_scheme, reference)
    gm_cropped = data_grabber.build_parcellation_naming(
        parcellation_scheme, reference, label="GM"
    )
    return whole_brain, gm_cropped
