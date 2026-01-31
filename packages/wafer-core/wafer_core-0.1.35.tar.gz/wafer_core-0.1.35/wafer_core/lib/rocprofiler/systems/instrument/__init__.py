"""ROCprofiler-Systems instrument module - rocprof-sys-instrument.

This module provides functionality for the rocprof-sys-instrument tool,
which provides binary instrumentation using Dyninst.
"""

from wafer_core.lib.rocprofiler.systems.instrument.profiler import run_instrumentation

__all__ = ["run_instrumentation"]
