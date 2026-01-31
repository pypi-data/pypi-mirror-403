"""Target and TargetSpec: the two core concepts for GPU resource management.

TargetSpec = provisioning blueprint (TOML config, "how to get a GPU")
Target = live running resource (from provider API, "what's actually running")

TargetSpec is the existing union of provider-specific frozen dataclasses
(RunPodTarget, DigitalOceanTarget, BaremetalTarget, etc.), re-exported here
under the name TargetSpec for clarity.

Target is always fetched from provider APIs. The spec_name field links a
live resource back to the spec that created it (None = orphan/unbound).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    pass

# TargetSpec is the existing union type, re-exported under a clearer name.
# Each variant is a frozen dataclass with provider-specific provisioning params.
from wafer_core.utils.kernel_utils.targets.config import (  # noqa: E402
    TargetConfig,
)

# TargetSpec = TargetConfig (same union, better name for the new API)
TargetSpec = TargetConfig


@dataclass(frozen=True)
class Target:
    """A live running GPU resource, fetched from a provider API.

    This is the runtime counterpart to TargetSpec. A TargetSpec describes
    *how* to provision a GPU; a Target describes *what's actually running*.

    The provider API is the source of truth for Target state. Local caches
    (target_state.json) are performance hints only.

    Fields:
        resource_id: Provider's unique ID (pod_id, droplet_id, or
            "baremetal:{host}:{port}" for SSH targets with no cloud lifecycle).
        provider: Which cloud provider owns this resource.
        status: Current state from provider API.
        public_ip: SSH-reachable IP address (None if not yet assigned).
        ssh_port: SSH port (None if not yet assigned).
        ssh_username: SSH user (typically "root" for cloud providers).
        gpu_type: GPU model name (e.g., "MI300X", "B200").
        name: Provider-side resource name (e.g., "wafer-runpod-mi300x-1706000000",
            "kernelbench-pool-0"). Used for spec_name inference.
        created_at: ISO timestamp of resource creation (None if unknown).
        spec_name: Name of the TargetSpec that owns this resource.
            None means unbound (orphan) — running but no spec claims it.
        price_per_hour: Cost in $/hr (None if unknown or baremetal).
        labels: Software metadata not available from the provider API's
            structured fields. Examples: {"rocm_version": "7.0.2",
            "cuda_version": "12.4", "image": "rocm/pytorch:rocm7.0.2_..."}.
            Populated from the container image string at provision time,
            or from SSH probe on demand. Pool queries filter on these.
    """

    resource_id: str
    provider: str
    status: str
    public_ip: str | None
    ssh_port: int | None
    ssh_username: str
    gpu_type: str
    name: str | None = None
    created_at: str | None = None
    spec_name: str | None = None
    price_per_hour: float | None = None
    labels: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        assert self.resource_id, "resource_id cannot be empty"
        assert self.provider, "provider cannot be empty"
        assert self.status, "status cannot be empty"


@dataclass(frozen=True)
class ReconcileResult:
    """Result of comparing TargetSpecs to live Targets.

    Pure data — no side effects. The caller decides what to do:
    - Display bound/unbound/unprovisioned in CLI
    - Terminate unbound targets
    - Provision from unprovisioned specs

    Fields:
        bound: Specs matched to live targets (spec, target) pairs.
        unbound: Live targets with no matching spec (orphans).
        unprovisioned: Specs with no live target running.
    """

    bound: list[tuple[TargetSpec, Target]]
    unbound: list[Target]
    unprovisioned: list[TargetSpec]


@runtime_checkable
class TargetProvider(Protocol):
    """Interface for querying and managing live GPU resources from a cloud provider.

    Each cloud provider (RunPod, DigitalOcean, etc.) implements this protocol.
    Methods are async because they hit external APIs.

    Baremetal is a degenerate case: list_targets returns a Target built from
    the spec's ssh_target, provision/terminate are no-ops.
    """

    async def list_targets(self) -> list[Target]:
        """List all running resources on the provider account.

        Always hits the provider API — never reads from local cache.
        """
        ...

    async def get_target(self, resource_id: str) -> Target | None:
        """Get a specific resource by provider ID.

        Returns None if the resource doesn't exist or is terminated.
        """
        ...

    async def provision(self, spec: TargetSpec) -> Target:
        """Provision a new resource from a spec.

        Blocks until the resource is SSH-ready.
        Raises on failure (no silent None returns).
        """
        ...

    async def terminate(self, resource_id: str) -> bool:
        """Terminate a resource by provider ID.

        Returns True if terminated, False if resource not found.
        """
        ...
