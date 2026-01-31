"""Sampling profiling execution for rocprof-sys-sample.

Follows Wafer-391: ROCprofiler Tools Architecture.
"""

import subprocess
from pathlib import Path
from typing import Optional

from wafer_core.lib.rocprofiler.systems.finder import find_rocprof_sys_sample
from wafer_core.lib.rocprofiler.systems.types import ProfileResult


def run_sampling(
    command: Optional[list[str]] = None,
    output_dir: Optional[Path] = None,
    trace: bool = False,
    profile: bool = False,
    flat_profile: bool = False,
    host: bool = False,
    device: bool = False,
    freq: Optional[int] = None,
    wait: Optional[float] = None,
    duration: Optional[float] = None,
    cpus: Optional[list[int]] = None,
    gpus: Optional[list[int]] = None,
    cputime: bool = False,
    realtime: bool = False,
) -> ProfileResult:
    """Run rocprof-sys-sample sampling profiling.

    Can be used standalone (attach to running processes) or with a command.

    Args:
        command: Target command to profile (optional - can attach to running process)
        output_dir: Directory for output files (default: cwd)
        trace: Generate detailed trace (Perfetto output)
        profile: Generate call-stack-based profile
        flat_profile: Generate flat profile (conflicts with profile)
        host: Enable sampling host-based metrics
        device: Enable sampling device-based metrics
        freq: Sampling frequency in Hz (default: system dependent)
        wait: Wait time before collecting data (seconds)
        duration: Duration of data collection (seconds)
        cpus: List of CPU IDs to sample (e.g., [0, 1, 2])
        gpus: List of GPU IDs to sample
        cputime: Sample based on CPU time
        realtime: Sample based on real (wall) time

    Returns:
        ProfileResult with success status and output file paths

    Example:
        >>> # Sample a command
        >>> result = run_sampling(
        ...     command=["./my_app"],
        ...     output_dir=Path("./results"),
        ...     trace=True,
        ...     freq=1000
        ... )

        >>> # Standalone sampling (attach to running process)
        >>> result = run_sampling(
        ...     output_dir=Path("./results"),
        ...     profile=True,
        ...     duration=10
        ... )
    """
    rocprof_path = find_rocprof_sys_sample()
    if not rocprof_path:
        return ProfileResult(
            success=False,
            error="rocprof-sys-sample not found. Install ROCm toolkit with rocprofiler-systems.",
        )

    # Build rocprof-sys-sample command
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

    # Host/device metrics
    if host:
        rocprof_cmd.append("--host")
    if device:
        rocprof_cmd.append("--device")

    # Sampling frequency
    if freq is not None:
        rocprof_cmd.extend(["--freq", str(freq)])

    # Timing
    if wait is not None:
        rocprof_cmd.extend(["--wait", str(wait)])
    if duration is not None:
        rocprof_cmd.extend(["--duration", str(duration)])

    # CPU/GPU selection
    if cpus:
        for cpu_id in cpus:
            rocprof_cmd.extend(["--cpus", str(cpu_id)])
    if gpus:
        for gpu_id in gpus:
            rocprof_cmd.extend(["--gpus", str(gpu_id)])

    # Sampling type
    if cputime:
        rocprof_cmd.append("--cputime")
    if realtime:
        rocprof_cmd.append("--realtime")

    # Add command if provided (for command profiling mode)
    if command:
        # rocprof-sys-sample requires -- separator before the command
        rocprof_cmd.append("--")
        rocprof_cmd.extend(command)

    # Execute sampling
    try:
        import sys
        timeout_val = max(600, (duration or 0) + 60) if duration else 600

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

        process.wait(timeout=timeout_val)
        stdout = ''.join(stdout_lines)
        stderr = ''  # Everything was combined into stdout
        result_returncode = process.returncode

        # Determine output files
        output_files = []
        search_dir = output_dir if output_dir else Path.cwd()

        # rocprof-sys-sample generates similar outputs to run
        if trace:
            perfetto_files = list(search_dir.glob("**/perfetto-trace.proto"))
            output_files.extend(perfetto_files)

        # Look for JSON outputs
        json_files = list(search_dir.glob("**/*-*.json"))
        output_files.extend(json_files)

        # Look for text outputs
        txt_files = list(search_dir.glob("**/*.txt"))
        output_files.extend(txt_files)

        # Remove duplicates and convert to strings
        output_files = [str(f) for f in sorted(set(output_files))]

        # Enhanced error detection for common failure cases
        error_msg = None
        if result_returncode != 0:
            # Check for common error patterns
            if result_returncode == 255 and command:
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
                    error_msg = f"Sampling failed with exit code {result_returncode}. The target application may have crashed or failed to start."
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
            error=f"Sampling timed out after {duration or 600} seconds",
        )
    except FileNotFoundError as e:
        return ProfileResult(
            success=False, command=rocprof_cmd, error=f"Command not found: {e}"
        )
    except Exception as e:
        return ProfileResult(success=False, command=rocprof_cmd, error=str(e))
