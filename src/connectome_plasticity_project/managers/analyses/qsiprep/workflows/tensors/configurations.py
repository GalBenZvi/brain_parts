"""
Configurations for *preprocessing* pipeline.
"""

METRICS = [
    "fa",
    "adc",
    "ad",
    "rd",
    "cl",
    "cp",
    "cs",
    "evec",
    "eval",
]
#: i/o
INPUT_NODE_FIELDS = ["base_directory", "dwi_file", "grad_file"]

#: Keyword arguments
DWI2TENSOR_KWARGS = dict()
TENSOR2METRIC_KWARGS = {
    f"out_{metric}": f"{metric}.nii.gz" for metric in METRICS
}
LISTIFY_KWARGS = dict(numinputs=len(METRICS))

#: Tensor namings
TENSOR_NAMING_KWARGS = dict(suffix="epiref", resolution="dwi", compress=True)
