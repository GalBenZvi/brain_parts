from pathlib import Path

from nipype.interfaces import fsl
from nipype.interfaces.ants import ApplyTransforms


def at_ants(
    in_file: Path,
    ref: Path,
    xfm: Path,
    out_file: Path,
    args: dict,
    force: bool = False,
):
    """
    Apply pre-calculated transformations between images of different spaces

    Parameters
    ----------
    in_file : Path
        Path to the "moving" file
    ref : Path
        Path to the "static" file
    xfm : Path
        Path to a pre-calculated transformation
    out_file : Path
        Path to output file
    args : dict
        A dictionary of keys appropriate for *ApplyTransform* instance of *nipype*
    force : bool, optional
        Whether to perform operation even if output exists, by default False
    """
    if not out_file.exists() or force:
        at = ApplyTransforms(**args)
        at.inputs.input_image = in_file
        at.inputs.reference_image = ref
        at.inputs.transforms = xfm
        at.inputs.output_image = str(out_file)
        at.run()


def binarize_image(
    in_file: Path, out_file: Path, threshold: float = 0.5, force: bool = False
):
    """
    Binarizes an image according to given *threshold*

    Parameters
    ----------
    in_file : Path
        Path to image to be binarized
    out_file : Path
        Path to output binarized images
    threshold : float, optional
        Threshold to use for binarization, by default 0.5
    """
    if not out_file.exists() or force:
        thresh = fsl.Threshold()
        thresh.inputs.in_file = in_file
        thresh.inputs.thresh = threshold
        thresh.inputs.direction = "below"
        # thresh.inputs.output_datatype = "int"
        thresh.inputs.out_file = out_file
        thresh.run()


def apply_mask(
    in_file: Path, mask: Path, out_file: Path, args: dict, force: bool = False
):
    if not out_file.exists() or force:
        masker = fsl.ApplyMask(**args)
        masker.inputs.in_file = in_file
        masker.inputs.mask_file = mask
        masker.inputs.out_file = out_file
        masker.run()
