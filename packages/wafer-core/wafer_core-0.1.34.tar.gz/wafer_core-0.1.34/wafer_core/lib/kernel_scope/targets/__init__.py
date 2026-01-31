"""GPU target specifications for occupancy and resource calculations.

Provides hardware-specific constants for AMD GPU architectures.
"""

from wafer_core.lib.kernel_scope.targets.specs import (
    TargetSpecs,
    get_target_specs,
    SUPPORTED_TARGETS,
)

__all__ = [
    "TargetSpecs",
    "get_target_specs",
    "SUPPORTED_TARGETS",
]
