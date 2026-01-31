"""ROCprofiler tools - AMD GPU profiling and analysis tools.

This package provides core functionality for AMD ROCprofiler tools:
- rocprofiler-sdk: Primary profiling tool (rocprofv3)
- rocprofiler-compute: GUI-based analysis tool

Follows Wafer-391: ROCprofiler Tools Architecture.
"""

# Import submodules
from . import compute, sdk

__all__ = [
    "compute",
    "sdk",
]
