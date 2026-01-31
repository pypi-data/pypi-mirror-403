"""Installation detection for rocprofv3.

Follows Wafer-391: ROCprofiler Tools Architecture.
"""

import os
import platform
import re
import shutil
import subprocess
from typing import Optional

from wafer_core.lib.rocprofiler.sdk.types import CheckResult


# Known rocprofv3 installation paths by platform
ROCPROFV3_PATHS = {
    "linux": [
        "/opt/rocm/bin/rocprofv3",
        "/usr/bin/rocprofv3",
        "/usr/local/bin/rocprofv3",
    ],
}


def _get_platform() -> str:
    """Get normalized platform name."""
    system = platform.system().lower()
    return "linux"  # ROCm only supports Linux


def _get_install_command() -> str:
    """Get platform-appropriate install command."""
    return "Install ROCm from https://rocm.docs.amd.com/"


def find_rocprofv3() -> Optional[str]:
    """Find rocprofv3 executable on the system.

    Searches in:
    1. System PATH
    2. Known ROCm installation paths

    Returns:
        Path to rocprofv3 executable, or None if not found
    """
    # Check PATH first
    rocprof = shutil.which("rocprofv3")
    if rocprof:
        return rocprof

    # Check known installation paths
    plat = _get_platform()
    for path in ROCPROFV3_PATHS.get(plat, []):
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path

    return None


def check_installation() -> CheckResult:
    """Check if rocprofv3 is installed.

    Returns:
        CheckResult with installation status and details
    """
    rocprof_path = find_rocprofv3()

    if rocprof_path is None:
        return CheckResult(
            installed=False,
            path=None,
            version=None,
            install_command=_get_install_command(),
        )

    # Try to get version
    version = None
    try:
        result = subprocess.run(
            [rocprof_path, "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            # Parse version from output
            version_line = result.stdout.strip()
            # Extract version number if present (format: rocprofv3 X.Y.Z or similar)
            match = re.search(r"(\d+\.\d+\.\d+)", version_line)
            if match:
                version = match.group(1)
            else:
                # Use full output if no version number found
                version = version_line
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        # Version check failed, but tool is still installed
        pass

    return CheckResult(
        installed=True, path=rocprof_path, version=version, install_command=None
    )


def list_counters() -> tuple[bool, Optional[str], Optional[str]]:
    """List available performance counters for the current GPU.

    Returns:
        Tuple of (success, output, error_message)
    """
    rocprof_path = find_rocprofv3()

    if rocprof_path is None:
        return (False, None, "rocprofv3 not found. Please install ROCm.")

    try:
        result = subprocess.run(
            [rocprof_path, "--list-avail"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            return (True, result.stdout, None)
        else:
            return (False, None, f"rocprofv3 --list-avail failed: {result.stderr}")

    except subprocess.TimeoutExpired:
        return (False, None, "Timeout while listing counters")
    except Exception as e:
        return (False, None, f"Error listing counters: {str(e)}")
