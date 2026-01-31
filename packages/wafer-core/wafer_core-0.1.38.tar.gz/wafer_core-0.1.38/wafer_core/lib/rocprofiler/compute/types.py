"""Type definitions for ROCprofiler-Compute tool.

Follows Wafer-391: ROCprofiler Tools Architecture.
"""

from dataclasses import dataclass
from typing import Optional, Any


@dataclass(frozen=True)
class CheckResult:
    """Result of checking rocprof-compute installation.

    Attributes:
        installed: Whether rocprof-compute is installed
        path: Path to rocprof-compute executable
        version: Version string if available
        install_command: Installation instructions if not installed
    """
    installed: bool
    path: Optional[str] = None
    version: Optional[str] = None
    install_command: Optional[str] = None


@dataclass(frozen=True)
class LaunchResult:
    """Result of building launch command for GUI server.

    Attributes:
        success: Whether command was built successfully
        command: Command array to spawn
        url: Expected URL of GUI server
        port: Port number
        folder: Folder path being analyzed
        error: Error message if unsuccessful
    """
    success: bool
    command: Optional[list[str]] = None
    url: Optional[str] = None
    port: Optional[int] = None
    folder: Optional[str] = None
    error: Optional[str] = None


@dataclass(frozen=True)
class GuiStatus:
    """Current status of GUI server.

    Note: This is managed by the extension handler, not by core.
    Core layer doesn't manage process lifecycle.

    Attributes:
        running: Whether server is currently running
        url: URL of running server
        port: Port number
        folder: Folder being analyzed
    """
    running: bool
    url: Optional[str] = None
    port: Optional[int] = None
    folder: Optional[str] = None


@dataclass(frozen=True)
class ProfileResult:
    """Result of running rocprof-compute profiling or analysis.

    Attributes:
        success: Whether operation succeeded
        workload_path: Path to workload directory
        output_files: List of generated files
        command: Command that was executed
        stdout: Standard output
        stderr: Standard error
        error: Error message if unsuccessful
    """
    success: bool
    workload_path: Optional[str] = None
    output_files: Optional[list[str]] = None
    command: Optional[list[str]] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    error: Optional[str] = None


@dataclass(frozen=True)
class KernelStats:
    """Statistics for a single kernel.

    Attributes:
        kernel_id: Kernel ID/index
        kernel_name: Name of the kernel
        dispatches: Number of dispatches
        duration_ns: Total duration in nanoseconds
        gpu_util: GPU utilization percentage
        memory_bw: Memory bandwidth in GB/s
        metrics: Additional metrics dictionary
    """
    kernel_id: int
    kernel_name: str
    dispatches: int
    duration_ns: Optional[float] = None
    gpu_util: Optional[float] = None
    memory_bw: Optional[float] = None
    metrics: Optional[dict[str, Any]] = None


@dataclass(frozen=True)
class RooflineData:
    """Roofline model data for a kernel.

    Attributes:
        kernel_name: Name of the kernel
        ai: Arithmetic intensity (FLOPS/Byte)
        perf: Performance (GFLOPS)
        roof_type: Roofline type (FP32, FP64, etc.)
    """
    kernel_name: str
    ai: float
    perf: float
    roof_type: str


@dataclass(frozen=True)
class AnalysisResult:
    """Result of analyzing rocprof-compute output.

    Attributes:
        success: Whether analysis succeeded
        workload_path: Path to workload directory
        architecture: GPU architecture (gfx90a, gfx942, etc.)
        kernels: List of kernel statistics
        roofline: Roofline data if available
        summary: Summary statistics
        error: Error message if unsuccessful
    """
    success: bool
    workload_path: Optional[str] = None
    architecture: Optional[str] = None
    kernels: Optional[list[KernelStats]] = None
    roofline: Optional[list[RooflineData]] = None
    summary: Optional[dict[str, Any]] = None
    error: Optional[str] = None
