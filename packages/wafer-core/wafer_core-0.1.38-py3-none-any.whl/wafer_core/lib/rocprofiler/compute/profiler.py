"""Profiling execution for ROCprofiler-Compute.

Follows Wafer-391: ROCprofiler Tools Architecture.
"""

import subprocess
from pathlib import Path
from typing import Optional
from wafer_core.lib.rocprofiler.compute.types import ProfileResult
from wafer_core.lib.rocprofiler.compute.finder import find_rocprof_compute


def run_profile(
    target_command: list[str],
    workload_name: str,
    workload_path: Optional[Path] = None,
    kernel_filter: Optional[list[str]] = None,
    dispatch_filter: Optional[list[int]] = None,
    block_filter: Optional[list[str]] = None,
    no_roof: bool = False,
    roof_only: bool = False,
    hip_trace: bool = False,
    verbose: int = 0,
) -> ProfileResult:
    """Run rocprof-compute profiling on a command.

    Args:
        target_command: Command to profile (e.g., ["./my_kernel", "arg1"])
        workload_name: Name for the workload (used in output path)
        workload_path: Base path for workload directory (default: ./workloads/<name>)
        kernel_filter: List of kernel names to filter
        dispatch_filter: List of dispatch IDs to filter
        block_filter: List of hardware blocks or metric IDs to filter
        no_roof: Skip roofline data collection (faster profiling)
        roof_only: Profile roofline data only (fastest, no detailed metrics)
        hip_trace: Enable HIP trace collection
        verbose: Verbosity level (0-3)

    Returns:
        ProfileResult with success status and output paths

    Example:
        >>> result = run_profile(
        ...     target_command=["./vcopy", "-n", "1048576"],
        ...     workload_name="vcopy_test",
        ...     block_filter=["SQ", "TCC"]
        ... )
        >>> if result.success:
        ...     print(f"Results in: {result.workload_path}")
    """
    rocprof_path = find_rocprof_compute()
    if not rocprof_path:
        return ProfileResult(
            success=False,
            error="rocprof-compute not found. Install ROCm toolkit."
        )

    # Build command: rocprof-compute profile -n <name> [options] -- <command>
    cmd = [rocprof_path, "profile", "-n", workload_name]

    # Add workload path if specified
    if workload_path:
        cmd.extend(["-p", str(workload_path)])

    # Add filters
    if kernel_filter:
        cmd.extend(["-k"] + kernel_filter)
    if dispatch_filter:
        cmd.extend(["-d"] + [str(d) for d in dispatch_filter])
    if block_filter:
        cmd.extend(["-b"] + block_filter)

    # Add roofline flags
    if no_roof:
        cmd.append("--no-roof")
    if roof_only:
        cmd.append("--roof-only")

    # Add trace flags
    if hip_trace:
        cmd.append("--hip-trace")

    # Add verbosity
    if verbose > 0:
        cmd.extend(["-V"] * verbose)

    # Add target command separator and command
    cmd.append("--")
    cmd.extend(target_command)

    # Execute profiling
    try:
        # Preserve ANSI colors and TTY-style output by setting environment
        import os
        import shutil
        import sys
        env = os.environ.copy()
        env['TERM'] = 'xterm-256color'  # Ensure color support
        env['FORCE_COLOR'] = '1'  # Force color output
        # Set terminal dimensions for proper chart sizing
        env['COLUMNS'] = str(shutil.get_terminal_size().columns)
        env['LINES'] = str(shutil.get_terminal_size().lines)

        # Stream output in real-time while capturing it
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # Combine stderr into stdout
            text=True,
            bufsize=1,  # Line buffered
            env=env
        )

        stdout_lines = []
        for line in process.stdout:
            print(line, end='', file=sys.stderr)  # Stream to stderr in real-time
            stdout_lines.append(line)

        process.wait(timeout=600)  # 10 minutes
        stdout = ''.join(stdout_lines)
        stderr = ''  # Everything was combined into stdout

        result_returncode = process.returncode

        # Determine workload output path
        # rocprof-compute default: ./workloads/<name>/
        if workload_path:
            output_path = Path(workload_path) / workload_name
        else:
            output_path = Path("workloads") / workload_name

        # Find generated files
        output_files = []
        if output_path.exists():
            output_files = [
                str(f) for f in output_path.rglob("*")
                if f.is_file() and f.suffix in [".csv", ".pdf", ".yaml", ".yml"]
            ]

        return ProfileResult(
            success=result_returncode == 0,
            workload_path=str(output_path) if output_path.exists() else None,
            output_files=output_files,
            command=cmd,
            stdout=stdout,
            stderr=stderr,
            error=None if result_returncode == 0 else f"Exit code: {result_returncode}"
        )

    except subprocess.TimeoutExpired:
        return ProfileResult(
            success=False,
            command=cmd,
            error="Profiling timed out after 10 minutes"
        )
    except Exception as e:
        return ProfileResult(
            success=False,
            command=cmd,
            error=str(e)
        )


def run_analysis(
    workload_path: str,
    kernel_filter: Optional[list[str]] = None,
    dispatch_filter: Optional[list[int]] = None,
    block_filter: Optional[list[str]] = None,
    output_file: Optional[str] = None,
    list_stats: bool = False,
    list_metrics: Optional[str] = None,  # Architecture (gfx90a, gfx942, etc.)
    verbose: int = 0,
) -> ProfileResult:
    """Run rocprof-compute analysis on existing profiling data.

    This is useful for re-analyzing data with different filters without re-profiling.

    Args:
        workload_path: Path to workload directory containing profiling results
        kernel_filter: List of kernel IDs to filter
        dispatch_filter: List of dispatch IDs to filter
        block_filter: List of metric IDs to filter
        output_file: Path to save analysis results
        list_stats: List all detected kernels and dispatches
        list_metrics: List available metrics for architecture (e.g., "gfx90a")
        verbose: Verbosity level (0-3)

    Returns:
        ProfileResult with analysis results

    Example:
        >>> result = run_analysis(
        ...     workload_path="./workloads/vcopy_test",
        ...     dispatch_filter=[0, 1],
        ...     output_file="analysis_dispatch_0_1.csv"
        ... )
    """
    rocprof_path = find_rocprof_compute()
    if not rocprof_path:
        return ProfileResult(
            success=False,
            error="rocprof-compute not found. Install ROCm toolkit."
        )

    # Verify workload path exists
    wl_path = Path(workload_path)
    if not wl_path.exists():
        return ProfileResult(
            success=False,
            error=f"Workload path not found: {workload_path}"
        )

    # Build command: rocprof-compute analyze -p <path> [options]
    cmd = [rocprof_path, "analyze", "-p", str(wl_path)]

    # Add list options (these don't generate output files)
    if list_stats:
        cmd.append("--list-stats")
    if list_metrics:
        cmd.extend(["--list-metrics", list_metrics])

    # Add filters
    if kernel_filter:
        cmd.extend(["-k"] + kernel_filter)
    if dispatch_filter:
        cmd.extend(["-d"] + [str(d) for d in dispatch_filter])
    if block_filter:
        cmd.extend(["-b"] + block_filter)

    # Add output file
    if output_file:
        cmd.extend(["-o", output_file])

    # Add verbosity
    if verbose > 0:
        cmd.extend(["-V"] * verbose)

    # Execute analysis
    try:
        # Preserve ANSI colors and TTY-style output by setting environment
        import os
        import shutil
        import sys
        env = os.environ.copy()
        env['TERM'] = 'xterm-256color'  # Ensure color support
        env['FORCE_COLOR'] = '1'  # Force color output
        # Set terminal dimensions for proper chart sizing
        env['COLUMNS'] = str(shutil.get_terminal_size().columns)
        env['LINES'] = str(shutil.get_terminal_size().lines)

        # Stream output in real-time while capturing it
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # Combine stderr into stdout
            text=True,
            bufsize=1,  # Line buffered
            env=env
        )

        stdout_lines = []
        for line in process.stdout:
            print(line, end='', file=sys.stderr)  # Stream to stderr in real-time
            stdout_lines.append(line)

        process.wait(timeout=300)  # 5 minutes
        stdout = ''.join(stdout_lines)
        stderr = ''  # Everything was combined into stdout

        result_returncode = process.returncode

        # Collect output files
        output_files = []
        if output_file and Path(output_file).exists():
            output_files.append(output_file)

        return ProfileResult(
            success=result_returncode == 0,
            workload_path=str(wl_path),
            output_files=output_files,
            command=cmd,
            stdout=stdout,
            stderr=stderr,
            error=None if result_returncode == 0 else f"Exit code: {result_returncode}"
        )

    except subprocess.TimeoutExpired:
        return ProfileResult(
            success=False,
            command=cmd,
            error="Analysis timed out after 5 minutes"
        )
    except Exception as e:
        return ProfileResult(
            success=False,
            command=cmd,
            error=str(e)
        )
