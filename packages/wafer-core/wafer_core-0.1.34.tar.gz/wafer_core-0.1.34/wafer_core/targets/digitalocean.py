"""DigitalOcean AMD GPU provisioning and lifecycle management.

Provides context manager for auto-provisioning DigitalOcean AMD droplets:
- Checks state file for existing droplet
- Provisions new droplet if needed
- Returns SSH connection info for evaluation
- Cleans up based on keep_alive setting

State file: ~/.wafer/digitalocean_state.json
API key: WAFER_AMD_DIGITALOCEAN_API_KEY environment variable
"""

from __future__ import annotations

import json
import logging
import os
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from http import HTTPStatus
from pathlib import Path
from typing import TYPE_CHECKING, Any

import requests
import trio

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from wafer_core.utils.kernel_utils.targets.config import DigitalOceanTarget

logger = logging.getLogger(__name__)

DIGITALOCEAN_AMD_API_URL = "https://api-amd.digitalocean.com/v2"
STATE_FILE = Path.home() / ".wafer" / "digitalocean_state.json"

# Per-target locks to prevent concurrent provisioning of the same target
_provision_locks: dict[str, trio.Lock] = {}


def _get_provision_lock(target_name: str) -> trio.Lock:
    """Get or create a lock for provisioning a specific target."""
    if target_name not in _provision_locks:
        _provision_locks[target_name] = trio.Lock()
    return _provision_locks[target_name]


class DigitalOceanError(Exception):
    """Error during DigitalOcean provisioning or management."""

    pass


@dataclass
class DigitalOceanSSHInfo:
    """SSH connection info for a provisioned DigitalOcean droplet."""

    host: str
    port: int
    user: str
    droplet_id: str


@dataclass
class DropletState:
    """State of a provisioned droplet, stored in state file."""

    droplet_id: str
    target_name: str
    public_ip: str
    ssh_port: int
    ssh_username: str
    created_at: str  # ISO format


# =============================================================================
# State File Management
# =============================================================================


def _load_state() -> dict[str, DropletState]:
    """Load droplet state from file. Returns empty dict if file doesn't exist."""
    if not STATE_FILE.exists():
        return {}

    try:
        data = json.loads(STATE_FILE.read_text())
        return {name: DropletState(**state) for name, state in data.items()}
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning(f"Corrupted state file, ignoring: {e}")
        return {}


def _save_state(state: dict[str, DropletState]) -> None:
    """Save droplet state to file."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = {
        name: {
            "droplet_id": s.droplet_id,
            "target_name": s.target_name,
            "public_ip": s.public_ip,
            "ssh_port": s.ssh_port,
            "ssh_username": s.ssh_username,
            "created_at": s.created_at,
        }
        for name, s in state.items()
    }
    STATE_FILE.write_text(json.dumps(data, indent=2))


def _add_droplet_to_state(
    target_name: str, droplet_id: str, public_ip: str, ssh_port: int, ssh_username: str
) -> None:
    """Add a droplet to the state file."""
    state = _load_state()
    state[target_name] = DropletState(
        droplet_id=droplet_id,
        target_name=target_name,
        public_ip=public_ip,
        ssh_port=ssh_port,
        ssh_username=ssh_username,
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    _save_state(state)


def _remove_droplet_from_state(target_name: str) -> None:
    """Remove a droplet from the state file."""
    state = _load_state()
    if target_name in state:
        del state[target_name]
        _save_state(state)


def get_droplet_state(target_name: str) -> DropletState | None:
    """Get droplet state for a target, if it exists."""
    state = _load_state()
    return state.get(target_name)


# =============================================================================
# DigitalOcean API
# =============================================================================


def _get_api_key() -> str:
    """Get DigitalOcean API key from environment or auth.json."""
    from wafer_core.auth import get_api_key

    api_key = get_api_key("digitalocean")
    if not api_key:
        raise DigitalOceanError(
            "DigitalOcean API key not found.\n"
            "Set WAFER_AMD_DIGITALOCEAN_API_KEY environment variable, or run:\n"
            "  wafer auth login digitalocean\n"
            "Get your API key from: https://cloud.digitalocean.com/account/api/tokens"
        )
    return api_key


def _api_request(
    method: str,
    endpoint: str,
    data: dict | None = None,
    params: dict | None = None,
) -> dict[str, Any]:
    """Make a request to DigitalOcean AMD API."""
    api_key = _get_api_key()

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    url = f"{DIGITALOCEAN_AMD_API_URL}{endpoint}"
    logger.debug(f"API request: {method} {url}")

    response = requests.request(
        method=method,
        url=url,
        json=data,
        params=params,
        headers=headers,
        timeout=(10, 30),
    )

    if not response.ok:
        response.raise_for_status()

    if response.status_code == HTTPStatus.NO_CONTENT or not response.content:
        return {}

    return response.json()


async def _api_request_async(
    method: str,
    endpoint: str,
    data: dict | None = None,
    params: dict | None = None,
) -> dict[str, Any]:
    """Async wrapper for API request."""
    return await trio.to_thread.run_sync(lambda: _api_request(method, endpoint, data, params))


async def _get_ssh_key_ids() -> list[int]:
    """Get SSH key IDs from DigitalOcean account."""
    try:
        response = await _api_request_async("GET", "/account/keys")
        ssh_keys = response.get("ssh_keys", [])
        return [key["id"] for key in ssh_keys]
    except Exception as e:
        logger.warning(f"Failed to fetch SSH keys: {e}")
        return []


async def check_droplet_running(droplet_id: str) -> bool:
    """Check if a droplet is still running via API."""
    try:
        response = await _api_request_async("GET", f"/droplets/{droplet_id}")
        droplet = response.get("droplet")
        if not droplet:
            return False
        status = droplet.get("status", "").lower()
        return status == "active"
    except requests.exceptions.HTTPError as e:
        if e.response is not None and e.response.status_code == HTTPStatus.NOT_FOUND:
            return False
        logger.warning(f"Failed to check droplet status: {e}")
        return False
    except Exception as e:
        logger.warning(f"Failed to check droplet status: {e}")
        return False


async def provision_droplet(target: DigitalOceanTarget) -> tuple[str, str, int, str]:
    """Provision a new DigitalOcean droplet.

    Returns: (droplet_id, public_ip, ssh_port, ssh_username)
    """
    droplet_name = f"wafer-{target.name}-{int(time.time())}"

    # Get SSH keys
    ssh_key_ids = await _get_ssh_key_ids()
    if not ssh_key_ids:
        logger.warning("No SSH keys found - droplet may not be accessible")

    create_data = {
        "name": droplet_name,
        "region": target.region,
        "size": target.size_slug,
        "image": target.image,
        "ssh_keys": ssh_key_ids,
        "backups": False,
        "ipv6": True,
        "monitoring": True,
    }

    logger.info(f"Provisioning DigitalOcean droplet: {droplet_name}")

    try:
        response = await _api_request_async("POST", "/droplets", data=create_data)
    except requests.exceptions.HTTPError as e:
        if e.response is not None:
            try:
                error_data = e.response.json()
                error_msg = error_data.get("message", str(e))
            except Exception:
                error_msg = e.response.text

            if "not available" in error_msg.lower():
                raise DigitalOceanError(
                    f"GPU size '{target.size_slug}' is not available in region '{target.region}'.\n"
                    f"DigitalOcean AMD Developer Cloud GPUs may be at capacity."
                ) from None
            raise DigitalOceanError(f"Failed to provision droplet: {error_msg}") from None
        raise

    if not response or "droplet" not in response:
        raise DigitalOceanError(f"Failed to create droplet: {response}")

    droplet = response["droplet"]
    droplet_id = str(droplet["id"])

    logger.info(f"Droplet created: {droplet_id}")

    # Wait for SSH to be ready
    public_ip = await _wait_for_ssh(droplet_id, target.provision_timeout)

    return droplet_id, public_ip, 22, "root"


async def _wait_for_ssh(droplet_id: str, timeout_seconds: int) -> str:
    """Wait for droplet to be ready with SSH access.

    Returns: public_ip
    """
    start_time = time.time()
    logger.info(f"Waiting for droplet {droplet_id} to be ready (timeout: {timeout_seconds}s)...")

    # Brief delay for API consistency
    await trio.sleep(5)

    while time.time() - start_time < timeout_seconds:
        try:
            response = await _api_request_async("GET", f"/droplets/{droplet_id}")

            if not response or "droplet" not in response:
                await trio.sleep(10)
                continue

            droplet = response["droplet"]
            status = droplet.get("status", "")

            if status == "active":
                # Extract public IP
                networks = droplet.get("networks", {})
                v4_networks = networks.get("v4", [])
                for net in v4_networks:
                    if net.get("type") == "public":
                        public_ip = net.get("ip_address")
                        if public_ip:
                            elapsed = int(time.time() - start_time)
                            logger.info(f"Droplet ready: {public_ip} (took {elapsed}s)")

                            # Wait for SSH daemon to initialize
                            logger.info("Waiting 20s for SSH daemon...")
                            await trio.sleep(20)

                            return public_ip

            elif status in {"off", "archive"}:
                raise DigitalOceanError(f"Droplet in terminal state: {status}")

        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code == HTTPStatus.NOT_FOUND:
                logger.debug(f"Droplet {droplet_id} not found yet, waiting...")
            else:
                logger.warning(f"HTTP error checking droplet status: {e}")
        except DigitalOceanError:
            raise
        except Exception as e:
            logger.warning(f"Error checking droplet status: {e}")

        await trio.sleep(10)

    raise DigitalOceanError(f"Timeout waiting for SSH after {timeout_seconds}s")


async def terminate_droplet(droplet_id: str) -> bool:
    """Terminate a DigitalOcean droplet."""
    try:
        logger.info(f"Terminating droplet {droplet_id}...")
        await _api_request_async("DELETE", f"/droplets/{droplet_id}")
        logger.info(f"Droplet {droplet_id} terminated")
        return True
    except Exception as e:
        logger.exception(f"Failed to terminate droplet: {e}")
        return False


# =============================================================================
# Context Manager
# =============================================================================


@asynccontextmanager
async def digitalocean_ssh_context(
    target: DigitalOceanTarget,
) -> AsyncIterator[DigitalOceanSSHInfo]:
    """Context manager for DigitalOcean SSH access.

    Lifecycle:
    1. Acquire per-target lock to prevent concurrent provisioning
    2. Check state file for existing droplet
    3. If exists and running, reuse it
    4. If not, provision new droplet
    5. Yield SSH info for evaluation
    6. If keep_alive=False, terminate droplet

    Usage:
        async with digitalocean_ssh_context(target) as ssh_info:
            # ssh_info.host, ssh_info.port, ssh_info.user available
            await run_ssh_evaluation(ssh_info)
    """
    droplet_id: str | None = None
    should_terminate = False
    provision_lock = _get_provision_lock(target.name)

    try:
        # Acquire lock to prevent concurrent provisioning of same target
        async with provision_lock:
            # Check for existing droplet
            existing = get_droplet_state(target.name)
            if existing:
                logger.info(
                    f"Found existing droplet {existing.droplet_id} for target {target.name}"
                )

                # Verify it's still running
                if await check_droplet_running(existing.droplet_id):
                    logger.info(f"Reusing existing droplet {existing.droplet_id}")
                    droplet_id = existing.droplet_id
                    ssh_info = DigitalOceanSSHInfo(
                        host=existing.public_ip,
                        port=existing.ssh_port,
                        user=existing.ssh_username,
                        droplet_id=existing.droplet_id,
                    )
                    # Don't terminate reused droplet unless keep_alive=False
                    should_terminate = not target.keep_alive
                else:
                    logger.info(
                        f"Existing droplet {existing.droplet_id} no longer running, removing from state"
                    )
                    _remove_droplet_from_state(target.name)
                    existing = None

            if not existing or not await check_droplet_running(
                existing.droplet_id if existing else ""
            ):
                # Provision new droplet (still under lock)
                droplet_id, public_ip, ssh_port, ssh_username = await provision_droplet(target)

                # Save to state file
                _add_droplet_to_state(target.name, droplet_id, public_ip, ssh_port, ssh_username)

                should_terminate = not target.keep_alive

                ssh_info = DigitalOceanSSHInfo(
                    host=public_ip,
                    port=ssh_port,
                    user=ssh_username,
                    droplet_id=droplet_id,
                )

        # Yield outside the lock so concurrent evals can run on the same droplet
        yield ssh_info

    finally:
        if should_terminate and droplet_id:
            await terminate_droplet(droplet_id)
            _remove_droplet_from_state(target.name)
        elif droplet_id and target.keep_alive:
            logger.warning(
                f"Droplet {droplet_id} left running (keep_alive=True). "
                f"Run 'wafer config targets cleanup {target.name}' to terminate and stop charges."
            )


# =============================================================================
# Cleanup Functions (for CLI)
# =============================================================================


async def cleanup_digitalocean_target(target_name: str) -> bool:
    """Terminate droplet for a specific target and remove from state.

    Returns True if droplet was terminated, False if no droplet found.
    """
    state = get_droplet_state(target_name)
    if not state:
        logger.info(f"No running droplet found for target {target_name}")
        return False

    success = await terminate_droplet(state.droplet_id)
    if success:
        _remove_droplet_from_state(target_name)
    return success


async def list_running_droplets() -> list[DropletState]:
    """List all droplets in state file that are still running."""
    state = _load_state()
    running = []

    for name, droplet_state in state.items():
        if await check_droplet_running(droplet_state.droplet_id):
            running.append(droplet_state)
        else:
            # Clean up stale entry
            logger.info(f"Removing stale state for {name} (droplet {droplet_state.droplet_id})")
            _remove_droplet_from_state(name)

    return running


async def cleanup_all_droplets() -> int:
    """Terminate all droplets in state file.

    Returns number of droplets terminated.
    """
    state = _load_state()
    count = 0

    for name, droplet_state in state.items():
        if await terminate_droplet(droplet_state.droplet_id):
            count += 1
        _remove_droplet_from_state(name)

    return count
