"""Type definitions for ROCprofiler-Systems tools.

Follows Wafer-391: ROCprofiler Tools Architecture.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class CheckResult:
    """Result of checking rocprof-sys installation.

    Attributes:
        installed: Whether any rocprof-sys tools are installed
        paths: Dictionary mapping tool names to paths (e.g., {"run": "/opt/rocm/bin/rocprof-sys-run"})
        versions: Dictionary mapping tool names to versions
        install_command: Installation instructions if not installed
    """

    installed: bool
    paths: dict[str, str] = None
    versions: dict[str, str] = None
    install_command: Optional[str] = None

    def __post_init__(self):
        # Ensure paths and versions are dicts even if None passed
        if self.paths is None:
            object.__setattr__(self, "paths", {})
        if self.versions is None:
            object.__setattr__(self, "versions", {})


@dataclass(frozen=True)
class ProfileResult:
    """Result of running rocprof-sys profiling.

    Attributes:
        success: Whether profiling completed successfully
        output_files: List of generated output file paths
        command: Command that was executed
        stdout: Standard output from rocprof-sys
        stderr: Standard error from rocprof-sys
        error: Error message if unsuccessful
    """

    success: bool
    output_files: Optional[list[str]] = None
    command: Optional[list[str]] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    error: Optional[str] = None


@dataclass(frozen=True)
class SystemMetrics:
    """Metrics for system-level profiling.

    Attributes:
        function_name: Function or region name
        call_count: Number of times called
        total_time_ns: Total execution time in nanoseconds
        mean_time_ns: Mean execution time in nanoseconds
        min_time_ns: Minimum execution time in nanoseconds
        max_time_ns: Maximum execution time in nanoseconds
        stddev_ns: Standard deviation in nanoseconds
        cpu_time_ns: CPU time in nanoseconds (if available)
        gpu_time_ns: GPU time in nanoseconds (if available)
    """

    function_name: str
    call_count: Optional[int] = None
    total_time_ns: Optional[float] = None
    mean_time_ns: Optional[float] = None
    min_time_ns: Optional[float] = None
    max_time_ns: Optional[float] = None
    stddev_ns: Optional[float] = None
    cpu_time_ns: Optional[float] = None
    gpu_time_ns: Optional[float] = None


@dataclass(frozen=True)
class AnalysisResult:
    """Result of analyzing rocprof-sys output files.

    Attributes:
        success: Whether analysis completed successfully
        file_format: Detected file format ("perfetto", "json", "text", "rocpd")
        functions: List of function metrics
        summary: Summary statistics dictionary
        metadata: Metadata from profiling run (PID, hostname, etc.)
        error: Error message if unsuccessful
    """

    success: bool
    file_format: str
    functions: Optional[list[SystemMetrics]] = None
    summary: Optional[dict] = None
    metadata: Optional[dict] = None
    error: Optional[str] = None
