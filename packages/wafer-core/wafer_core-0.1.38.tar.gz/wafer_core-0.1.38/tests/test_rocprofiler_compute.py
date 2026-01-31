"""Unit tests for ROCprofiler-Compute tool.

Tests the core functionality of rocprof-compute installation checking
and GUI launch command building.

Follows similar testing patterns from the codebase.
"""

import subprocess
from unittest.mock import Mock, patch

from wafer_core.lib.rocprofiler.compute import (
    DEFAULT_PORT,
    CheckResult,
    LaunchResult,
    check_installation,
    find_rocprof_compute,
    get_launch_command,
    launch_gui,
)


class TestCheckResult:
    """Test CheckResult dataclass."""

    def test_creates_not_installed_result(self) -> None:
        """Test creating result for tool not installed."""
        result = CheckResult(installed=False, install_command="Install ROCm")
        assert result.installed is False
        assert result.path is None
        assert result.version is None
        assert result.install_command == "Install ROCm"

    def test_creates_installed_result(self) -> None:
        """Test creating result for installed tool."""
        result = CheckResult(installed=True, path="/opt/rocm/bin/rocprof-compute", version="6.0.0")
        assert result.installed is True
        assert result.path == "/opt/rocm/bin/rocprof-compute"
        assert result.version == "6.0.0"
        assert result.install_command is None


class TestLaunchResult:
    """Test LaunchResult dataclass."""

    def test_creates_success_result(self) -> None:
        """Test creating successful launch result."""
        result = LaunchResult(
            success=True,
            command=["rocprof-compute", "analyze", "-p", "/data", "--gui", "--port", "8050"],
            url="http://localhost:8050",
            port=8050,
            folder="/data",
        )
        assert result.success is True
        assert result.command is not None
        assert result.url == "http://localhost:8050"
        assert result.port == 8050
        assert result.folder == "/data"
        assert result.error is None

    def test_creates_error_result(self) -> None:
        """Test creating error result."""
        result = LaunchResult(success=False, error="Tool not installed")
        assert result.success is False
        assert result.command is None
        assert result.error == "Tool not installed"


class TestFindRocprofCompute:
    """Test find_rocprof_compute function."""

    @patch("shutil.which")
    def test_finds_in_path(self, mock_which: Mock) -> None:
        """Test finding rocprof-compute in system PATH."""
        mock_which.return_value = "/usr/bin/rocprof-compute"

        result = find_rocprof_compute()

        assert result == "/usr/bin/rocprof-compute"
        mock_which.assert_called_once_with("rocprof-compute")

    @patch("shutil.which")
    @patch("os.path.isfile")
    @patch("os.access")
    def test_finds_in_known_paths(
        self, mock_access: Mock, mock_isfile: Mock, mock_which: Mock
    ) -> None:
        """Test finding rocprof-compute in known ROCm paths."""
        mock_which.return_value = None  # Not in PATH
        mock_isfile.return_value = True
        mock_access.return_value = True

        result = find_rocprof_compute()

        assert result == "/opt/rocm/bin/rocprof-compute"

    @patch("shutil.which")
    @patch("os.path.isfile")
    @patch("os.access")
    def test_returns_none_when_not_found(
        self, mock_access: Mock, mock_isfile: Mock, mock_which: Mock
    ) -> None:
        """Test returns None when rocprof-compute not found."""
        mock_which.return_value = None  # Not in PATH
        mock_isfile.return_value = False  # Not in known paths

        result = find_rocprof_compute()

        assert result is None


class TestCheckInstallation:
    """Test check_installation function."""

    @patch("wafer_core.lib.rocprofiler.compute.finder.find_rocprof_compute")
    @patch("subprocess.run")
    def test_returns_installed_with_version(self, mock_run: Mock, mock_find: Mock) -> None:
        """Test check returns installed status with version."""
        mock_find.return_value = "/opt/rocm/bin/rocprof-compute"
        mock_run.return_value = Mock(returncode=0, stdout="rocprof-compute 6.0.0\n")

        result = check_installation()

        assert isinstance(result, CheckResult)
        assert result.installed is True
        assert result.path == "/opt/rocm/bin/rocprof-compute"
        assert result.version == "6.0.0"
        assert result.install_command is None

    @patch("wafer_core.lib.rocprofiler.compute.finder.find_rocprof_compute")
    def test_returns_not_installed(self, mock_find: Mock) -> None:
        """Test check returns not installed status."""
        mock_find.return_value = None

        result = check_installation()

        assert isinstance(result, CheckResult)
        assert result.installed is False
        assert result.path is None
        assert result.version is None
        assert result.install_command is not None

    @patch("wafer_core.lib.rocprofiler.compute.finder.find_rocprof_compute")
    @patch("subprocess.run")
    def test_handles_version_check_failure(self, mock_run: Mock, mock_find: Mock) -> None:
        """Test handles version check failure gracefully."""
        mock_find.return_value = "/opt/rocm/bin/rocprof-compute"
        mock_run.side_effect = subprocess.TimeoutExpired("cmd", 10)

        result = check_installation()

        assert isinstance(result, CheckResult)
        assert result.installed is True
        assert result.path == "/opt/rocm/bin/rocprof-compute"
        assert result.version is None  # Version check failed but tool is installed


class TestGetLaunchCommand:
    """Test get_launch_command function."""

    def test_builds_command_with_defaults(self) -> None:
        """Test building command with default port."""
        cmd = get_launch_command("/data/results")

        # Note: --gui takes the port as an optional argument, not as --port flag
        # Syntax: rocprof-compute analyze -p PATH --gui [PORT]
        assert cmd == ["rocprof-compute", "analyze", "-p", "/data/results", "--gui", "8050"]

    def test_builds_command_with_custom_port(self) -> None:
        """Test building command with custom port."""
        cmd = get_launch_command("/data/results", port=9000)

        assert cmd == ["rocprof-compute", "analyze", "-p", "/data/results", "--gui", "9000"]


class TestLaunchGui:
    """Test launch_gui function."""

    @patch("wafer_core.lib.rocprofiler.compute.gui_server.check_installation")
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.is_dir")
    def test_returns_success_for_valid_inputs(
        self, mock_is_dir: Mock, mock_exists: Mock, mock_check: Mock
    ) -> None:
        """Test returns success result for valid inputs."""
        mock_check.return_value = CheckResult(installed=True, path="/opt/rocm/bin/rocprof-compute")
        mock_exists.return_value = True
        mock_is_dir.return_value = True

        result = launch_gui("/data/results", port=8050)

        assert isinstance(result, LaunchResult)
        assert result.success is True
        assert result.command is not None
        assert result.url == "http://localhost:8050"
        assert result.port == 8050
        assert "/data/results" in str(result.folder)
        assert result.error is None

    @patch("wafer_core.lib.rocprofiler.compute.gui_server.check_installation")
    def test_returns_error_when_not_installed(self, mock_check: Mock) -> None:
        """Test returns error when rocprof-compute not installed."""
        mock_check.return_value = CheckResult(installed=False, install_command="Install ROCm")

        result = launch_gui("/data/results")

        assert isinstance(result, LaunchResult)
        assert result.success is False
        assert result.error is not None
        assert "not installed" in result.error

    @patch("wafer_core.lib.rocprofiler.compute.gui_server.check_installation")
    @patch("pathlib.Path.exists")
    def test_returns_error_when_folder_not_found(self, mock_exists: Mock, mock_check: Mock) -> None:
        """Test returns error when folder doesn't exist."""
        mock_check.return_value = CheckResult(installed=True, path="/opt/rocm/bin/rocprof-compute")
        mock_exists.return_value = False

        result = launch_gui("/nonexistent/folder")

        assert isinstance(result, LaunchResult)
        assert result.success is False
        assert result.error is not None
        assert "not found" in result.error

    @patch("wafer_core.lib.rocprofiler.compute.gui_server.check_installation")
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.is_dir")
    def test_returns_error_when_path_not_directory(
        self, mock_is_dir: Mock, mock_exists: Mock, mock_check: Mock
    ) -> None:
        """Test returns error when path is not a directory."""
        mock_check.return_value = CheckResult(installed=True, path="/opt/rocm/bin/rocprof-compute")
        mock_exists.return_value = True
        mock_is_dir.return_value = False

        result = launch_gui("/path/to/file.txt")

        assert isinstance(result, LaunchResult)
        assert result.success is False
        assert result.error is not None
        assert "not a directory" in result.error


class TestConstants:
    """Test module constants."""

    def test_default_port(self) -> None:
        """Test DEFAULT_PORT constant."""
        assert DEFAULT_PORT == 8050
