"""NSYS Tools - Shared NSYS parsing and profiling utilities.

This package provides shared logic for NSYS (Nsight Systems) profiling and analysis
that can be used by both the CLI (wafer-cli) and API (wafer-api).

Components:
- discovery: Find nsys executable on various platforms
- parser: Parse nsys stats CSV output into structured data
- models: Frozen dataclasses for results
- profiler: Profiling execution helpers
"""

from .discovery import (
    find_nsys,
    get_nsys_version,
    get_install_command,
    is_macos,
    NSYSInstallation,
)

from .models import (
    KernelInfo,
    MemoryTransfer,
    NSYSSummary,
    NSYSParseResult,
    NSYSProfileResult,
)

from .parser import (
    parse_kernel_csv,
    parse_memory_csv,
    run_nsys_stats,
    analyze_report,
)

__all__ = [
    # Discovery
    "find_nsys",
    "get_nsys_version",
    "get_install_command",
    "is_macos",
    "NSYSInstallation",
    # Models
    "KernelInfo",
    "MemoryTransfer",
    "NSYSSummary",
    "NSYSParseResult",
    "NSYSProfileResult",
    # Parser
    "parse_kernel_csv",
    "parse_memory_csv",
    "run_nsys_stats",
    "analyze_report",
]
