"""Metric computation for kernel scope analysis."""

from wafer_core.lib.kernel_scope.metrics.occupancy import (
    compute_occupancy,
    OccupancyResult,
)

__all__ = [
    "compute_occupancy",
    "OccupancyResult",
]
