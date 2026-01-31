"""Target state cache: bindings and labels for live resources.

Cache file: ~/.wafer/target_state.json

Bindings map resource_id -> spec_name (performance hint for reconciliation).
Labels map resource_id -> {key: value} (probed software versions).

The provider API is always the source of truth for whether a resource exists.
This cache stores metadata that's expensive to recompute (SSH probes, name inference).

Format:
{
    "bindings": {
        "<resource_id>": {
            "spec_name": "<spec_name>",
            "provider": "<provider>",
            "bound_at": "<ISO timestamp>"
        }
    },
    "labels": {
        "<resource_id>": {
            "rocm_version": "7.0.2",
            "python_version": "3.12",
            ...
        }
    }
}
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

WAFER_DIR = Path.home() / ".wafer"
STATE_FILE = WAFER_DIR / "target_state.json"


@dataclass(frozen=True)
class BindingEntry:
    """A cached binding from resource_id to spec_name."""

    spec_name: str
    provider: str
    bound_at: str  # ISO timestamp


# ---------------------------------------------------------------------------
# Raw file I/O
# ---------------------------------------------------------------------------

def _load_state() -> dict:
    """Load the full state file. Returns empty dict if missing/corrupted."""
    if not STATE_FILE.exists():
        return {}

    try:
        return json.loads(STATE_FILE.read_text())
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning(f"Corrupted state cache, ignoring: {e}")
        return {}


def _save_state(data: dict) -> None:
    """Write the full state file."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(data, indent=2) + "\n")


# ---------------------------------------------------------------------------
# Bindings
# ---------------------------------------------------------------------------

def load_bindings() -> dict[str, BindingEntry]:
    """Load binding cache from disk."""
    data = _load_state()
    bindings_raw = data.get("bindings", {})
    result = {}
    for rid, entry in bindings_raw.items():
        try:
            result[rid] = BindingEntry(**entry)
        except TypeError:
            logger.warning(f"Skipping malformed binding for {rid}")
    return result


def save_bindings(bindings: dict[str, BindingEntry]) -> None:
    """Write bindings to disk (preserves labels)."""
    data = _load_state()
    data["bindings"] = {rid: asdict(entry) for rid, entry in bindings.items()}
    _save_state(data)


def add_binding(resource_id: str, entry: BindingEntry) -> None:
    """Add a single binding to the cache."""
    bindings = load_bindings()
    bindings[resource_id] = entry
    save_bindings(bindings)


def remove_binding(resource_id: str) -> None:
    """Remove a binding from the cache. No-op if not found."""
    bindings = load_bindings()
    if resource_id in bindings:
        del bindings[resource_id]
        save_bindings(bindings)


def get_binding_hints() -> dict[str, str]:
    """Get resource_id -> spec_name map for reconciliation."""
    bindings = load_bindings()
    return {rid: entry.spec_name for rid, entry in bindings.items()}


# ---------------------------------------------------------------------------
# Labels
# ---------------------------------------------------------------------------

def load_all_labels() -> dict[str, dict[str, str]]:
    """Load all cached labels. Returns resource_id -> labels dict."""
    data = _load_state()
    return data.get("labels", {})


def load_labels(resource_id: str) -> dict[str, str]:
    """Load cached labels for a single resource. Returns empty dict if none."""
    return load_all_labels().get(resource_id, {})


def save_labels(resource_id: str, labels: dict[str, str]) -> None:
    """Save labels for a resource (preserves bindings and other labels)."""
    data = _load_state()
    if "labels" not in data:
        data["labels"] = {}
    data["labels"][resource_id] = labels
    _save_state(data)


def remove_labels(resource_id: str) -> None:
    """Remove cached labels for a resource. No-op if not found."""
    data = _load_state()
    labels = data.get("labels", {})
    if resource_id in labels:
        del labels[resource_id]
        data["labels"] = labels
        _save_state(data)
