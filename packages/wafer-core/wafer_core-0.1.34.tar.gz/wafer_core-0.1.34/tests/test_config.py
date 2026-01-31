"""Tests for wafer_core.config module."""

from pathlib import Path

import pytest

from wafer_core.config import WaferConfig, load_config, merge_configs
from wafer_core.config.loader import resolve_command_permission
from wafer_core.rollouts.templates.base import SAFE_BASH_COMMANDS


class TestWaferConfigFromDict:
    """Tests for WaferConfig.from_dict()."""

    def test_empty_dict_uses_defaults(self) -> None:
        config = WaferConfig.from_dict({})
        assert config.sandbox.enabled is True
        assert config.sandbox.paths.writable == []
        assert config.sandbox.paths.network is False
        assert config.allowlist.allow == []
        assert config.allowlist.block == []

    def test_sandbox_enabled_false(self) -> None:
        config = WaferConfig.from_dict({"sandbox": {"enabled": False}})
        assert config.sandbox.enabled is False

    def test_allowlist_allow(self) -> None:
        config = WaferConfig.from_dict({"allowlist": {"allow": ["npm run", "cargo build"]}})
        assert config.allowlist.allow == ["npm run", "cargo build"]

    def test_allowlist_block(self) -> None:
        config = WaferConfig.from_dict({"allowlist": {"block": ["rm -rf", "sudo"]}})
        assert config.allowlist.block == ["rm -rf", "sudo"]

    def test_sandbox_paths(self) -> None:
        config = WaferConfig.from_dict({
            "sandbox": {
                "paths": {
                    "writable": ["/tmp/cache", "/var/log"],
                    "network": True,
                }
            }
        })
        assert config.sandbox.paths.writable == ["/tmp/cache", "/var/log"]
        assert config.sandbox.paths.network is True

    def test_invalid_allow_type(self) -> None:
        with pytest.raises(TypeError, match="allowlist.allow must be a list"):
            WaferConfig.from_dict({"allowlist": {"allow": "not a list"}})

    def test_invalid_allow_item_type(self) -> None:
        with pytest.raises(TypeError, match=r"allowlist.allow\[0\] must be a string"):
            WaferConfig.from_dict({"allowlist": {"allow": [123]}})

    def test_invalid_enabled_type(self) -> None:
        with pytest.raises(TypeError, match="sandbox.enabled must be a boolean"):
            WaferConfig.from_dict({"sandbox": {"enabled": "yes"}})


class TestLoadConfig:
    """Tests for load_config()."""

    def test_no_config_files(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        # Mock user config path to a non-existent location
        monkeypatch.setattr(
            "wafer_core.config.loader.get_user_config_path",
            lambda: tmp_path / "nonexistent" / "config.toml",
        )
        user_config, project_config = load_config(tmp_path)
        assert user_config is None
        assert project_config is None

    def test_project_config_only(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        # Mock user config path to a non-existent location
        monkeypatch.setattr(
            "wafer_core.config.loader.get_user_config_path",
            lambda: tmp_path / "nonexistent" / "config.toml",
        )
        config_dir = tmp_path / ".wafer"
        config_dir.mkdir()
        config_file = config_dir / "config.toml"
        config_file.write_text("[sandbox]\nenabled = false\n")

        user_config, project_config = load_config(tmp_path)
        assert user_config is None
        assert project_config is not None
        assert project_config.sandbox.enabled is False

    def test_user_config_only(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        # Create a user config in tmp_path
        user_config_dir = tmp_path / "home" / ".wafer"
        user_config_dir.mkdir(parents=True)
        user_config_file = user_config_dir / "config.toml"
        user_config_file.write_text('[allowlist]\nallow = ["custom-cmd"]\n')

        monkeypatch.setattr(
            "wafer_core.config.loader.get_user_config_path", lambda: user_config_file
        )

        project_dir = tmp_path / "project"
        project_dir.mkdir()

        user_config, project_config = load_config(project_dir)
        assert user_config is not None
        assert user_config.allowlist.allow == ["custom-cmd"]
        assert project_config is None

    def test_invalid_toml(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            "wafer_core.config.loader.get_user_config_path",
            lambda: tmp_path / "nonexistent" / "config.toml",
        )
        config_dir = tmp_path / ".wafer"
        config_dir.mkdir()
        config_file = config_dir / "config.toml"
        config_file.write_text("invalid toml [[[")

        with pytest.raises(ValueError, match="Invalid TOML"):
            load_config(tmp_path)


class TestMergeConfigs:
    """Tests for merge_configs()."""

    def test_defaults_only(self) -> None:
        merged = merge_configs(None, None)
        assert merged.sandbox.enabled is True
        assert set(merged.allowlist.allow) == set(SAFE_BASH_COMMANDS)
        assert merged.allowlist.block == []

    def test_user_config_extends_defaults(self) -> None:
        user = WaferConfig.from_dict({"allowlist": {"allow": ["npm run"]}})
        merged = merge_configs(user, None)
        assert "npm run" in merged.allowlist.allow
        assert "ls" in merged.allowlist.allow  # Built-in still present

    def test_project_config_extends_user(self) -> None:
        user = WaferConfig.from_dict({"allowlist": {"allow": ["npm run"]}})
        project = WaferConfig.from_dict({"allowlist": {"allow": ["cargo build"]}})
        merged = merge_configs(user, project)
        assert "npm run" in merged.allowlist.allow
        assert "cargo build" in merged.allowlist.allow
        assert "ls" in merged.allowlist.allow

    def test_project_sandbox_overrides_user(self) -> None:
        user = WaferConfig.from_dict({"sandbox": {"enabled": True}})
        project = WaferConfig.from_dict({"sandbox": {"enabled": False}})
        merged = merge_configs(user, project)
        assert merged.sandbox.enabled is False

    def test_cli_sandbox_overrides_all(self) -> None:
        user = WaferConfig.from_dict({"sandbox": {"enabled": False}})
        project = WaferConfig.from_dict({"sandbox": {"enabled": False}})
        merged = merge_configs(user, project, cli_sandbox_enabled=True)
        assert merged.sandbox.enabled is True

    def test_cli_allow_is_additive(self) -> None:
        user = WaferConfig.from_dict({"allowlist": {"allow": ["npm run"]}})
        merged = merge_configs(user, None, cli_allow=["cargo build"])
        assert "npm run" in merged.allowlist.allow
        assert "cargo build" in merged.allowlist.allow

    def test_cli_allowlist_replace(self) -> None:
        user = WaferConfig.from_dict({"allowlist": {"allow": ["npm run"]}})
        merged = merge_configs(user, None, cli_allowlist_replace=["only-this"])
        assert merged.allowlist.allow == ["only-this"]
        assert "npm run" not in merged.allowlist.allow
        assert "ls" not in merged.allowlist.allow

    def test_cli_block_is_additive(self) -> None:
        user = WaferConfig.from_dict({"allowlist": {"block": ["rm -rf"]}})
        merged = merge_configs(user, None, cli_block=["sudo"])
        assert "rm -rf" in merged.allowlist.block
        assert "sudo" in merged.allowlist.block

    def test_block_lists_merge_from_all_sources(self) -> None:
        user = WaferConfig.from_dict({"allowlist": {"block": ["rm"]}})
        project = WaferConfig.from_dict({"allowlist": {"block": ["sudo"]}})
        merged = merge_configs(user, project, cli_block=["dd"])
        assert "rm" in merged.allowlist.block
        assert "sudo" in merged.allowlist.block
        assert "dd" in merged.allowlist.block

    def test_writable_paths_merge(self) -> None:
        user = WaferConfig.from_dict({"sandbox": {"paths": {"writable": ["/tmp/user"]}}})
        project = WaferConfig.from_dict({"sandbox": {"paths": {"writable": ["/tmp/project"]}}})
        merged = merge_configs(user, project)
        assert "/tmp/user" in merged.sandbox.paths.writable
        assert "/tmp/project" in merged.sandbox.paths.writable

    def test_network_or_logic(self) -> None:
        user = WaferConfig.from_dict({"sandbox": {"paths": {"network": True}}})
        project = WaferConfig.from_dict({"sandbox": {"paths": {"network": False}}})
        merged = merge_configs(user, project)
        assert merged.sandbox.paths.network is True

    def test_deduplication(self) -> None:
        user = WaferConfig.from_dict({"allowlist": {"allow": ["npm run"]}})
        project = WaferConfig.from_dict({"allowlist": {"allow": ["npm run"]}})
        merged = merge_configs(user, project, cli_allow=["npm run"])
        # Should only appear once
        assert merged.allowlist.allow.count("npm run") == 1


class TestResolveCommandPermission:
    """Tests for resolve_command_permission()."""

    def test_exact_match_allow(self) -> None:
        result = resolve_command_permission("ls", ["ls"], [])
        assert result == "allow"

    def test_prefix_match_allow(self) -> None:
        result = resolve_command_permission("npm run build", ["npm run"], [])
        assert result == "allow"

    def test_exact_match_block(self) -> None:
        result = resolve_command_permission("sudo", [], ["sudo"])
        assert result == "block"

    def test_prefix_match_block(self) -> None:
        result = resolve_command_permission("rm -rf /", [], ["rm "])
        assert result == "block"

    def test_no_match_returns_ask(self) -> None:
        result = resolve_command_permission("unknown-cmd", ["ls"], ["rm"])
        assert result == "ask"

    def test_block_wins_over_allow(self) -> None:
        # Command matches both allow and block - block wins
        result = resolve_command_permission("npm run", ["npm"], ["npm run"])
        assert result == "block"

    def test_whitespace_handling(self) -> None:
        result = resolve_command_permission("  ls -la  ", ["ls"], [])
        assert result == "allow"
