"""Tests for TraceLens finder module."""

from wafer_core.lib.tracelens import check_installation
from wafer_core.lib.tracelens.types import CheckResult


def test_check_installation_returns_result() -> None:
    """Test check_installation returns a valid CheckResult."""
    result = check_installation()
    
    # Always returns a valid CheckResult
    assert isinstance(result, CheckResult)
    assert hasattr(result, 'installed')
    assert hasattr(result, 'install_command')
    assert isinstance(result.installed, bool)


def test_check_installation_has_install_instructions_if_not_installed() -> None:
    """Test that install instructions are provided when not installed."""
    result = check_installation()
    
    # If not installed, should have install instructions
    if not result.installed:
        assert result.install_command is not None
        assert "pip install" in result.install_command
        assert "TraceLens" in result.install_command


def test_check_installation_has_commands_if_installed() -> None:
    """Test that available commands are listed when installed."""
    result = check_installation()
    
    # If installed, should have list of commands
    if result.installed:
        assert result.commands_available is not None
        assert len(result.commands_available) > 0
        # Each command should be a known TraceLens command
        for cmd in result.commands_available:
            assert cmd.startswith("TraceLens_")
