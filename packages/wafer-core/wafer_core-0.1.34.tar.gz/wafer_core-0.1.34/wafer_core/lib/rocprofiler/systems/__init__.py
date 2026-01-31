"""ROCprofiler-Systems - System-level profiling and analysis.

This module provides functionality for the rocprof-sys toolset integration.
Follows the architecture pattern established in Wafer-391: ROCprofiler Tools Architecture.

rocprof-sys is a multi-tool ecosystem for system-level profiling:
    - rocprof-sys-run: Main profiling wrapper (comprehensive tracing/profiling)
    - rocprof-sys-sample: Sampling-based profiling
    - rocprof-sys-instrument: Binary instrumentation (Dyninst)
    - rocprof-sys-avail: Query available metrics/components

Public API:
    Installation:
    - check_installation: Check if rocprof-sys tools are installed
    - find_rocprof_sys_run: Find rocprof-sys-run executable path
    - find_rocprof_sys_sample: Find rocprof-sys-sample executable path
    - find_rocprof_sys_instrument: Find rocprof-sys-instrument executable path
    - find_rocprof_sys_avail: Find rocprof-sys-avail executable path

    Profiling:
    - run_systems_profile: Execute system profiling (rocprof-sys-run)
    - run_sampling: Execute sampling profiling (rocprof-sys-sample)
    - run_instrumentation: Execute binary instrumentation (rocprof-sys-instrument)

    Analysis:
    - analyze_file: Analyze output files (auto-detect format) - in run.analyzer

    Querying:
    - query_available_metrics: Query available metrics and components
    - query_components: Query available components
    - query_hw_counters: Query hardware counters

    Types:
    - CheckResult: Installation check result
    - ProfileResult: Profiling execution result
    - AnalysisResult: Analysis result
    - SystemMetrics: System metrics data

Example:
    >>> from wafer_core.lib.rocprofiler.systems import check_installation, run_systems_profile
    >>>
    >>> # Check if rocprof-sys is installed
    >>> result = check_installation()
    >>> if result.installed:
    ...     print(f"Found rocprof-sys-run at {result.paths['run']}")
    >>>
    >>> # Run system profiling
    >>> profile_result = run_systems_profile(
    ...     command=["./my_app"],
    ...     output_dir=Path("./results"),
    ...     trace=True,
    ...     profile=True
    ... )
    >>> if profile_result.success:
    ...     print(f"Generated files: {profile_result.output_files}")
"""

from wafer_core.lib.rocprofiler.systems.avail.query import (
    query_available_metrics,
    query_components,
    query_hw_counters,
)
from wafer_core.lib.rocprofiler.systems.finder import (
    check_installation,
    find_rocprof_sys_avail,
    find_rocprof_sys_instrument,
    find_rocprof_sys_run,
    find_rocprof_sys_sample,
)
from wafer_core.lib.rocprofiler.systems.instrument.profiler import (
    run_instrumentation,
)
from wafer_core.lib.rocprofiler.systems.run.profiler import run_systems_profile
from wafer_core.lib.rocprofiler.systems.sample.profiler import run_sampling
from wafer_core.lib.rocprofiler.systems.types import (
    AnalysisResult,
    CheckResult,
    ProfileResult,
    SystemMetrics,
)

__all__ = [
    # Installation checking
    "check_installation",
    "find_rocprof_sys_run",
    "find_rocprof_sys_sample",
    "find_rocprof_sys_instrument",
    "find_rocprof_sys_avail",
    # Profiling
    "run_systems_profile",
    "run_sampling",
    "run_instrumentation",
    # Querying
    "query_available_metrics",
    "query_components",
    "query_hw_counters",
    # Types
    "CheckResult",
    "ProfileResult",
    "AnalysisResult",
    "SystemMetrics",
]
