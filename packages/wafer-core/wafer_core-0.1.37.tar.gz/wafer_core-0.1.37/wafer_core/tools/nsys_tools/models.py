"""NSYS Models - Frozen dataclasses for NSYS analysis results.

All models are frozen (immutable) dataclasses following the project's
convention for data/config structures.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class KernelInfo:
    """Information about a CUDA kernel from NSYS profile."""

    name: str
    duration_ms: float = 0.0
    duration_ns: int = 0
    time_percent: float = 0.0
    instances: int = 0
    avg_time_ns: float = 0.0
    min_time_ns: int = 0
    max_time_ns: int = 0
    grid_size: str | None = None
    block_size: str | None = None
    registers_per_thread: int | None = None
    shared_memory_bytes: int | None = None
    memory_throughput_gb_s: float | None = None


@dataclass(frozen=True)
class MemoryTransfer:
    """Information about a memory transfer from NSYS profile."""

    operation: str
    duration_ms: float = 0.0
    size_bytes: int = 0
    throughput_gb_s: float = 0.0
    instances: int = 0


@dataclass(frozen=True)
class TimelineEvent:
    """Timeline event from NSYS profile."""

    event_type: str  # kernel, memcpy, memset, cuda_api, etc.
    name: str
    phase: str = "X"  # Chrome trace phase (B/E/X/i/M/C)
    start_time_ms: float = 0.0
    end_time_ms: float = 0.0
    duration_ms: float = 0.0
    tid: int = 0
    pid: int = 0
    stream_id: int | None = None
    device_id: int | None = None
    context_id: int | None = None
    is_overhead: bool = False


@dataclass(frozen=True)
class DiagnosticEvent:
    """Diagnostic event from NSYS profile."""

    source: str = ""
    level: str = "Info"  # Info, Warning, Error
    text: str = ""
    process_id: int = 0
    time_ms: float = 0.0
    timestamp: int = 0


@dataclass(frozen=True)
class NSYSSummary:
    """Summary of NSYS analysis."""

    gpu: str = "Unknown"
    duration_ms: float = 0.0
    kernel_count: int = 0
    memory_transfers: int = 0
    total_kernel_time_ms: float = 0.0
    total_memory_time_ms: float = 0.0
    event_counts: dict[str, int] = field(default_factory=dict)
    total_events: int = 0
    profiler_overhead_percent: float = 0.0


@dataclass(frozen=True)
class NSYSParseResult:
    """Result of parsing NSYS report."""

    success: bool
    summary: NSYSSummary | None = None
    kernels: tuple[KernelInfo, ...] = ()
    memory_transfers: tuple[MemoryTransfer, ...] = ()
    timeline: tuple[TimelineEvent, ...] = ()
    diagnostics: tuple[DiagnosticEvent, ...] = ()
    error: str | None = None


@dataclass(frozen=True)
class NSYSProfileResult:
    """Result of NSYS profiling execution."""

    success: bool
    output_path: str | None = None
    stdout: str | None = None
    stderr: str | None = None
    error: str | None = None


@dataclass(frozen=True)
class NSYSInstallation:
    """Information about NSYS installation."""

    installed: bool
    path: str | None = None
    version: str | None = None
    install_command: str | None = None
    is_ssh: bool = False
    is_workspace: bool = False
