"""Profiling execution for rocprofv3.

Follows Wafer-391: ROCprofiler Tools Architecture.
"""

import subprocess
from pathlib import Path
from typing import Optional

from wafer_core.lib.rocprofiler.sdk.finder import find_rocprofv3
from wafer_core.lib.rocprofiler.sdk.types import ProfileResult


def run_profile(
    command: list[str],
    output_dir: Optional[Path] = None,
    output_format: str = "csv",
    counters: Optional[list[str]] = None,
    kernel_include_regex: Optional[str] = None,
    kernel_exclude_regex: Optional[str] = None,
    trace_hip_runtime: bool = False,
    trace_hip_compiler: bool = False,
    trace_hsa: bool = False,
    trace_marker: bool = False,
    trace_memory_copy: bool = False,
) -> ProfileResult:
    """Run rocprofv3 profiling on a command.

    Args:
        command: Target command to profile (e.g., ["./my_app", "arg1"])
        output_dir: Directory for output files (default: cwd)
        output_format: Output format ("csv", "json", "rocpd", "pftrace")
        counters: List of hardware counters to collect
        kernel_include_regex: Include only kernels matching this regex
        kernel_exclude_regex: Exclude kernels matching this regex (applied after include)
        trace_hip_runtime: Enable HIP runtime API tracing
        trace_hip_compiler: Enable HIP compiler generated code tracing
        trace_hsa: Enable HSA API tracing
        trace_marker: Enable ROCTx marker tracing
        trace_memory_copy: Enable memory copy operation tracing

    Returns:
        ProfileResult with success status and output file paths

    Example:
        >>> result = run_profile(
        ...     command=["./my_kernel"],
        ...     output_dir=Path("./results"),
        ...     output_format="csv",
        ...     kernel_include_regex="vectorAdd|matmul",
        ...     trace_hip_runtime=True
        ... )
        >>> if result.success:
        ...     print(f"Output files: {result.output_files}")
    """
    rocprof_path = find_rocprofv3()
    if not rocprof_path:
        return ProfileResult(
            success=False, error="rocprofv3 not found. Install ROCm toolkit."
        )

    # Build rocprofv3 command
    rocprof_cmd = [rocprof_path]

    if output_dir:
        rocprof_cmd.extend(["--output-directory", str(output_dir)])

    # Enable kernel tracing by default (required by rocprofv3)
    rocprof_cmd.append("--kernel-trace")

    # Add additional tracing options if specified
    if trace_hip_runtime:
        rocprof_cmd.append("--hip-runtime-trace")
    if trace_hip_compiler:
        rocprof_cmd.append("--hip-compiler-trace")
    if trace_hsa:
        rocprof_cmd.append("--hsa-trace")
    if trace_marker:
        rocprof_cmd.append("--marker-trace")
    if trace_memory_copy:
        rocprof_cmd.append("--memory-copy-trace")

    # Add format-specific flags
    if output_format == "csv":
        rocprof_cmd.extend(["--output-format", "csv"])
    elif output_format == "json":
        rocprof_cmd.extend(["--output-format", "json"])
    elif output_format == "rocpd":
        # rocpd is the default SQLite database format
        rocprof_cmd.extend(["--output-format", "rocpd"])
        if output_dir:
            rocprof_cmd.extend(["--output-file", "results.db"])
    elif output_format == "pftrace":
        rocprof_cmd.extend(["--output-format", "pftrace"])
    elif output_format == "otf2":
        rocprof_cmd.extend(["--output-format", "otf2"])
    else:
        return ProfileResult(
            success=False, error=f"Unsupported output format: {output_format}"
        )

    # Add hardware counters if specified
    if counters:
        # rocprofv3 uses --pmc for performance monitoring counters
        rocprof_cmd.append("--pmc")
        rocprof_cmd.extend(counters)

    # Add kernel filtering if specified
    if kernel_include_regex:
        rocprof_cmd.extend(["--kernel-include-regex", kernel_include_regex])
    if kernel_exclude_regex:
        rocprof_cmd.extend(["--kernel-exclude-regex", kernel_exclude_regex])

    # Add separator and target command
    rocprof_cmd.append("--")
    rocprof_cmd.extend(command)

    # Execute profiling
    try:
        import sys
        # Stream output in real-time while capturing it
        process = subprocess.Popen(
            rocprof_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # Combine stderr into stdout
            text=True,
            bufsize=1,  # Line buffered
        )

        stdout_lines = []
        for line in process.stdout:
            print(line, end='', file=sys.stderr)  # Stream to stderr in real-time
            stdout_lines.append(line)

        process.wait(timeout=600)  # 10 minutes
        stdout = ''.join(stdout_lines)
        stderr = ''  # Everything was combined into stdout
        result_returncode = process.returncode

        # Determine output files (rocprofv3 generates them in output_dir/hostname/pid/)
        output_files = []
        search_dir = output_dir if output_dir else Path.cwd()

        # rocprofv3 creates subdirectories: output_dir/hostname/pid/
        # We need to search recursively in subdirectories
        if output_format == "csv":
            # CSV format generates multiple files:
            # - *_kernel_trace.csv (always)
            # - *_counter_collection.csv (when --pmc used)
            # - *_hip_api_trace.csv (when --trace-hip-runtime used)
            # - *_memory_copy_trace.csv (when --trace-memory-copy used)
            # - *_marker_api_trace.csv (when --trace-marker used)
            # - *_agent_info.csv (always)
            # Find all CSV files in the output directory
            output_files = list(search_dir.glob("*/*.csv"))
            if not output_files:
                output_files = list(search_dir.glob("**/*.csv"))
        elif output_format == "json":
            # JSON format generates: *_results.json
            output_files = list(search_dir.glob("*/*_results.json"))
            if not output_files:
                output_files = list(search_dir.glob("**/*_results.json"))
        elif output_format == "rocpd":
            # rocpd format generates: *_results.db
            output_files = list(search_dir.glob("*/*_results.db"))
            if not output_files:
                output_files = list(search_dir.glob("**/*_results.db"))
        elif output_format == "pftrace":
            # Perfetto format generates: *.pftrace
            output_files = list(search_dir.glob("*/*.pftrace"))
            if not output_files:
                output_files = list(search_dir.glob("**/*.pftrace"))
        elif output_format == "otf2":
            # OTF2 format generates: *.otf2
            output_files = list(search_dir.glob("*/*.otf2"))
            if not output_files:
                output_files = list(search_dir.glob("**/*.otf2"))

        return ProfileResult(
            success=result_returncode == 0,
            output_files=[str(f) for f in output_files],
            command=rocprof_cmd,
            stdout=stdout,
            stderr=stderr,
            error=None
            if result_returncode == 0
            else f"Exit code: {result_returncode}",
        )

    except subprocess.TimeoutExpired:
        return ProfileResult(
            success=False,
            command=rocprof_cmd,
            error="Profiling timed out after 10 minutes",
        )
    except FileNotFoundError as e:
        return ProfileResult(
            success=False, command=rocprof_cmd, error=f"Command not found: {e}"
        )
    except Exception as e:
        return ProfileResult(success=False, command=rocprof_cmd, error=str(e))
