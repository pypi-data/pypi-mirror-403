"""Installation detection for rocprof-compute.

Follows Wafer-391: ROCprofiler Tools Architecture.
"""

import os
import platform
import shutil
import subprocess
from typing import Optional
from wafer_core.lib.rocprofiler.compute.types import CheckResult


# Known rocprof-compute installation paths by platform
ROCPROF_COMPUTE_PATHS = {
    "linux": [
        "/opt/rocm/bin/rocprof-compute",
        "/usr/bin/rocprof-compute",
        "/usr/local/bin/rocprof-compute",
    ],
}


def _get_platform() -> str:
    """Get normalized platform name."""
    system = platform.system().lower()
    return "linux"  # ROCm only supports Linux


def _get_install_command() -> str:
    """Get platform-appropriate install command."""
    return "Install ROCm from https://rocm.docs.amd.com/"


def find_rocprof_compute() -> Optional[str]:
    """Find rocprof-compute executable on the system.

    Searches in:
    1. System PATH
    2. Known ROCm installation paths

    Returns:
        Path to rocprof-compute executable, or None if not found
    """
    # Check PATH first
    rocprof = shutil.which("rocprof-compute")
    if rocprof:
        return rocprof

    # Check known installation paths
    plat = _get_platform()
    for path in ROCPROF_COMPUTE_PATHS.get(plat, []):
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path

    return None


def check_installation() -> CheckResult:
    """Check if rocprof-compute is installed.

    Returns:
        CheckResult with installation status and details
    """
    rocprof_path = find_rocprof_compute()

    if rocprof_path is None:
        return CheckResult(
            installed=False,
            path=None,
            version=None,
            install_command=_get_install_command()
        )

    # Try to get version
    version = None
    try:
        result = subprocess.run(
            [rocprof_path, "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            # Parse version from output
            version_line = result.stdout.strip()
            # Extract version number if present (format: rocprof-compute X.Y.Z)
            import re
            match = re.search(r'(\d+\.\d+\.\d+)', version_line)
            if match:
                version = match.group(1)
            else:
                # Use full output if no version number found
                version = version_line
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        # Version check failed, but tool is still installed
        pass

    return CheckResult(
        installed=True,
        path=rocprof_path,
        version=version,
        install_command=None
    )
