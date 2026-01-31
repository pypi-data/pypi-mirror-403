"""Baremetal provider — degenerate case with no cloud API.

Baremetal targets have no provisioning lifecycle. The "resource" is just the
SSH endpoint from the spec. list_targets returns nothing (no API to query),
and provision/terminate are errors.
"""

from __future__ import annotations

from wafer_core.targets.types import Target, TargetSpec
from wafer_core.utils.kernel_utils.targets.config import BaremetalTarget, VMTarget


def target_from_ssh_spec(spec: BaremetalTarget | VMTarget) -> Target:
    """Build a Target from a baremetal/VM spec's SSH info.

    Since there's no cloud API, the resource_id is synthetic:
    "baremetal:{host}:{port}" to make it unique and stable.
    """
    # Parse user@host:port
    ssh_target = spec.ssh_target
    assert ":" in ssh_target, f"ssh_target must include port, got: {ssh_target}"

    user_host, port_str = ssh_target.rsplit(":", 1)
    if "@" in user_host:
        user, host = user_host.split("@", 1)
    else:
        user = "root"
        host = user_host

    port = int(port_str)

    return Target(
        resource_id=f"baremetal:{host}:{port}",
        provider="baremetal",
        status="running",  # Assumed running; TCP check happens elsewhere
        public_ip=host,
        ssh_port=port,
        ssh_username=user,
        gpu_type=spec.gpu_type,
        name=spec.name,
        spec_name=spec.name,
    )


class BaremetalProvider:
    """Baremetal implementation of TargetProvider.

    Baremetal has no cloud API. list_targets returns empty (no remote state
    to query). Use target_from_ssh_spec() to build a Target from a spec
    when you already know which spec you want.
    """

    async def list_targets(self) -> list[Target]:
        """Baremetal has no API to list. Returns empty."""
        return []

    async def get_target(self, resource_id: str) -> Target | None:
        """Baremetal has no API to query. Returns None."""
        return None

    async def provision(self, spec: TargetSpec) -> Target:
        """Baremetal targets cannot be provisioned — they already exist."""
        assert isinstance(spec, (BaremetalTarget, VMTarget)), (
            f"BaremetalProvider.provision requires BaremetalTarget or VMTarget, "
            f"got {type(spec).__name__}"
        )
        return target_from_ssh_spec(spec)

    async def terminate(self, resource_id: str) -> bool:
        """Baremetal targets cannot be terminated via API."""
        return False
