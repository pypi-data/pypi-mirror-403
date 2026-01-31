"""ROCprofiler-SDK - Core profiling and analysis functionality.

This module provides core functionality for the rocprofv3 tool integration.
Follows the architecture pattern established in Wafer-391: ROCprofiler Tools Architecture.

Public API:
    - check_installation: Check if rocprofv3 is installed
    - find_rocprofv3: Find rocprofv3 executable path
    - run_profile: Execute profiling
    - analyze_file: Analyze output files (auto-detect format)
    - analyze_csv, analyze_json, analyze_rocpd: Format-specific analyzers
    - CheckResult: Installation check result
    - ProfileResult: Profiling execution result
    - AnalysisResult: Analysis result
    - KernelMetrics: Kernel metrics data

Example:
    >>> from wafer_core.lib.rocprofiler.sdk import check_installation, run_profile
    >>>
    >>> # Check if rocprofv3 is installed
    >>> result = check_installation()
    >>> if result.installed:
    ...     print(f"Found rocprofv3 at {result.path}")
    >>>
    >>> # Run profiling
    >>> profile_result = run_profile(
    ...     command=["./my_kernel"],
    ...     output_dir=Path("./results"),
    ...     output_format="csv"
    ... )
    >>> if profile_result.success:
    ...     print(f"Generated files: {profile_result.output_files}")
"""

from wafer_core.lib.rocprofiler.sdk.analyzer import (
    analyze_csv,
    analyze_file,
    analyze_json,
    analyze_rocpd,
)
from wafer_core.lib.rocprofiler.sdk.finder import (
    check_installation,
    find_rocprofv3,
    list_counters,
)
from wafer_core.lib.rocprofiler.sdk.profiler import run_profile
from wafer_core.lib.rocprofiler.sdk.types import (
    AnalysisResult,
    CheckResult,
    KernelMetrics,
    ProfileResult,
)

__all__ = [
    # Installation checking
    "check_installation",
    "find_rocprofv3",
    "list_counters",
    # Profiling
    "run_profile",
    # Analysis
    "analyze_file",
    "analyze_csv",
    "analyze_json",
    "analyze_rocpd",
    # Types
    "CheckResult",
    "ProfileResult",
    "AnalysisResult",
    "KernelMetrics",
]
