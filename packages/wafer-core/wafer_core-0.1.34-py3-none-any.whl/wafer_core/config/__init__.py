"""Configuration loading for Wafer CLI.

Handles config file loading from:
1. User config: ~/.wafer/config.toml
2. Project config: .wafer/config.toml (in working directory)

Resolution rules:
- Built-in SAFE_BASH_COMMANDS are always included
- allow lists merge additively across all sources
- block lists merge additively across all sources
- block always wins over allow
- CLI flags override sandbox.enabled
"""

from wafer_core.config.loader import load_config, merge_configs
from wafer_core.config.schema import WaferConfig

__all__ = [
    "WaferConfig",
    "load_config",
    "merge_configs",
]
