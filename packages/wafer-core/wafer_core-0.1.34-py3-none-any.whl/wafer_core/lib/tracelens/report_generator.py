"""Generate performance reports using TraceLens.

Wraps TraceLens CLI commands for report generation.
"""

import subprocess
from pathlib import Path
from typing import Optional

from wafer_core.lib.tracelens.types import (
    TraceFormat,
    ReportResult,
    CollectiveReportResult,
)
from wafer_core.lib.tracelens.finder import find_tracelens_command


def _detect_trace_format(trace_path: Path) -> TraceFormat:
    """Auto-detect trace format from file.
    
    Detection logic:
    - .db, .rocpd, or "rocprof" in name → ROCPROF
    - .pb or "xplane" in name → JAX
    - Default to PYTORCH for .json files
    
    Args:
        trace_path: Path to trace file
        
    Returns:
        Detected TraceFormat
    """
    suffix = trace_path.suffix.lower()
    name = trace_path.name.lower()
    
    # rocprofv3 traces
    if suffix in [".db", ".rocpd"] or "rocprof" in name:
        return TraceFormat.ROCPROF
    
    # JAX traces use protobuf format
    if suffix == ".pb" or "xplane" in name:
        return TraceFormat.JAX
    
    # Default to PyTorch for .json files
    return TraceFormat.PYTORCH


def _get_command_for_format(trace_format: TraceFormat) -> Optional[str]:
    """Get TraceLens command name for a trace format.
    
    Args:
        trace_format: The trace format
        
    Returns:
        Command name or None if unsupported
    """
    format_to_command = {
        TraceFormat.PYTORCH: "TraceLens_generate_perf_report_pytorch",
        TraceFormat.ROCPROF: "TraceLens_generate_perf_report_rocprof",
        TraceFormat.JAX: "TraceLens_generate_perf_report_jax",
    }
    return format_to_command.get(trace_format)


def generate_perf_report(
    trace_path: str,
    output_path: Optional[str] = None,
    trace_format: TraceFormat = TraceFormat.AUTO,
    short_kernel_study: bool = False,
    kernel_details: bool = False,
) -> ReportResult:
    """Generate performance report from a trace file.
    
    Logic:
    1. Validate trace file exists
    2. Auto-detect format if needed
    3. Find appropriate TraceLens command
    4. Build and execute command
    5. Return result with output path
    
    Args:
        trace_path: Path to input trace file (JSON, zip, gz)
        output_path: Path for output Excel file (default: <trace_name>_report.xlsx)
        trace_format: Trace format (auto-detect if AUTO)
        short_kernel_study: Include short kernel analysis
        kernel_details: Include detailed kernel breakdown
        
    Returns:
        ReportResult with success status and output path
    """
    trace_file = Path(trace_path)
    
    # Validate file exists
    if not trace_file.exists():
        return ReportResult(
            success=False,
            error=f"Trace file not found: {trace_path}"
        )
    
    # Detect format if auto
    actual_format = trace_format
    if trace_format == TraceFormat.AUTO:
        actual_format = _detect_trace_format(trace_file)
    
    # Get command for format
    cmd_name = _get_command_for_format(actual_format)
    if not cmd_name:
        return ReportResult(
            success=False,
            error=f"Unsupported trace format: {trace_format}"
        )
    
    # Find command on PATH
    cmd_path = find_tracelens_command(cmd_name)
    if not cmd_path:
        return ReportResult(
            success=False,
            error=f"TraceLens command not found: {cmd_name}. "
                  f"Install with: pip install git+https://github.com/AMD-AGI/TraceLens.git"
        )
    
    # Build command
    cmd = [cmd_path, "--profile_json_path", str(trace_file)]
    
    if output_path:
        cmd.extend(["--output", output_path])
    
    if short_kernel_study:
        cmd.append("--short_kernel_study")
    
    if kernel_details:
        cmd.append("--kernel_details")
    
    # Execute with 15-minute timeout (large traces need more time)
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=900,
        )
        
        if result.returncode == 0:
            # Determine output path - TraceLens creates report in same dir by default
            actual_output = output_path
            if not actual_output:
                # TraceLens naming convention
                actual_output = str(trace_file.with_suffix("")) + "_perf_report.xlsx"
            
            return ReportResult(
                success=True,
                output_path=actual_output,
                trace_format=actual_format.value,
                stdout=result.stdout,
                stderr=result.stderr,
            )
        else:
            return ReportResult(
                success=False,
                error=f"Command failed with exit code {result.returncode}",
                stdout=result.stdout,
                stderr=result.stderr,
            )
    
    except subprocess.TimeoutExpired:
        return ReportResult(
            success=False,
            error="Timeout: Report generation took too long (>15 minutes). "
                  "Try running TraceLens directly: "
                  f"TraceLens_generate_perf_report_pytorch --profile_json_path {trace_path}"
        )
    except Exception as e:
        return ReportResult(
            success=False,
            error=f"Error running TraceLens: {str(e)}"
        )


def generate_collective_report(
    trace_dir: str,
    world_size: int,
    output_path: Optional[str] = None,
) -> CollectiveReportResult:
    """Generate multi-rank collective performance report.
    
    Logic:
    1. Validate trace directory exists
    2. Find the multi-rank collective command
    3. Build and execute command with 10-minute timeout
    4. Return result with status
    
    Args:
        trace_dir: Directory containing trace files for all ranks
        world_size: Number of ranks (GPUs)
        output_path: Optional output path for report
        
    Returns:
        CollectiveReportResult with success status
    """
    cmd_name = "TraceLens_generate_multi_rank_collective_report_pytorch"
    cmd_path = find_tracelens_command(cmd_name)
    
    if not cmd_path:
        return CollectiveReportResult(
            success=False,
            error=f"TraceLens command not found: {cmd_name}. "
                  f"Install with: pip install git+https://github.com/AMD-AGI/TraceLens.git"
        )
    
    trace_dir_path = Path(trace_dir)
    if not trace_dir_path.is_dir():
        return CollectiveReportResult(
            success=False,
            error=f"Trace directory not found: {trace_dir}"
        )
    
    # Build command
    cmd = [
        cmd_path,
        "--trace_dir", str(trace_dir_path),
        "--world_size", str(world_size),
    ]
    
    if output_path:
        cmd.extend(["--output", output_path])
    
    # Execute with 10-minute timeout (multi-rank analysis is slower)
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,
        )
        
        if result.returncode == 0:
            return CollectiveReportResult(
                success=True,
                output_path=output_path,
                world_size=world_size,
            )
        else:
            error_msg = result.stderr.strip() if result.stderr else f"Exit code {result.returncode}"
            return CollectiveReportResult(
                success=False,
                error=error_msg,
            )
    
    except subprocess.TimeoutExpired:
        return CollectiveReportResult(
            success=False,
            error="Timeout: Multi-rank analysis took too long (>10 minutes)"
        )
    except Exception as e:
        return CollectiveReportResult(
            success=False,
            error=str(e)
        )
