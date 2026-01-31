"""Binary instrumentation execution for rocprof-sys-instrument.

Follows Wafer-391: ROCprofiler Tools Architecture.
"""

import subprocess
from pathlib import Path
from typing import Optional

from wafer_core.lib.rocprofiler.systems.finder import find_rocprof_sys_instrument
from wafer_core.lib.rocprofiler.systems.types import ProfileResult


def run_instrumentation(
    command: list[str],
    output: Optional[Path] = None,
    function_include: Optional[list[str]] = None,
    function_exclude: Optional[list[str]] = None,
    module_include: Optional[list[str]] = None,
    module_exclude: Optional[list[str]] = None,
    instrument_loops: bool = False,
    coverage: bool = False,
    simulate: bool = False,
    verbose: bool = False,
) -> ProfileResult:
    """Run rocprof-sys-instrument binary instrumentation.

    Instruments a binary using Dyninst to collect function call information,
    coverage data, and other runtime metrics.

    Args:
        command: Target command to instrument and run (e.g., ["./my_app", "arg1"])
        output: Output directory for instrumentation results
        function_include: List of function patterns to instrument (regex/glob)
        function_exclude: List of function patterns to exclude
        module_include: List of module patterns to instrument
        module_exclude: List of module patterns to exclude
        instrument_loops: Enable loop instrumentation
        coverage: Enable code coverage mode
        simulate: Simulate instrumentation (dry run, outputs diagnostics)
        verbose: Enable verbose output

    Returns:
        ProfileResult with success status and output file paths

    Example:
        >>> result = run_instrumentation(
        ...     command=["./my_app"],
        ...     output=Path("./results"),
        ...     function_include=["kernel*", "compute*"],
        ...     coverage=True
        ... )
        >>> if result.success:
        ...     print(f"Instrumentation completed: {result.output_files}")
    """
    rocprof_path = find_rocprof_sys_instrument()
    if not rocprof_path:
        return ProfileResult(
            success=False,
            error="rocprof-sys-instrument not found. Install ROCm toolkit with rocprofiler-systems.",
        )

    # Build rocprof-sys-instrument command
    rocprof_cmd = [rocprof_path]

    # Output directory
    if output:
        output.mkdir(parents=True, exist_ok=True)
        rocprof_cmd.extend(["--output", str(output)])

    # Function filtering
    if function_include:
        for pattern in function_include:
            rocprof_cmd.extend(["--function-include", pattern])

    if function_exclude:
        for pattern in function_exclude:
            rocprof_cmd.extend(["--function-exclude", pattern])

    # Module filtering
    if module_include:
        for pattern in module_include:
            rocprof_cmd.extend(["--module-include", pattern])

    if module_exclude:
        for pattern in module_exclude:
            rocprof_cmd.extend(["--module-exclude", pattern])

    # Instrumentation options
    if instrument_loops:
        rocprof_cmd.append("--instrument-loops")

    if coverage:
        rocprof_cmd.append("--coverage")

    if simulate:
        rocprof_cmd.append("--simulate")

    if verbose:
        rocprof_cmd.append("--verbose")

    # Add separator and target command
    rocprof_cmd.append("--")
    rocprof_cmd.extend(command)

    # Execute instrumentation
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

        # Determine output files
        output_files = []
        search_dir = output if output else Path.cwd()

        # rocprof-sys-instrument generates various diagnostic files
        # When simulating: available.txt, instrumented.txt, excluded.txt, etc.
        if simulate:
            txt_files = list(search_dir.glob("**/*.txt"))
            output_files.extend(txt_files)
            json_files = list(search_dir.glob("**/*.json"))
            output_files.extend(json_files)
        else:
            # Look for runtime output files
            json_files = list(search_dir.glob("**/*-*.json"))
            output_files.extend(json_files)

            txt_files = list(search_dir.glob("**/*.txt"))
            output_files.extend(txt_files)

            # Coverage data files
            cov_files = list(search_dir.glob("**/*.cov"))
            output_files.extend(cov_files)

        # Remove duplicates and convert to strings
        output_files = [str(f) for f in sorted(set(output_files))]

        return ProfileResult(
            success=result_returncode == 0,
            output_files=output_files,
            command=rocprof_cmd,
            stdout=stdout,
            stderr=stderr,
            error=None if result_returncode == 0 else f"Exit code: {result_returncode}",
        )

    except subprocess.TimeoutExpired:
        return ProfileResult(
            success=False,
            command=rocprof_cmd,
            error="Instrumentation timed out after 10 minutes",
        )
    except FileNotFoundError as e:
        return ProfileResult(
            success=False, command=rocprof_cmd, error=f"Command not found: {e}"
        )
    except Exception as e:
        return ProfileResult(success=False, command=rocprof_cmd, error=str(e))
