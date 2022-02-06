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
    whole_brain = data_grabber.build_derivatives_name(
        reference, suffix="dseg", atlas=parcellation_scheme, space="anat"
    )
    gm_cropped = data_grabber.build_derivatives_name(
        reference,
        label="GM",
        suffix="dseg",
        atlas=parcellation_scheme,
        space="anat",
    )
    return str(whole_brain), str(gm_cropped)
