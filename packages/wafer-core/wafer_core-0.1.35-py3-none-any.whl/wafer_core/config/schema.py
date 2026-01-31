"""Configuration schema for Wafer CLI.

Example config.toml:

    [sandbox]
    enabled = true

    [allowlist]
    allow = ["npm run", "cargo build"]
    block = ["rm -rf", "sudo"]

    [sandbox.paths]
    writable = ["/tmp/my-cache"]
    network = false
"""

from dataclasses import dataclass, field


@dataclass
class SandboxPathsConfig:
    """Sandbox path configuration."""

    writable: list[str] = field(default_factory=list)
    network: bool = False


@dataclass
class SandboxConfig:
    """Sandbox configuration."""

    enabled: bool = True
    paths: SandboxPathsConfig = field(default_factory=SandboxPathsConfig)


@dataclass
class AllowlistConfig:
    """Command allowlist configuration."""

    allow: list[str] = field(default_factory=list)
    block: list[str] = field(default_factory=list)


@dataclass
class WaferConfig:
    """Complete Wafer configuration.

    Attributes:
        sandbox: Sandbox settings (enabled, paths, network)
        allowlist: Command allow/block lists
        source: Where this config was loaded from (for debugging)
    """

    sandbox: SandboxConfig = field(default_factory=SandboxConfig)
    allowlist: AllowlistConfig = field(default_factory=AllowlistConfig)
    source: str | None = None

    @classmethod
    def from_dict(cls, data: dict, source: str | None = None) -> "WaferConfig":
        """Create config from a dictionary (parsed TOML).

        Args:
            data: Dictionary from TOML parsing
            source: Path or description of where config came from

        Returns:
            WaferConfig instance

        Raises:
            TypeError: If config has invalid types
        """
        sandbox_data = data.get("sandbox", {})
        allowlist_data = data.get("allowlist", {})

        # Parse sandbox.paths (can be nested in sandbox or at top level)
        paths_data = sandbox_data.get("paths", {})
        paths_config = SandboxPathsConfig(
            writable=_validate_string_list(
                paths_data.get("writable", []), "sandbox.paths.writable"
            ),
            network=_validate_bool(paths_data.get("network", False), "sandbox.paths.network"),
        )

        sandbox_config = SandboxConfig(
            enabled=_validate_bool(sandbox_data.get("enabled", True), "sandbox.enabled"),
            paths=paths_config,
        )

        allowlist_config = AllowlistConfig(
            allow=_validate_string_list(allowlist_data.get("allow", []), "allowlist.allow"),
            block=_validate_string_list(allowlist_data.get("block", []), "allowlist.block"),
        )

        return cls(
            sandbox=sandbox_config,
            allowlist=allowlist_config,
            source=source,
        )

    def to_dict(self) -> dict:
        """Convert to dictionary (for serialization)."""
        return {
            "sandbox": {
                "enabled": self.sandbox.enabled,
                "paths": {
                    "writable": self.sandbox.paths.writable,
                    "network": self.sandbox.paths.network,
                },
            },
            "allowlist": {
                "allow": self.allowlist.allow,
                "block": self.allowlist.block,
            },
        }


def _validate_string_list(value: object, field_name: str) -> list[str]:
    """Validate that a value is a list of strings."""
    if not isinstance(value, list):
        raise TypeError(f"{field_name} must be a list, got {type(value).__name__}")
    for i, item in enumerate(value):
        if not isinstance(item, str):
            raise TypeError(f"{field_name}[{i}] must be a string, got {type(item).__name__}")
    return value


def _validate_bool(value: object, field_name: str) -> bool:
    """Validate that a value is a boolean."""
    if not isinstance(value, bool):
        raise TypeError(f"{field_name} must be a boolean, got {type(value).__name__}")
    return value
