"""GUI server command building for rocprof-compute.

Follows Wafer-391: ROCprofiler Tools Architecture.

Note: This module does NOT manage process lifecycle - that's handled by the
extension handler. Core layer only provides command building.
"""

from pathlib import Path
from wafer_core.lib.rocprofiler.compute.types import LaunchResult
from wafer_core.lib.rocprofiler.compute.finder import check_installation


# rocprof-compute only supports port 8050
DEFAULT_PORT = 8050


def get_launch_command(
    folder_path: str,
    port: int = DEFAULT_PORT,
    rocprof_path: str = 'rocprof-compute'
) -> list[str]:
    """Build command array for launching rocprof-compute GUI.

    Args:
        folder_path: Path to folder containing ROCprofiler results
        port: Port number for GUI server (default: 8050)
        rocprof_path: Path to rocprof-compute executable (default: 'rocprof-compute')

    Returns:
        Command array ready for subprocess.run() or spawn()

    Example:
        >>> cmd = get_launch_command('/path/to/results', 8050)
        >>> # cmd == ['rocprof-compute', 'analyze', '-p', '/path/to/results', '--gui', '8050']
        >>> cmd = get_launch_command('/path/to/results', 9000, '/opt/rocm/bin/rocprof-compute')
        >>> # cmd == ['/opt/rocm/bin/rocprof-compute', 'analyze', '-p', '/path/to/results', '--gui', '9000']
    """
    # Note: --gui takes the port as an optional argument, not as --port flag
    # Syntax: rocprof-compute analyze -p PATH --gui [PORT]
    return [
        rocprof_path,
        'analyze',
        '-p', str(folder_path),
        '--gui', str(port)
    ]


def launch_gui(folder_path: str, port: int = DEFAULT_PORT) -> LaunchResult:
    """Build launch command and validate prerequisites.

    This function does NOT spawn the process - it only validates
    and builds the command. Process management is handled by:
    - CLI layer (subprocess.run, blocks)
    - Extension layer (spawn, non-blocking)

    Args:
        folder_path: Path to folder containing ROCprofiler results
        port: Port number for GUI server (default: 8050)

    Returns:
        LaunchResult with command array and metadata

    Raises:
        No exceptions - returns error in LaunchResult instead
    """
    # Check installation
    install_info = check_installation()
    if not install_info.installed:
        return LaunchResult(
            success=False,
            error=f"rocprof-compute not installed. {install_info.install_command}"
        )

    # Verify folder exists
    folder = Path(folder_path).resolve()
    if not folder.exists():
        return LaunchResult(
            success=False,
            error=f"Folder not found: {folder_path}"
        )
    if not folder.is_dir():
        return LaunchResult(
            success=False,
            error=f"Path is not a directory: {folder_path}"
        )

    # Build command using discovered path (or fall back to 'rocprof-compute' if path is None)
    rocprof_path = install_info.path or 'rocprof-compute'
    cmd = get_launch_command(str(folder), port, rocprof_path)

    return LaunchResult(
        success=True,
        command=cmd,
        url=f"http://localhost:{port}",
        port=port,
        folder=str(folder),
        error=None
    )
