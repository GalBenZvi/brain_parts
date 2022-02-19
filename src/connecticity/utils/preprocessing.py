from niworkflows.utils.spaces import Reference, SpatialReferences

FREESURFER_DIR = "/media/groot/Yalla/media/MRI/derivatives/freesurfer"
THE_BASE_IDENTIFIERS = dict(
    dwi_identifier={"direction": "FWD"},
    fmap_identifier={"direction": "REV", "suffix": "epi"},
    t1w_identifier={"ceagent": "corrected"},
    t2w_identifier={"ceagent": "corrected"},
)
SMRIPREP_KWARGS = dict(
    freesurfer=False,
    hires=True,
    longitudinal=False,
    omp_nthreads=1,
    skull_strip_mode="force",
    skull_strip_template=Reference("OASIS30ANTs"),
    spaces=SpatialReferences(spaces=["MNI152NLin2009cAsym", "fsaverage5"]),
)
