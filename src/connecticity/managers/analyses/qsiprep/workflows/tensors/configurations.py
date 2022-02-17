"""
Configurations for *preprocessing* pipeline.
"""
from connecticity.managers.analyses.utils.templates import (
    TENSOR_DERIVED_METRICS,
    TENSOR_METRICS_FILES_TEMPLATE,
)

#: i/o
INPUT_NODE_FIELDS = ["base_directory", "dwi_file", "grad_file"]

#: Keyword arguments
DWI2TENSOR_KWARGS = dict()
TENSOR2METRIC_KWARGS = {
    f"out_{metric}": f"{metric}.nii.gz" for metric in TENSOR_DERIVED_METRICS
}
LISTIFY_KWARGS = dict(numinputs=len(TENSOR_DERIVED_METRICS.keys()))

#: Tensor namings
TENSOR_NAMING_KWARGS = dict(**TENSOR_METRICS_FILES_TEMPLATE, compress=True)
