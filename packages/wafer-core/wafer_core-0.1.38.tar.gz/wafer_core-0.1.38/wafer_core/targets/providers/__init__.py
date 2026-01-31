"""Provider registry for GPU resource management.

Each provider implements TargetProvider protocol: list, get, provision, terminate.
"""

from __future__ import annotations

from wafer_core.targets.providers.baremetal import BaremetalProvider
from wafer_core.targets.providers.digitalocean import DigitalOceanProvider
from wafer_core.targets.providers.runpod import RunPodProvider
from wafer_core.targets.types import TargetProvider

_PROVIDERS: dict[str, type] = {
    "runpod": RunPodProvider,
    "digitalocean": DigitalOceanProvider,
    "baremetal": BaremetalProvider,
}


def get_provider(name: str) -> TargetProvider:
    """Get a provider instance by name.

    Raises KeyError if provider is not registered.
    """
    cls = _PROVIDERS.get(name)
    if cls is None:
        raise KeyError(f"Unknown provider: {name!r}. Available: {', '.join(sorted(_PROVIDERS))}")
    return cls()


def get_all_cloud_providers() -> list[tuple[str, TargetProvider]]:
    """Get all cloud providers that can list remote resources.

    Excludes baremetal (no remote API to query).
    Returns list of (name, provider) tuples.
    """
    return [(name, cls()) for name, cls in _PROVIDERS.items() if name != "baremetal"]


__all__ = [
    "BaremetalProvider",
    "DigitalOceanProvider",
    "RunPodProvider",
    "get_all_cloud_providers",
    "get_provider",
]
