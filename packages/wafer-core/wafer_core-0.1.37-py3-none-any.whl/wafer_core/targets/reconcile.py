"""Reconciliation: compare TargetSpecs to live Targets.

Pure function — no API calls, no side effects. Takes specs and targets as
inputs, returns a ReconcileResult describing what's bound, what's orphaned,
and what's unprovisioned.
"""

from __future__ import annotations

from wafer_core.targets.types import ReconcileResult, Target, TargetSpec
from wafer_core.utils.kernel_utils.targets.config import (
    BaremetalTarget,
    DigitalOceanTarget,
    RunPodTarget,
    VMTarget,
)


def _is_cloud_spec(spec: TargetSpec) -> bool:
    """Check if a spec represents a cloud-provisioned resource.

    Baremetal and VM specs don't have cloud-managed lifecycles,
    so they're excluded from "unprovisioned" checks.
    """
    return isinstance(spec, (RunPodTarget, DigitalOceanTarget))


def _spec_provider(spec: TargetSpec) -> str | None:
    """Get the provider name for a spec, or None if not cloud-managed."""
    if isinstance(spec, RunPodTarget):
        return "runpod"
    if isinstance(spec, DigitalOceanTarget):
        return "digitalocean"
    if isinstance(spec, (BaremetalTarget, VMTarget)):
        return "baremetal"
    return None


def reconcile(
    specs: list[TargetSpec],
    targets: list[Target],
    binding_hints: dict[str, str] | None = None,
) -> ReconcileResult:
    """Compare specs to live targets and classify each.

    Matching rules (in priority order):
    1. Target.spec_name matches Spec.name exactly (set by naming convention
       or explicit binding).
    2. binding_hints maps resource_id → spec_name (from local cache).
    3. No match → target is unbound (orphan).

    A cloud spec with no matching target is "unprovisioned".
    Baremetal/VM specs are never "unprovisioned" (they don't have a cloud
    lifecycle — the machine is always there or it isn't).

    Args:
        specs: All known TargetSpecs (loaded from TOML files).
        targets: All live Targets (fetched from provider APIs).
        binding_hints: Optional resource_id → spec_name cache for targets
            whose spec_name can't be inferred from naming convention.

    Returns:
        ReconcileResult with bound, unbound, and unprovisioned lists.
    """
    hints = binding_hints or {}
    spec_by_name = {s.name: s for s in specs}
    claimed_spec_names: set[str] = set()

    bound: list[tuple[TargetSpec, Target]] = []
    unbound: list[Target] = []

    for target in targets:
        # Try to find the spec this target belongs to
        resolved_spec_name = target.spec_name or hints.get(target.resource_id)

        if resolved_spec_name and resolved_spec_name in spec_by_name:
            spec = spec_by_name[resolved_spec_name]
            bound.append((spec, target))
            claimed_spec_names.add(resolved_spec_name)
        else:
            unbound.append(target)

    # Cloud specs with no bound target are unprovisioned
    unprovisioned = [s for s in specs if s.name not in claimed_spec_names and _is_cloud_spec(s)]

    return ReconcileResult(
        bound=bound,
        unbound=unbound,
        unprovisioned=unprovisioned,
    )
