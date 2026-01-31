"""DigitalOcean provider — adapts existing DO REST API to TargetProvider protocol."""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone

from wafer_core.targets.digitalocean import (
    DigitalOceanError,
    _api_request_async,
    _get_ssh_key_ids,
    _wait_for_ssh,
)
from wafer_core.targets.digitalocean import (
    terminate_droplet as _terminate_droplet,
)
from wafer_core.targets.types import Target, TargetSpec
from wafer_core.utils.kernel_utils.targets.config import DigitalOceanTarget

logger = logging.getLogger(__name__)


def _parse_droplet_to_target(droplet: dict) -> Target:
    """Parse a DigitalOcean API droplet response into a Target."""
    droplet_id = str(droplet.get("id", ""))
    droplet_name = droplet.get("name", "")
    status_raw = droplet.get("status", "").lower()

    # Map DO statuses to our values
    # DO: new, active, off, archive
    status_map = {
        "new": "pending",
        "active": "running",
        "off": "stopped",
        "archive": "terminated",
    }
    status = status_map.get(status_raw, status_raw)

    # Extract public IP
    public_ip = None
    networks = droplet.get("networks", {})
    for net in networks.get("v4", []):
        if net.get("type") == "public":
            public_ip = net.get("ip_address")
            break

    # Infer spec_name from naming convention: wafer-{spec_name}-{timestamp}
    spec_name = None
    if droplet_name.startswith("wafer-"):
        parts = droplet_name.split("-")
        if len(parts) >= 3:
            spec_name = "-".join(parts[1:-1])

    created_at = droplet.get("created_at")

    # Extract GPU type from size slug
    size = droplet.get("size", {})
    size_slug = (
        size.get("slug", "") if isinstance(size, dict) else str(droplet.get("size_slug", ""))
    )
    gpu_type = "MI300X" if "mi300x" in size_slug.lower() else "unknown"

    return Target(
        resource_id=droplet_id,
        provider="digitalocean",
        status=status,
        public_ip=public_ip,
        ssh_port=22,
        ssh_username="root",
        gpu_type=gpu_type,
        name=droplet_name or None,
        created_at=created_at,
        spec_name=spec_name,
    )


class DigitalOceanProvider:
    """DigitalOcean implementation of TargetProvider.

    Wraps existing REST API calls for droplet management.
    """

    async def list_targets(self) -> list[Target]:
        """List all droplets on the DigitalOcean account."""
        try:
            response = await _api_request_async("GET", "/droplets", params={"per_page": "200"})
        except DigitalOceanError:
            raise
        except Exception as e:
            logger.warning(f"Failed to list DigitalOcean droplets: {e}")
            return []

        droplets = response.get("droplets", [])
        return [_parse_droplet_to_target(d) for d in droplets]

    async def get_target(self, resource_id: str) -> Target | None:
        """Get a specific droplet by ID."""
        try:
            response = await _api_request_async("GET", f"/droplets/{resource_id}")
        except Exception as e:
            logger.warning(f"Failed to get DigitalOcean droplet {resource_id}: {e}")
            return None

        droplet = response.get("droplet")
        if not droplet:
            return None

        return _parse_droplet_to_target(droplet)

    async def provision(self, spec: TargetSpec) -> Target:
        """Provision a new DigitalOcean droplet from a spec.

        Blocks until SSH is ready.
        """
        assert isinstance(spec, DigitalOceanTarget), (
            f"DigitalOceanProvider.provision requires DigitalOceanTarget, got {type(spec).__name__}"
        )

        droplet_name = f"wafer-{spec.name}-{int(time.time())}"

        ssh_key_ids = await _get_ssh_key_ids()
        if not ssh_key_ids:
            logger.warning("No SSH keys found - droplet may not be accessible")

        create_data = {
            "name": droplet_name,
            "region": spec.region,
            "size": spec.size_slug,
            "image": spec.image,
            "ssh_keys": ssh_key_ids,
            "backups": False,
            "ipv6": True,
            "monitoring": True,
        }

        logger.info(f"Provisioning DigitalOcean droplet: {droplet_name}")
        response = await _api_request_async("POST", "/droplets", data=create_data)

        if not response or "droplet" not in response:
            raise DigitalOceanError(f"Failed to create droplet: {response}")

        droplet = response["droplet"]
        droplet_id = str(droplet["id"])
        logger.info(f"Droplet created: {droplet_id}")

        public_ip = await _wait_for_ssh(droplet_id, spec.provision_timeout)

        return Target(
            resource_id=droplet_id,
            provider="digitalocean",
            status="running",
            public_ip=public_ip,
            ssh_port=22,
            ssh_username="root",
            gpu_type=spec.gpu_type,
            name=droplet_name,
            created_at=datetime.now(timezone.utc).isoformat(),
            spec_name=spec.name,
        )

    async def terminate(self, resource_id: str) -> bool:
        """Terminate a DigitalOcean droplet."""
        return await _terminate_droplet(resource_id)
