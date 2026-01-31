"""Installation detection for TraceLens.

Detects if TraceLens is installed and which commands are available.
"""

import shutil
import subprocess
from typing import Optional

from wafer_core.lib.tracelens.types import CheckResult


# Known TraceLens CLI commands
TRACELENS_COMMANDS = [
    "TraceLens_generate_perf_report_pytorch",
    "TraceLens_generate_perf_report_rocprof",
    "TraceLens_compare_perf_reports_pytorch",
    "TraceLens_generate_multi_rank_collective_report_pytorch",
]


def find_tracelens_command(command: str) -> Optional[str]:
    """Find a TraceLens command on the system.
    
    Args:
        command: Command name to find
        
    Returns:
        Path to command if found, None otherwise
    """
    return shutil.which(command)


def _get_version() -> Optional[str]:
    """Get TraceLens version from pip.
    
    WHY best-effort: Version detection shouldn't fail the check.
    
    Returns:
        Version string if found, None otherwise
    """
    try:
        result = subprocess.run(
            ["pip", "show", "TraceLens"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                if line.startswith("Version:"):
                    return line.split(":", 1)[1].strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        # Version check is best-effort
        pass
    return None


def check_installation() -> CheckResult:
    """Check if TraceLens is installed.
    
    Logic:
    1. Check each known command via shutil.which()
    2. Collect available commands
    3. If none found, return with install instructions
    4. If found, attempt to get version via pip
    
    Returns:
        CheckResult with installation status and details
    """
    available_commands = []
    
    for cmd in TRACELENS_COMMANDS:
        if find_tracelens_command(cmd):
            available_commands.append(cmd)
    
    if not available_commands:
        return CheckResult(
            installed=False,
            version=None,
            commands_available=None,
            install_command="pip install git+https://github.com/AMD-AGI/TraceLens.git",
        )
    
    version = _get_version()
    
    return CheckResult(
        installed=True,
        version=version,
        commands_available=available_commands,
        install_command=None,
    )
