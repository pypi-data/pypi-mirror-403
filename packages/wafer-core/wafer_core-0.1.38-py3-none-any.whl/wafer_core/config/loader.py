"""Configuration loading and merging.

Loads config from:
1. User config: ~/.wafer/config.toml
2. Project config: .wafer/config.toml (in working directory)

Then merges with CLI flags according to resolution rules.
"""

from pathlib import Path

from wafer_core.config.schema import (
    AllowlistConfig,
    SandboxConfig,
    SandboxPathsConfig,
    WaferConfig,
)
from wafer_core.rollouts.templates.base import SAFE_BASH_COMMANDS


def get_user_config_path() -> Path:
    """Get path to user config file (~/.wafer/config.toml)."""
    return Path.home() / ".wafer" / "config.toml"


def get_project_config_path(working_dir: Path) -> Path:
    """Get path to project config file (.wafer/config.toml)."""
    return working_dir / ".wafer" / "config.toml"


def load_toml(path: Path) -> dict | None:
    """Load TOML file, returning None if it doesn't exist.

    Raises:
        ValueError: If file exists but is invalid TOML
    """
    if not path.exists():
        return None

    try:
        import tomllib
    except ImportError:
        # Python < 3.11
        import tomli as tomllib  # type: ignore

    try:
        with open(path, "rb") as f:
            return tomllib.load(f)
    except Exception as e:
        raise ValueError(f"Invalid TOML in {path}: {e}") from e


def load_config(working_dir: Path) -> tuple[WaferConfig | None, WaferConfig | None]:
    """Load user and project configs.

    Args:
        working_dir: Working directory for finding project config

    Returns:
        Tuple of (user_config, project_config). Either may be None if not found.

    Raises:
        ValueError: If config file exists but is invalid
    """
    user_config = None
    project_config = None

    # Load user config
    user_path = get_user_config_path()
    user_data = load_toml(user_path)
    if user_data is not None:
        user_config = WaferConfig.from_dict(user_data, source=str(user_path))

    # Load project config
    project_path = get_project_config_path(working_dir)
    project_data = load_toml(project_path)
    if project_data is not None:
        project_config = WaferConfig.from_dict(project_data, source=str(project_path))

    return user_config, project_config


def merge_configs(
    user_config: WaferConfig | None,
    project_config: WaferConfig | None,
    cli_sandbox_enabled: bool | None = None,
    cli_allow: list[str] | None = None,
    cli_block: list[str] | None = None,
    cli_allowlist_replace: list[str] | None = None,
) -> WaferConfig:
    """Merge configs according to resolution rules.

    Priority (highest to lowest):
    1. CLI flags
    2. Project config (.wafer/config.toml)
    3. User config (~/.wafer/config.toml)
    4. Built-in defaults (SAFE_BASH_COMMANDS + sandbox enabled)

    Resolution rules:
    - allow lists merge additively (unless cli_allowlist_replace is set)
    - block lists merge additively
    - block always wins over allow
    - sandbox.enabled: CLI > project > user > default (True)

    Args:
        user_config: User-level config (~/.wafer/config.toml)
        project_config: Project-level config (.wafer/config.toml)
        cli_sandbox_enabled: --sandbox / --no-sandbox flag (None = not specified)
        cli_allow: --allow flags (additive)
        cli_block: --block flags (additive)
        cli_allowlist_replace: --allowlist flag (replaces all allow lists)

    Returns:
        Merged WaferConfig
    """
    # Start with built-in defaults
    allow_list: list[str] = list(SAFE_BASH_COMMANDS)
    block_list: list[str] = []
    sandbox_enabled = True
    writable_paths: list[str] = []
    network = False

    # Layer 1: User config
    if user_config is not None:
        allow_list.extend(user_config.allowlist.allow)
        block_list.extend(user_config.allowlist.block)
        sandbox_enabled = user_config.sandbox.enabled
        writable_paths.extend(user_config.sandbox.paths.writable)
        network = network or user_config.sandbox.paths.network

    # Layer 2: Project config (overwrites sandbox.enabled, extends lists)
    if project_config is not None:
        allow_list.extend(project_config.allowlist.allow)
        block_list.extend(project_config.allowlist.block)
        sandbox_enabled = project_config.sandbox.enabled
        writable_paths.extend(project_config.sandbox.paths.writable)
        network = network or project_config.sandbox.paths.network

    # Layer 3: CLI flags
    if cli_allowlist_replace is not None:
        # --allowlist replaces everything
        allow_list = list(cli_allowlist_replace)
    elif cli_allow is not None:
        # --allow is additive
        allow_list.extend(cli_allow)

    if cli_block is not None:
        block_list.extend(cli_block)

    if cli_sandbox_enabled is not None:
        sandbox_enabled = cli_sandbox_enabled

    # Deduplicate while preserving order
    allow_list = _dedupe(allow_list)
    block_list = _dedupe(block_list)
    writable_paths = _dedupe(writable_paths)

    return WaferConfig(
        sandbox=SandboxConfig(
            enabled=sandbox_enabled,
            paths=SandboxPathsConfig(
                writable=writable_paths,
                network=network,
            ),
        ),
        allowlist=AllowlistConfig(
            allow=allow_list,
            block=block_list,
        ),
        source="merged",
    )


def resolve_command_permission(
    command: str,
    allow_list: list[str],
    block_list: list[str],
) -> str:
    """Determine permission level for a command.

    Args:
        command: The command to check (e.g., "npm run build")
        allow_list: List of allowed command prefixes
        block_list: List of blocked command prefixes

    Returns:
        "allow", "block", or "ask"

    Resolution:
    1. If command matches any block prefix -> "block"
    2. If command matches any allow prefix -> "allow"
    3. Otherwise -> "ask"

    Block always wins over allow (checked first).
    """
    command_stripped = command.strip()

    # Check block list first (block always wins)
    for prefix in block_list:
        if command_stripped.startswith(prefix) or command_stripped == prefix.rstrip():
            return "block"

    # Check allow list
    for prefix in allow_list:
        if command_stripped.startswith(prefix) or command_stripped == prefix.rstrip():
            return "allow"

    return "ask"


def _dedupe(items: list[str]) -> list[str]:
    """Deduplicate list while preserving order."""
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result
