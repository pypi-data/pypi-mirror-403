"""NSYS Discovery - Find nsys executable on various platforms.

Cross-platform NSYS detection following the same pattern as the CLI
and extension implementations.

NOTE: On macOS, NSYS CLI is NOT available. NVIDIA only provides the
GUI viewer (nsys-ui). macOS users must use remote analysis.
"""

import os
import platform
import shutil
import subprocess

from .models import NSYSInstallation

# Known NSYS installation paths by platform
# NOTE: On macOS, NVIDIA only provides the GUI viewer (nsys-ui), NOT the CLI tool.
# The nsys CLI is only available on Linux. macOS users must use remote analysis.
NSYS_PATHS = {
    "linux": [
        "/usr/bin/nsys",
        "/usr/local/bin/nsys",
        "/usr/local/cuda/bin/nsys",
        "/opt/nvidia/nsight-systems/bin/nsys",
        "/opt/nvidia/nsight-systems-cli/bin/nsys",
    ],
    # macOS: nsys CLI not available - only GUI viewer exists
    # Set to empty list to always fall back to remote analysis
    "darwin": [],
    "windows": [
        r"C:\Program Files\NVIDIA Corporation\Nsight Systems\bin\nsys.exe",
        r"C:\Program Files\NVIDIA Corporation\Nsight Systems 2024.1\target-windows-x64\nsys.exe",
        r"C:\Program Files\NVIDIA Corporation\Nsight Systems 2023.4\target-windows-x64\nsys.exe",
    ],
}


def _get_platform() -> str:
    """Get normalized platform name."""
    system = platform.system().lower()
    if system == "darwin":
        return "darwin"
    elif system == "windows":
        return "windows"
    return "linux"


def is_macos() -> bool:
    """Check if running on macOS."""
    return _get_platform() == "darwin"


def find_nsys() -> str | None:
    """Find nsys executable.

    Search order:
    1. PATH environment variable
    2. Common platform-specific installation paths

    Returns:
        Path to nsys executable if found, None otherwise
    """
    # On macOS, nsys CLI is not available
    if is_macos():
        return None

    # Check PATH first
    which_result = shutil.which("nsys")
    if which_result:
        return which_result

    # Check common paths
    plat = _get_platform()
    paths = NSYS_PATHS.get(plat, [])

    for path in paths:
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path

    return None


def get_nsys_version(nsys_path: str) -> str | None:
    """Get NSYS version string.

    Args:
        nsys_path: Path to nsys executable

    Returns:
        Version string (e.g., "2024.1.1") or None if failed
    """
    try:
        result = subprocess.run(
            [nsys_path, "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        # Output format: "NVIDIA Nsight Systems version 2024.1.1.59-241133297320v0"
        for line in result.stdout.split("\n"):
            if "version" in line.lower():
                parts = line.split("version")
                if len(parts) > 1:
                    version = parts[1].strip().split("-")[0].strip()
                    return version
        return result.stdout.strip()
    except (subprocess.TimeoutExpired, OSError, FileNotFoundError):
        return None


def get_install_command() -> str:
    """Get platform-appropriate install command for NSYS.

    Returns:
        Install command/instructions string
    """
    plat = _get_platform()

    if plat == "darwin":
        return (
            "NSYS CLI not available on macOS. "
            "Use --remote flag or --target for remote analysis."
        )
    elif plat == "windows":
        return (
            "Download NVIDIA Nsight Systems from: "
            "https://developer.nvidia.com/nsight-systems"
        )
    else:
        return (
            "apt install -y nsight-systems-cli  # Ubuntu/Debian\n"
            "# Or download from: https://developer.nvidia.com/nsight-systems"
        )


def check_installation() -> NSYSInstallation:
    """Check if NSYS is installed and get details.

    Returns:
        NSYSInstallation with installation status and details
    """
    nsys_path = find_nsys()

    if nsys_path is None:
        return NSYSInstallation(
            installed=False,
            install_command=get_install_command(),
        )

    version = get_nsys_version(nsys_path)

    return NSYSInstallation(
        installed=True,
        path=nsys_path,
        version=version,
    )
