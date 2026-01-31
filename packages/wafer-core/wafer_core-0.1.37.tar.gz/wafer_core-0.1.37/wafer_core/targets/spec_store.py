"""Spec store: CRUD for TargetSpec TOML files.

Specs live in ~/.wafer/specs/{name}.toml. On first access, auto-migrates
from the old ~/.wafer/targets/ directory if specs/ doesn't exist yet.

This module provides the same operations as the old targets.py but under
the "spec" vocabulary. The CLI-layer targets.py still works and delegates
here where needed.
"""

from __future__ import annotations

import logging
import shutil
from dataclasses import asdict
from pathlib import Path
from typing import Any

import tomllib

from wafer_core.utils.kernel_utils.targets.config import (
    BaremetalTarget,
    DigitalOceanTarget,
    LocalTarget,
    ModalTarget,
    RunPodTarget,
    TargetConfig,
    VMTarget,
    WorkspaceTarget,
)

logger = logging.getLogger(__name__)

WAFER_DIR = Path.home() / ".wafer"
SPECS_DIR = WAFER_DIR / "specs"
OLD_TARGETS_DIR = WAFER_DIR / "targets"
CONFIG_FILE = WAFER_DIR / "config.toml"


def _ensure_specs_dir() -> None:
    """Ensure ~/.wafer/specs/ exists, migrating from targets/ if needed."""
    if SPECS_DIR.exists():
        return

    if OLD_TARGETS_DIR.exists() and any(OLD_TARGETS_DIR.glob("*.toml")):
        logger.info(
            f"Migrating {OLD_TARGETS_DIR} -> {SPECS_DIR} (target configs are now called 'specs')"
        )
        shutil.copytree(OLD_TARGETS_DIR, SPECS_DIR)
        # Don't delete old dir yet — other code may still read from it.
        # It becomes a dead symlink target once all callers migrate.
        logger.info(
            f"Migration complete. Old directory preserved at {OLD_TARGETS_DIR}. "
            "You can safely delete it once 'wafer specs list' works."
        )
    else:
        SPECS_DIR.mkdir(parents=True, exist_ok=True)


def _spec_path(name: str) -> Path:
    return SPECS_DIR / f"{name}.toml"


# ── Parsing ──────────────────────────────────────────────────────────────────

_TYPE_MAP: dict[str, type] = {
    "baremetal": BaremetalTarget,
    "vm": VMTarget,
    "modal": ModalTarget,
    "workspace": WorkspaceTarget,
    "runpod": RunPodTarget,
    "digitalocean": DigitalOceanTarget,
    "local": LocalTarget,
}

_TYPE_REVERSE: dict[type, str] = {v: k for k, v in _TYPE_MAP.items()}


def parse_spec(data: dict[str, Any]) -> TargetConfig:
    """Parse TOML dict into TargetSpec (TargetConfig union)."""
    target_type = data.get("type")
    if not target_type:
        raise ValueError("Spec must have 'type' field")

    cls = _TYPE_MAP.get(target_type)
    if cls is None:
        raise ValueError(
            f"Unknown spec type: {target_type}. Must be one of: {', '.join(sorted(_TYPE_MAP))}"
        )

    fields = {k: v for k, v in data.items() if k != "type"}

    # TOML parses lists; dataclasses may want tuples
    if "pip_packages" in fields and isinstance(fields["pip_packages"], list):
        fields["pip_packages"] = tuple(fields["pip_packages"])
    if "gpu_ids" in fields and isinstance(fields["gpu_ids"], list):
        fields["gpu_ids"] = tuple(fields["gpu_ids"])

    return cls(**fields)


def serialize_spec(spec: TargetConfig) -> dict[str, Any]:
    """Serialize TargetSpec to TOML-compatible dict."""
    data = asdict(spec)
    data["type"] = _TYPE_REVERSE.get(type(spec), "unknown")

    # Tuples -> lists for TOML
    for key in ("pip_packages", "gpu_ids"):
        if key in data and isinstance(data[key], tuple):
            data[key] = list(data[key])

    # Drop empty pip_packages
    if "pip_packages" in data and not data["pip_packages"]:
        del data["pip_packages"]

    return data


# ── CRUD ─────────────────────────────────────────────────────────────────────


def load_spec(name: str) -> TargetConfig:
    """Load spec by name from ~/.wafer/specs/{name}.toml.

    Falls back to ~/.wafer/targets/{name}.toml for backwards compatibility.
    """
    _ensure_specs_dir()

    path = _spec_path(name)
    if not path.exists():
        # Fallback to old location
        old_path = OLD_TARGETS_DIR / f"{name}.toml"
        if old_path.exists():
            path = old_path
        else:
            raise FileNotFoundError(f"Spec not found: {name} (looked in {SPECS_DIR})")

    with open(path, "rb") as f:
        data = tomllib.load(f)

    return parse_spec(data)


def save_spec(spec: TargetConfig) -> None:
    """Save spec to ~/.wafer/specs/{name}.toml."""
    _ensure_specs_dir()

    data = serialize_spec(spec)
    path = _spec_path(spec.name)
    _write_toml(path, data)


def list_spec_names() -> list[str]:
    """List all spec names from ~/.wafer/specs/."""
    _ensure_specs_dir()
    return sorted(p.stem for p in SPECS_DIR.glob("*.toml"))


def remove_spec(name: str) -> None:
    """Remove a spec by name."""
    path = _spec_path(name)
    if not path.exists():
        raise FileNotFoundError(f"Spec not found: {name}")
    path.unlink()


def load_all_specs() -> list[TargetConfig]:
    """Load all specs. Skips specs that fail to parse (logs warning)."""
    specs = []
    for name in list_spec_names():
        try:
            specs.append(load_spec(name))
        except Exception as e:
            logger.warning(f"Failed to load spec {name}: {e}")
    return specs


# ── TOML writer ──────────────────────────────────────────────────────────────


def _write_toml(path: Path, data: dict[str, Any]) -> None:
    """Write dict as flat TOML file."""
    lines = []
    for key, value in data.items():
        if value is None:
            continue
        if isinstance(value, bool):
            lines.append(f"{key} = {str(value).lower()}")
        elif isinstance(value, int | float):
            lines.append(f"{key} = {value}")
        elif isinstance(value, str):
            lines.append(f'{key} = "{value}"')
        elif isinstance(value, list):
            if all(isinstance(v, int) for v in value):
                lines.append(f"{key} = {value}")
            else:
                formatted = ", ".join(f'"{v}"' if isinstance(v, str) else str(v) for v in value)
                lines.append(f"{key} = [{formatted}]")

    path.write_text("\n".join(lines) + "\n")
