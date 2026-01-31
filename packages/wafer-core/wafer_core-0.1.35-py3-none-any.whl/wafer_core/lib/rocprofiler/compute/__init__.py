"""ROCprofiler-Compute - Launch GUI, run profiling, and analyze ROCprofiler data.

This module provides core functionality for the rocprof-compute tool integration.
Follows the architecture pattern established in Wafer-391: ROCprofiler Tools Architecture.

Public API:
    - check_installation: Check if rocprof-compute is installed
    - find_rocprof_compute: Find rocprof-compute executable path
    - launch_gui: Build launch command for external rocprof-compute GUI
    - launch_gui_server: Launch bundled GUI viewer (Python-based)
    - get_launch_command: Build command array for spawning
    - run_profile: Execute rocprof-compute profiling
    - run_analysis: Execute rocprof-compute analysis on existing data
    - parse_workload: Parse workload directory and extract metrics
    - CheckResult: Installation check result
    - ProfileResult: Profile/analysis result
    - LaunchResult: Launch command result
    - GuiStatus: Server status (managed by extension)
    - KernelStats: Kernel statistics
    - RooflineData: Roofline model data
    - AnalysisResult: Analysis result with kernels and roofline
"""

from wafer_core.lib.rocprofiler.compute.finder import (
    check_installation,
    find_rocprof_compute,
)
from wafer_core.lib.rocprofiler.compute.gui_server import (
    launch_gui,
    get_launch_command,
    DEFAULT_PORT,
)
from wafer_core.lib.rocprofiler.compute.gui.launcher import (
    launch_gui_server,
    launch_gui_server_threaded,
)
from wafer_core.lib.rocprofiler.compute.profiler import (
    run_profile,
    run_analysis,
)
from wafer_core.lib.rocprofiler.compute.analyzer import (
    parse_workload,
    parse_csv,
    parse_yaml,
)
from wafer_core.lib.rocprofiler.compute.types import (
    CheckResult,
    ProfileResult,
    LaunchResult,
    GuiStatus,
    KernelStats,
    RooflineData,
    AnalysisResult,
)

__all__ = [
    # Installation checking
    "check_installation",
    "find_rocprof_compute",
    # GUI server (external binary)
    "launch_gui",
    "get_launch_command",
    "DEFAULT_PORT",
    # GUI server (bundled viewer)
    "launch_gui_server",
    "launch_gui_server_threaded",
    # Profiling and analysis
    "run_profile",
    "run_analysis",
    # Parsing
    "parse_workload",
    "parse_csv",
    "parse_yaml",
    # Types
    "CheckResult",
    "ProfileResult",
    "LaunchResult",
    "GuiStatus",
    "KernelStats",
    "RooflineData",
    "AnalysisResult",
]
