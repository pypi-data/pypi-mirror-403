"""Type definitions for ROCprofiler-SDK tool.

Follows Wafer-391: ROCprofiler Tools Architecture.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class CheckResult:
    """Result of checking rocprofv3 installation.

    Attributes:
        installed: Whether rocprofv3 is installed
        path: Path to rocprofv3 executable
        version: Version string if available
        install_command: Installation instructions if not installed
    """

    installed: bool
    path: Optional[str] = None
    version: Optional[str] = None
    install_command: Optional[str] = None


@dataclass(frozen=True)
class ProfileResult:
    """Result of running rocprofv3 profiling.

    Attributes:
        success: Whether profiling completed successfully
        output_files: List of generated output file paths
        command: Command that was executed
        stdout: Standard output from rocprofv3
        stderr: Standard error from rocprofv3
        error: Error message if unsuccessful
    """

    success: bool
    output_files: Optional[list[str]] = None
    command: Optional[list[str]] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    error: Optional[str] = None


@dataclass(frozen=True)
class KernelMetrics:
    """Metrics for a single kernel execution.

    Attributes:
        name: Kernel name
        duration_ns: Execution duration in nanoseconds
        grid_size: Grid dimensions (if available)
        block_size: Block dimensions (if available)
        registers_per_thread: Registers used per thread (if available)
        lds_per_workgroup: Local data share per workgroup in bytes (if available)
        vgprs: Number of vector GPRs used (if available)
        sgprs: Number of scalar GPRs used (if available)
    """

    name: str
    duration_ns: Optional[float] = None
    grid_size: Optional[str] = None
    block_size: Optional[str] = None
    registers_per_thread: Optional[int] = None
    lds_per_workgroup: Optional[int] = None
    vgprs: Optional[int] = None
    sgprs: Optional[int] = None


@dataclass(frozen=True)
class AnalysisResult:
    """Result of analyzing rocprofiler output files.

    Attributes:
        success: Whether analysis completed successfully
        file_format: Detected file format ("csv", "json", "rocpd")
        kernels: List of kernel metrics
        summary: Summary statistics dictionary
        error: Error message if unsuccessful
    """

    success: bool
    file_format: str
    kernels: Optional[list[KernelMetrics]] = None
    summary: Optional[dict] = None
    error: Optional[str] = None
