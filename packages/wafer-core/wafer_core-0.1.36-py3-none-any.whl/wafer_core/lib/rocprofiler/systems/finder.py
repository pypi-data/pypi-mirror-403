"""Installation detection for rocprof-sys tools.

Follows Wafer-391: ROCprofiler Tools Architecture.
"""

import os
import platform
import re
import shutil
import subprocess
from typing import Optional

from wafer_core.lib.rocprofiler.systems.types import CheckResult


# Known rocprof-sys installation paths by platform
ROCPROF_SYS_PATHS = {
    "linux": {
        "run": [
            "/opt/rocm/bin/rocprof-sys-run",
            "/usr/bin/rocprof-sys-run",
            "/usr/local/bin/rocprof-sys-run",
        ],
        "sample": [
            "/opt/rocm/bin/rocprof-sys-sample",
            "/usr/bin/rocprof-sys-sample",
            "/usr/local/bin/rocprof-sys-sample",
        ],
        "instrument": [
            "/opt/rocm/bin/rocprof-sys-instrument",
            "/usr/bin/rocprof-sys-instrument",
            "/usr/local/bin/rocprof-sys-instrument",
        ],
        "avail": [
            "/opt/rocm/bin/rocprof-sys-avail",
            "/usr/bin/rocprof-sys-avail",
            "/usr/local/bin/rocprof-sys-avail",
        ],
    }
}


def _get_platform() -> str:
    """Get normalized platform name."""
    system = platform.system().lower()
    return "linux"  # ROCm only supports Linux


def _get_install_command() -> str:
    """Get platform-appropriate install command."""
    return "Install ROCm from https://rocm.docs.amd.com/"


def _find_tool(tool_name: str, command: str) -> Optional[str]:
    """Find a rocprof-sys tool executable on the system.

    Args:
        tool_name: Name of the tool (e.g., "run", "sample")
        command: Command name (e.g., "rocprof-sys-run")

    Returns:
        Path to tool executable, or None if not found
    """
    # Check PATH first
    tool_path = shutil.which(command)
    if tool_path:
        return tool_path

    # Check known installation paths
    plat = _get_platform()
    paths = ROCPROF_SYS_PATHS.get(plat, {}).get(tool_name, [])
    for path in paths:
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path

    return None


def find_rocprof_sys_run() -> Optional[str]:
    """Find rocprof-sys-run executable on the system.

    Searches in:
    1. System PATH
    2. Known ROCm installation paths

    Returns:
        Path to rocprof-sys-run executable, or None if not found
    """
    return _find_tool("run", "rocprof-sys-run")


def find_rocprof_sys_sample() -> Optional[str]:
    """Find rocprof-sys-sample executable on the system.

    Returns:
        Path to rocprof-sys-sample executable, or None if not found
    """
    return _find_tool("sample", "rocprof-sys-sample")


def find_rocprof_sys_instrument() -> Optional[str]:
    """Find rocprof-sys-instrument executable on the system.

    Returns:
        Path to rocprof-sys-instrument executable, or None if not found
    """
    return _find_tool("instrument", "rocprof-sys-instrument")


def find_rocprof_sys_avail() -> Optional[str]:
    """Find rocprof-sys-avail executable on the system.

    Returns:
        Path to rocprof-sys-avail executable, or None if not found
    """
    return _find_tool("avail", "rocprof-sys-avail")


def _get_tool_version(tool_path: str) -> Optional[str]:
    """Get version of a rocprof-sys tool.

    Args:
        tool_path: Path to the tool executable

    Returns:
        Version string, or None if unable to determine
    """
    try:
        result = subprocess.run(
            [tool_path, "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            # Parse version from output
            version_line = result.stdout.strip()
            # Extract version number if present (format: rocprof-sys X.Y.Z or similar)
            match = re.search(r"(\d+\.\d+\.\d+)", version_line)
            if match:
                return match.group(1)
            # Use full output if no version number found
            return version_line
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        pass

    return None


def check_installation() -> CheckResult:
    """Check if rocprof-sys tools are installed.

    Checks for all rocprof-sys tools and returns details about what's available.

    Returns:
        CheckResult with installation status and tool paths
    """
    tools = {
        "run": find_rocprof_sys_run(),
        "sample": find_rocprof_sys_sample(),
        "instrument": find_rocprof_sys_instrument(),
        "avail": find_rocprof_sys_avail(),
    }

    # Check if at least one tool is installed
    installed_tools = {k: v for k, v in tools.items() if v is not None}

    if not installed_tools:
        return CheckResult(
            installed=False,
            paths={},
            versions={},
            install_command=_get_install_command(),
        )

    # Get versions for installed tools
    versions = {}
    for tool_name, tool_path in installed_tools.items():
        version = _get_tool_version(tool_path)
        if version:
            versions[tool_name] = version

    return CheckResult(
        installed=True,
        paths=installed_tools,
        versions=versions,
        install_command=None,
    )
