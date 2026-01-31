"""ROCprofiler-Compute tools.

Grouped rocprof compute operations: profile, analyze.
"""

from wafer_core.tools.rocprof_compute_tools.rocprof_compute_analyze_tool import (
    ROCPROF_COMPUTE_ANALYZE_TOOL,
    exec_rocprof_compute_analyze,
)
from wafer_core.tools.rocprof_compute_tools.rocprof_compute_profile_tool import (
    ROCPROF_COMPUTE_PROFILE_TOOL,
    exec_rocprof_compute_profile,
)

__all__ = [
    "ROCPROF_COMPUTE_PROFILE_TOOL",
    "ROCPROF_COMPUTE_ANALYZE_TOOL",
    "exec_rocprof_compute_profile",
    "exec_rocprof_compute_analyze",
]
