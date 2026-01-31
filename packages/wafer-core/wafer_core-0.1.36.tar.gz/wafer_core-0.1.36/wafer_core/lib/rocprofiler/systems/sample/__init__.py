"""ROCprofiler-Systems sample module - rocprof-sys-sample profiling.

This module provides functionality for the rocprof-sys-sample tool,
which provides sampling-based profiling.
"""

from wafer_core.lib.rocprofiler.systems.sample.profiler import run_sampling

__all__ = ["run_sampling"]
