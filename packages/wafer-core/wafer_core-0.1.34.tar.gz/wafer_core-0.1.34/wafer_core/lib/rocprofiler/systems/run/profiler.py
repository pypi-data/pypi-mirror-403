"""Profiling execution for rocprof-sys-run.

Follows Wafer-391: ROCprofiler Tools Architecture.
"""

import subprocess
from pathlib import Path
from typing import Optional

from wafer_core.lib.rocprofiler.systems.finder import find_rocprof_sys_run
from wafer_core.lib.rocprofiler.systems.types import ProfileResult


def run_systems_profile(
    command: list[str],
    output_dir: Optional[Path] = None,
    trace: bool = True,
    profile: bool = False,
    flat_profile: bool = False,
    sample: bool = False,
    host: bool = False,
    device: bool = False,
    wait: Optional[float] = None,
    duration: Optional[float] = None,
    use_rocm: bool = True,
    use_sampling: bool = False,
    use_kokkosp: bool = False,
    use_mpip: bool = False,
    use_rocpd: bool = False,
    backends: Optional[list[str]] = None,
) -> ProfileResult:
    """Run rocprof-sys-run system profiling on a command.

    Args:
        command: Target command to profile (e.g., ["./my_app", "arg1"])
        output_dir: Directory for output files (default: cwd)
        trace: Generate detailed trace (Perfetto output)
        profile: Generate call-stack-based profile
        flat_profile: Generate flat profile (conflicts with profile)
        sample: Enable sampling profiling
        host: Enable sampling host-based metrics (CPU freq, memory, etc.)
        device: Enable sampling device-based metrics (GPU temp, memory, etc.)
        wait: Wait time before collecting data (seconds)
        duration: Duration of data collection (seconds)
        use_rocm: Enable ROCm backend (default: True)
        use_sampling: Enable sampling backend
        use_kokkosp: Enable Kokkos profiling backend
        use_mpip: Enable MPI profiling backend
        use_rocpd: Enable rocpd database output (SQLite)
        backends: List of backends for --include flag (overrides use_* flags).
                  Valid values: 'rocm', 'kokkosp', 'mpip', 'rcclp', 'ompt', etc.

    Returns:
        ProfileResult with success status and output file paths

    Example:
        >>> result = run_systems_profile(
        ...     command=["./my_app"],
        ...     output_dir=Path("./results"),
        ...     trace=True,
        ...     profile=True,
        ...     use_rocm=True
        ... )
        >>> if result.success:
        ...     print(f"Output files: {result.output_files}")
    """
    rocprof_path = find_rocprof_sys_run()
    if not rocprof_path:
        return ProfileResult(
            success=False,
            error="rocprof-sys-run not found. Install ROCm toolkit with rocprofiler-systems.",
        )

    # Build rocprof-sys-run command
    rocprof_cmd = [rocprof_path]

    # Output directory
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        rocprof_cmd.extend(["--output", str(output_dir)])

    # Profiling modes
    if trace:
        rocprof_cmd.append("--trace")

    if profile and flat_profile:
        return ProfileResult(
            success=False,
            error="Cannot use both --profile and --flat-profile. Choose one.",
        )

    if profile:
        rocprof_cmd.append("--profile")
    elif flat_profile:
        rocprof_cmd.append("--flat-profile")

    # Sampling
    if sample:
        rocprof_cmd.append("--sample")

    # Host/device metrics
    if host:
        rocprof_cmd.append("--host")
    if device:
        rocprof_cmd.append("--device")

    # Timing
    if wait is not None:
        rocprof_cmd.extend(["--wait", str(wait)])
    if duration is not None:
        rocprof_cmd.extend(["--duration", str(duration)])

    # Backends
    # Note: --include is for specific backends (kokkosp, mpip, rocm, etc.)
    # while --use-* flags control broader backend types (sampling, rocm, etc.)
    # We use --use-* flags as they're the primary way to enable backends
    if backends:
        # If explicit backends list provided, use --include for each
        for backend in backends:
            rocprof_cmd.extend(["--include", backend])
    else:
        # Use individual --use-* flags (recommended approach)
        if use_rocm:
            rocprof_cmd.append("--use-rocm")
        if use_sampling:
            rocprof_cmd.append("--use-sampling")
        if use_kokkosp:
            rocprof_cmd.append("--use-kokkosp")
        if use_mpip:
            rocprof_cmd.append("--use-mpip")

    # rocpd output (SQLite database)
    if use_rocpd:
        # Set environment variable to enable rocpd output
        import os

        env = os.environ.copy()
        env["ROCPROFSYS_USE_ROCPD"] = "1"
    else:
        env = None

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
            env=env,
        )

        stdout_lines = []
        for line in process.stdout:
            print(line, end='', file=sys.stderr)  # Stream to stderr in real-time
            stdout_lines.append(line)

        process.wait(timeout=600)  # 10 minutes
        stdout = ''.join(stdout_lines)
        stderr = ''  # Everything was combined into stdout
        result_returncode = process.returncode

        # Determine output files
        output_files = []
        search_dir = output_dir if output_dir else Path.cwd()

        # rocprof-sys-run generates multiple output files
        # Common patterns:
        # - perfetto-trace.proto (Perfetto trace)
        # - wall_clock-[PID].json (wall clock timing)
        # - metadata-[PID].json (metadata)
        # - functions-[PID].json (function data)
        # - wall-clock.txt (text summary)
        # - *.db (rocpd database if enabled)

        if trace:
            # Look for Perfetto trace
            perfetto_files = list(search_dir.glob("**/perfetto-trace.proto"))
            output_files.extend(perfetto_files)

        # Look for JSON outputs
        json_files = list(search_dir.glob("**/*-*.json"))
        output_files.extend(json_files)

        # Look for text outputs
        txt_files = list(search_dir.glob("**/*.txt"))
        output_files.extend(txt_files)

        # Look for rocpd database
        if use_rocpd:
            db_files = list(search_dir.glob("**/*.db"))
            output_files.extend(db_files)

        # Remove duplicates and convert to strings
        output_files = [str(f) for f in sorted(set(output_files))]

        # Enhanced error detection for common failure cases
        error_msg = None
        if result_returncode != 0:
            # Check for common error patterns
            if result_returncode == 255:
                # Exit code 255 often means command not found or execution failed
                # Check if the target binary exists
                target_binary = Path(command[0])

                if not target_binary.exists():
                    error_msg = f"Command not found: '{command[0]}' does not exist"
                elif not target_binary.is_file():
                    error_msg = f"Invalid command: '{command[0]}' is not a file"
                elif not target_binary.stat().st_mode & 0o111:
                    error_msg = f"Permission denied: '{command[0]}' is not executable"
                else:
                    error_msg = f"Profiling failed with exit code {result_returncode}. The target application may have crashed or failed to start."
            else:
                error_msg = f"Exit code: {result_returncode}"

        return ProfileResult(
            success=result_returncode == 0,
            output_files=output_files,
            command=rocprof_cmd,
            stdout=stdout,
            stderr=stderr,
            error=error_msg,
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
