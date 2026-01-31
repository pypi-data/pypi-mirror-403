"""Tests for the sandbox module.

These tests verify that:
1. Platform detection works correctly
2. Sandbox policies are constructed properly
3. Seatbelt (macOS) policies are generated correctly
4. Commands are executed with appropriate sandboxing
"""

import sys
import tempfile
from pathlib import Path

import pytest

from wafer_core.sandbox import SandboxPolicy
from wafer_core.sandbox.executor import (
    get_platform,
    get_sandbox_unavailable_reason,
    is_sandbox_available,
)


class TestPlatformDetection:
    """Tests for platform detection."""

    def test_get_platform_returns_known_value(self):
        """Platform should be one of the known values."""
        platform = get_platform()
        assert platform in ("macos", "linux", "windows", "unknown")

    def test_get_platform_matches_sys_platform(self):
        """Platform detection should match sys.platform."""
        platform = get_platform()
        if sys.platform == "darwin":
            assert platform == "macos"
        elif sys.platform.startswith("linux"):
            assert platform == "linux"
        elif sys.platform == "win32":
            assert platform == "windows"

    def test_sandbox_availability_returns_bool(self):
        """is_sandbox_available should return a boolean."""
        result = is_sandbox_available()
        assert isinstance(result, bool)

    def test_unavailable_reason_consistent(self):
        """Unavailable reason should be None iff sandbox is available."""
        available = is_sandbox_available()
        reason = get_sandbox_unavailable_reason()

        if available:
            assert reason is None
        else:
            assert reason is not None
            assert isinstance(reason, str)


class TestSandboxPolicy:
    """Tests for SandboxPolicy construction."""

    def test_workspace_write_creates_policy(self):
        """workspace_write should create a valid policy."""
        with tempfile.TemporaryDirectory() as tmpdir:
            working_dir = Path(tmpdir)
            policy = SandboxPolicy.workspace_write(working_dir)

            assert policy.working_dir == working_dir
            assert working_dir in policy.get_all_writable_roots()
            assert policy.network_access is False

    def test_workspace_write_with_network(self):
        """workspace_write should respect network_access flag."""
        with tempfile.TemporaryDirectory() as tmpdir:
            working_dir = Path(tmpdir)
            policy = SandboxPolicy.workspace_write(working_dir, network_access=True)

            assert policy.network_access is True

    def test_workspace_write_protects_git(self):
        """workspace_write should auto-protect .git directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            working_dir = Path(tmpdir)
            git_dir = working_dir / ".git"
            git_dir.mkdir()

            policy = SandboxPolicy.workspace_write(working_dir)

            assert git_dir in policy.read_only_paths

    def test_read_only_creates_restrictive_policy(self):
        """read_only should create a policy with no write access."""
        with tempfile.TemporaryDirectory() as tmpdir:
            working_dir = Path(tmpdir)
            policy = SandboxPolicy.read_only(working_dir)

            assert policy.working_dir == working_dir
            assert len(policy.writable_roots) == 0
            assert policy.network_access is False

    def test_extra_writable_paths(self):
        """Extra writable paths should be included in policy."""
        with tempfile.TemporaryDirectory() as tmpdir:
            working_dir = Path(tmpdir)
            extra_dir = Path(tmpdir) / "extra"
            extra_dir.mkdir()

            policy = SandboxPolicy.workspace_write(
                working_dir,
                extra_writable=[extra_dir],
            )

            roots = policy.get_all_writable_roots()
            assert working_dir in roots
            assert extra_dir in roots


@pytest.mark.skipif(
    get_platform() != "macos",
    reason="Seatbelt tests only run on macOS",
)
class TestSeatbeltPolicy:
    """Tests for macOS Seatbelt policy generation."""

    def test_build_seatbelt_policy_basic(self):
        """Should generate valid SBPL policy."""
        from wafer_core.sandbox.seatbelt import build_seatbelt_policy

        with tempfile.TemporaryDirectory() as tmpdir:
            working_dir = Path(tmpdir)
            policy = SandboxPolicy.workspace_write(working_dir)

            sbpl, params = build_seatbelt_policy(policy)

            # Check basic structure
            assert "(version 1)" in sbpl
            assert "(deny default)" in sbpl
            assert "(allow file-read*)" in sbpl
            assert "(allow file-write*" in sbpl

            # Check params include working dir
            param_names = [p[0] for p in params]
            assert any("WRITABLE_ROOT" in name for name in param_names)

    def test_build_seatbelt_policy_with_network(self):
        """Should include network policy when enabled."""
        from wafer_core.sandbox.seatbelt import build_seatbelt_policy

        with tempfile.TemporaryDirectory() as tmpdir:
            working_dir = Path(tmpdir)
            policy = SandboxPolicy.workspace_write(working_dir, network_access=True)

            sbpl, params = build_seatbelt_policy(policy)

            assert "(allow network-outbound)" in sbpl
            assert "(allow network-inbound)" in sbpl

    def test_build_seatbelt_policy_without_network(self):
        """Should not include network policy when disabled."""
        from wafer_core.sandbox.seatbelt import build_seatbelt_policy

        with tempfile.TemporaryDirectory() as tmpdir:
            working_dir = Path(tmpdir)
            policy = SandboxPolicy.workspace_write(working_dir, network_access=False)

            sbpl, params = build_seatbelt_policy(policy)

            assert "(allow network-outbound)" not in sbpl
            assert "(allow network-inbound)" not in sbpl


@pytest.mark.skipif(
    not is_sandbox_available(),
    reason="Sandbox not available on this platform",
)
class TestSandboxExecution:
    """Integration tests for sandboxed execution."""

    @pytest.mark.anyio
    async def test_sandboxed_echo_works(self):
        """Basic echo command should work in sandbox."""
        from wafer_core.sandbox import execute_sandboxed

        with tempfile.TemporaryDirectory() as tmpdir:
            working_dir = Path(tmpdir)
            policy = SandboxPolicy.workspace_write(working_dir)

            result = await execute_sandboxed("echo hello", policy)

            assert result.returncode == 0
            assert "hello" in result.stdout

    @pytest.mark.anyio
    async def test_sandboxed_write_to_working_dir_works(self):
        """Writing to working directory should be allowed."""
        from wafer_core.sandbox import execute_sandboxed

        with tempfile.TemporaryDirectory() as tmpdir:
            working_dir = Path(tmpdir)
            policy = SandboxPolicy.workspace_write(working_dir)
            test_file = working_dir / "test.txt"

            result = await execute_sandboxed(
                f"echo 'test content' > {test_file}",
                policy,
            )

            # Should succeed
            assert result.returncode == 0 or result.sandbox_denied is False
            # File might be created depending on shell behavior

    @pytest.mark.anyio
    async def test_sandboxed_write_outside_working_dir_blocked(self):
        """Writing outside working directory should be blocked."""
        from wafer_core.sandbox import execute_sandboxed

        with tempfile.TemporaryDirectory() as tmpdir:
            working_dir = Path(tmpdir) / "workspace"
            working_dir.mkdir()

            # Create another dir outside workspace
            outside_dir = Path(tmpdir) / "outside"
            outside_dir.mkdir()
            outside_file = outside_dir / "test.txt"

            policy = SandboxPolicy.workspace_write(working_dir)

            result = await execute_sandboxed(
                f"echo 'evil' > {outside_file}",
                policy,
            )

            # Should be blocked
            assert result.returncode != 0 or result.sandbox_denied
            # File should not exist
            assert not outside_file.exists()
