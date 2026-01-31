"""Type definitions for TraceLens tool.

All types use frozen dataclasses for immutability.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class TraceFormat(str, Enum):
    """Supported trace formats.
    
    WHY str base: Allows direct string comparison and serialization.
    """
    PYTORCH = "pytorch"
    ROCPROF = "rocprof"
    JAX = "jax"
    AUTO = "auto"  # Auto-detect from file patterns


@dataclass(frozen=True)
class CheckResult:
    """Result of checking TraceLens installation.
    
    Attributes:
        installed: Whether TraceLens is available
        version: Version string from pip if available
        commands_available: List of TraceLens CLI commands found on PATH
        install_command: Installation instructions if not installed
    """
    installed: bool
    version: Optional[str] = None
    commands_available: Optional[list[str]] = None
    install_command: Optional[str] = None


@dataclass(frozen=True)
class ReportResult:
    """Result of generating a performance report.
    
    Attributes:
        success: Whether generation completed successfully
        output_path: Path to generated Excel report
        trace_format: Detected/used trace format
        summary: Optional summary statistics dict
        error: Error message if unsuccessful
        stdout: Standard output from command
        stderr: Standard error from command
    """
    success: bool
    output_path: Optional[str] = None
    trace_format: Optional[str] = None
    summary: Optional[dict] = None
    error: Optional[str] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None


@dataclass(frozen=True)
class CompareResult:
    """Result of comparing two performance reports.
    
    Attributes:
        success: Whether comparison completed successfully
        output_path: Path to comparison Excel file
        sheets_compared: List of sheet names compared
        summary: Comparison summary statistics
        error: Error message if unsuccessful
    """
    success: bool
    output_path: Optional[str] = None
    sheets_compared: Optional[list[str]] = None
    summary: Optional[dict] = None
    error: Optional[str] = None


@dataclass(frozen=True)
class CollectiveReportResult:
    """Result of generating multi-rank collective report.
    
    Attributes:
        success: Whether generation completed successfully
        output_path: Path to generated report
        world_size: Number of ranks analyzed
        error: Error message if unsuccessful
    """
    success: bool
    output_path: Optional[str] = None
    world_size: Optional[int] = None
    error: Optional[str] = None
