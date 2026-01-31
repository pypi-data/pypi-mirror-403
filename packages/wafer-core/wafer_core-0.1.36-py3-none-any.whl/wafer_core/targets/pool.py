"""Pool queries: filter live targets by GPU type, provider, and labels.

A pool is a predicate over live targets, not a hardcoded list.
Pool queries are defined in ~/.wafer/config.toml:

    [pools.mi300x]
    gpu_type = "MI300X"

    [pools.mi300x-rocm7]
    gpu_type = "MI300X"
    labels.rocm_version = "7.0.2"

    [pools.runpod-only]
    provider = "runpod"

Matching: a target matches a pool query if all specified fields match.
Fields not specified in the query are ignored (match anything).
Label matching is AND — all required labels must be present and equal.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from wafer_core.targets.types import Target

WAFER_DIR = Path.home() / ".wafer"
CONFIG_FILE = WAFER_DIR / "config.toml"

# Fields on PoolQuery that map directly to Target fields
_TARGET_FIELDS = ("gpu_type", "provider", "status")


@dataclass(frozen=True)
class PoolQuery:
    """Predicate for filtering live targets.

    All specified fields must match (AND semantics).
    None means "don't care" for that field.
    """

    gpu_type: str | None = None
    provider: str | None = None
    status: str | None = "running"
    labels: dict[str, str] = field(default_factory=dict)


def match_targets(query: PoolQuery, targets: list[Target]) -> list[Target]:
    """Filter targets that satisfy the pool query. Pure function."""
    matched = []
    for target in targets:
        if not _matches(query, target):
            continue
        matched.append(target)
    return matched


def _matches(query: PoolQuery, target: Target) -> bool:
    """Check if a single target satisfies the query."""
    if query.gpu_type is not None and target.gpu_type != query.gpu_type:
        return False
    if query.provider is not None and target.provider != query.provider:
        return False
    if query.status is not None and target.status != query.status:
        return False

    # All required labels must be present and equal
    for key, value in query.labels.items():
        if target.labels.get(key) != value:
            return False

    return True


def load_pool_query(name: str) -> PoolQuery:
    """Load a pool query from ~/.wafer/config.toml.

    Raises KeyError if the pool is not defined.
    """
    pools = _load_pools_section()
    if name not in pools:
        available = ", ".join(sorted(pools)) if pools else "(none)"
        raise KeyError(f"Pool {name!r} not found. Available: {available}")

    raw = pools[name]
    assert isinstance(raw, dict), f"Pool {name!r} must be a table, got {type(raw).__name__}"

    labels_raw = raw.get("labels", {})
    assert isinstance(labels_raw, dict), (
        f"Pool {name!r} labels must be a table, got {type(labels_raw).__name__}"
    )

    return PoolQuery(
        gpu_type=raw.get("gpu_type"),
        provider=raw.get("provider"),
        status=raw.get("status", "running"),
        labels={str(k): str(v) for k, v in labels_raw.items()},
    )


def list_pool_names() -> list[str]:
    """List all pool names from config.toml."""
    pools = _load_pools_section()
    return sorted(pools.keys())


def is_query_pool(name: str) -> bool:
    """Check if a pool is defined as a PoolQuery (new format) vs target list (old format).

    Old format: [pools.name] targets = ["t1", "t2"]
    New format: [pools.name] gpu_type = "MI300X"

    Returns False if pool doesn't exist or is old format.
    """
    pools = _load_pools_section()
    if name not in pools:
        return False
    raw = pools[name]
    if not isinstance(raw, dict):
        return False
    # Old format has a "targets" key with a list of names
    return "targets" not in raw


async def resolve_pool(name: str) -> list[Target]:
    """Resolve a pool query to live targets.

    Queries all cloud providers, hydrates cached labels, filters by pool query.
    Returns matching Target objects sorted by resource_id for determinism.

    Raises KeyError if pool not found.
    """
    from dataclasses import replace

    from wafer_core.targets.providers import get_all_cloud_providers
    from wafer_core.targets.state_cache import load_all_labels
    from wafer_core.targets.types import TargetProvider

    import trio

    query = load_pool_query(name)

    # Fetch all live targets
    all_targets: list[Target] = []

    async def _fetch(prov_impl: TargetProvider, results: list[Target]) -> None:
        try:
            targets = await prov_impl.list_targets()
            results.extend(targets)
        except Exception:
            pass  # Skip providers that fail (missing API key, etc.)

    async with trio.open_nursery() as nursery:
        for _, prov_impl in get_all_cloud_providers():
            nursery.start_soon(_fetch, prov_impl, all_targets)

    # Hydrate labels from cache
    cached_labels = load_all_labels()
    all_targets = [
        replace(t, labels=cached_labels[t.resource_id])
        if t.resource_id in cached_labels
        else t
        for t in all_targets
    ]

    # Filter and sort
    matched = match_targets(query, all_targets)
    matched.sort(key=lambda t: t.resource_id)
    return matched


def _load_pools_section() -> dict:
    """Read the [pools] section from config.toml. Returns empty dict if missing."""
    if not CONFIG_FILE.exists():
        return {}

    import tomllib

    data = tomllib.loads(CONFIG_FILE.read_text())
    return data.get("pools", {})
