"""RunPod GPU provisioning and lifecycle management.

Provides context manager for auto-provisioning RunPod pods:
- Checks state file for existing pod
- Provisions new pod if needed
- Returns SSH connection info for evaluation
- Cleans up based on keep_alive setting

State file: ~/.wafer/runpod_state.json
API key: WAFER_RUNPOD_API_KEY environment variable
"""

from __future__ import annotations

import json
import logging
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

import requests
import trio

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from wafer_core.utils.kernel_utils.targets.config import RunPodTarget

logger = logging.getLogger(__name__)

RUNPOD_API_URL = "https://api.runpod.io/graphql"
STATE_FILE = Path.home() / ".wafer" / "runpod_state.json"
LOCK_FILE = Path.home() / ".wafer" / "runpod_provision.lock"

# Per-target locks to prevent concurrent provisioning of the same target
_provision_locks: dict[str, trio.Lock] = {}


def _get_provision_lock(target_name: str) -> trio.Lock:
    """Get or create a lock for provisioning a specific target."""
    if target_name not in _provision_locks:
        _provision_locks[target_name] = trio.Lock()
    return _provision_locks[target_name]


class RunPodError(Exception):
    """Error during RunPod provisioning or management."""

    pass


@dataclass
class RunPodSSHInfo:
    """SSH connection info for a provisioned RunPod pod."""

    host: str
    port: int
    user: str
    pod_id: str


@dataclass
class PodState:
    """State of a provisioned pod, stored in state file."""

    pod_id: str
    target_name: str
    public_ip: str
    ssh_port: int
    ssh_username: str
    created_at: str  # ISO format


# =============================================================================
# State File Management
# =============================================================================


def _load_state() -> dict[str, PodState]:
    """Load pod state from file. Returns empty dict if file doesn't exist."""
    if not STATE_FILE.exists():
        return {}

    try:
        data = json.loads(STATE_FILE.read_text())
        return {name: PodState(**state) for name, state in data.items()}
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning(f"Corrupted state file, ignoring: {e}")
        return {}


def _save_state(state: dict[str, PodState]) -> None:
    """Save pod state to file."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = {
        name: {
            "pod_id": s.pod_id,
            "target_name": s.target_name,
            "public_ip": s.public_ip,
            "ssh_port": s.ssh_port,
            "ssh_username": s.ssh_username,
            "created_at": s.created_at,
        }
        for name, s in state.items()
    }
    STATE_FILE.write_text(json.dumps(data, indent=2))


def _add_pod_to_state(
    target_name: str, pod_id: str, public_ip: str, ssh_port: int, ssh_username: str
) -> None:
    """Add a pod to the state file."""
    state = _load_state()
    state[target_name] = PodState(
        pod_id=pod_id,
        target_name=target_name,
        public_ip=public_ip,
        ssh_port=ssh_port,
        ssh_username=ssh_username,
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    _save_state(state)


def _remove_pod_from_state(target_name: str) -> None:
    """Remove a pod from the state file."""
    state = _load_state()
    if target_name in state:
        del state[target_name]
        _save_state(state)


def get_pod_state(target_name: str) -> PodState | None:
    """Get pod state for a target, if it exists."""
    state = _load_state()
    return state.get(target_name)


# =============================================================================
# RunPod API
# =============================================================================


def _get_api_key() -> str:
    """Get RunPod API key from environment or auth.json."""
    from wafer_core.auth import get_api_key

    api_key = get_api_key("runpod")
    if not api_key:
        raise RunPodError(
            "RunPod API key not found.\n"
            "Set WAFER_RUNPOD_API_KEY environment variable, or run:\n"
            "  wafer auth login runpod\n"
            "Get your API key from: https://runpod.io/console/user/settings"
        )
    return api_key


def _graphql_request(query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
    """Make a GraphQL request to RunPod API."""
    api_key = _get_api_key()

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload: dict[str, Any] = {"query": query}
    if variables:
        payload["variables"] = variables

    response = requests.post(
        RUNPOD_API_URL,
        json=payload,
        headers=headers,
        timeout=(10, 30),
    )
    response.raise_for_status()

    data = response.json()
    if "errors" in data:
        raise RunPodError(f"GraphQL errors: {data['errors']}")

    return data.get("data", {})


async def _graphql_request_async(
    query: str, variables: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Async wrapper for GraphQL request."""
    return await trio.to_thread.run_sync(lambda: _graphql_request(query, variables))


async def check_pod_running(pod_id: str) -> bool:
    """Check if a pod is still running via API."""
    query = """
    query pod($input: PodFilter!) {
        pod(input: $input) {
            id
            desiredStatus
        }
    }
    """
    variables = {"input": {"podId": pod_id}}

    try:
        data = await _graphql_request_async(query, variables)
        pod = data.get("pod")
        if not pod:
            return False
        status = pod.get("desiredStatus", "").lower()
        return status == "running"
    except Exception as e:
        logger.warning(f"Failed to check pod status: {e}")
        return False


async def provision_pod(target: RunPodTarget) -> tuple[str, str, int, str]:
    """Provision a new RunPod pod.

    Returns: (pod_id, public_ip, ssh_port, ssh_username)
    """
    pod_name = f"wafer-{target.name}-{int(time.time())}"

    mutation = """
    mutation podFindAndDeployOnDemand($input: PodFindAndDeployOnDemandInput!) {
        podFindAndDeployOnDemand(input: $input) {
            id
            machineId
            machine {
                podHostId
            }
        }
    }
    """

    pod_input = {
        "gpuTypeId": target.gpu_type_id,
        "gpuCount": target.gpu_count,
        "cloudType": "SECURE",  # AMD MI300X only in secure cloud
        "name": pod_name,
        "supportPublicIp": True,
        "containerDiskInGb": target.container_disk_gb,
        "minVcpuCount": 1,
        "minMemoryInGb": 4,
        "ports": "22/tcp",
        "startSsh": True,
        "startJupyter": False,
        "env": [],
    }

    if target.template_id:
        # Template defines image, dockerArgs (sshd setup), and ports.
        # Required for non-RunPod images (e.g. rocm/pytorch) that don't
        # have RunPod's built-in SSH handler.
        pod_input["templateId"] = target.template_id
    else:
        pod_input["imageName"] = target.image

    variables = {"input": pod_input}

    logger.info(f"Provisioning RunPod pod: {pod_name}")

    try:
        data = await _graphql_request_async(mutation, variables)
    except requests.exceptions.HTTPError as e:
        if e.response is not None:
            try:
                error_data = e.response.json()
                error_msg = error_data.get("errors", [{}])[0].get("message", str(e))
            except Exception:
                error_msg = e.response.text
            raise RunPodError(f"Failed to provision pod: {error_msg}") from None
        raise

    pod_data = data.get("podFindAndDeployOnDemand")
    if not pod_data:
        raise RunPodError("No pod returned from deployment")

    pod_id = pod_data["id"]
    logger.info(f"Pod created: {pod_id}")

    # Wait for SSH to be ready
    public_ip, ssh_port, ssh_username = await _wait_for_ssh(pod_id, target.provision_timeout)

    return pod_id, public_ip, ssh_port, ssh_username


async def _wait_for_ssh(pod_id: str, timeout_seconds: int) -> tuple[str, int, str]:
    """Wait for pod to be ready with SSH access.

    Returns: (public_ip, ssh_port, ssh_username)
    """
    query = """
    query pod($input: PodFilter!) {
        pod(input: $input) {
            id
            desiredStatus
            machine {
                podHostId
            }
            runtime {
                ports {
                    ip
                    isIpPublic
                    privatePort
                    publicPort
                    type
                }
            }
        }
    }
    """
    variables = {"input": {"podId": pod_id}}

    start_time = time.time()
    logger.info(f"Waiting for pod {pod_id} to be ready (timeout: {timeout_seconds}s)...")

    while time.time() - start_time < timeout_seconds:
        try:
            data = await _graphql_request_async(query, variables)
        except Exception as e:
            logger.warning(f"Failed to get pod details: {e}")
            await trio.sleep(15)
            continue

        pod = data.get("pod")
        if not pod:
            logger.warning("Pod disappeared")
            raise RunPodError("Pod disappeared during provisioning")

        status = pod.get("desiredStatus", "").lower()

        if status in {"failed", "terminated"}:
            raise RunPodError(f"Pod in terminal state: {status}")

        # Check for SSH port
        runtime = pod.get("runtime")
        if runtime and status == "running":
            # ports can be null in JSON response, so use 'or []' instead of default
            for port in runtime.get("ports") or []:
                if (
                    port.get("privatePort") == 22
                    and port.get("isIpPublic")
                    and port.get("type") == "tcp"
                ):
                    public_ip = port.get("ip")
                    ssh_port = port.get("publicPort")

                    # Skip proxy SSH, wait for direct IP
                    if public_ip and public_ip != "ssh.runpod.io" and ssh_port:
                        elapsed = int(time.time() - start_time)
                        logger.info(f"Pod ready: {public_ip}:{ssh_port} (took {elapsed}s)")

                        # Wait for SSH daemon to initialize
                        logger.info("Waiting 30s for SSH daemon...")
                        await trio.sleep(30)

                        return public_ip, ssh_port, "root"

        await trio.sleep(15)

    raise RunPodError(f"Timeout waiting for SSH after {timeout_seconds}s")


async def terminate_pod(pod_id: str) -> bool:
    """Terminate a RunPod pod."""
    mutation = """
    mutation podTerminate($input: PodTerminateInput!) {
        podTerminate(input: $input)
    }
    """
    variables = {"input": {"podId": pod_id}}

    try:
        logger.info(f"Terminating pod {pod_id}...")
        await _graphql_request_async(mutation, variables)
        logger.info(f"Pod {pod_id} terminated")
        return True
    except Exception as e:
        logger.exception(f"Failed to terminate pod: {e}")
        return False


# =============================================================================
# Template Management (not yet implemented)
# =============================================================================
#
# The saveTemplate mutation allows creating reusable pod templates with custom
# configurations. Templates can specify docker images, environment setup,
# container disk size, and other pod settings.
#
# Example mutation:
#
#     mutation saveTemplate($input: SaveTemplateInput) {
#         saveTemplate(input: $input) {
#             id
#             name
#             imageName
#             containerDiskInGb
#             ports
#             dockerArgs
#             startSsh
#             startJupyter
#         }
#     }
#
# Example variables:
#
#     {
#         "input": {
#             "containerDiskInGb": 50,
#             "dockerArgs": "bash -c \"apt-get update && apt-get install -y openssh-server && ...\"",
#             "env": [],
#             "isPublic": false,
#             "isServerless": false,
#             "name": "template-name",
#             "ports": "22/tcp",
#             "portsConfig": [{"name": "SSH", "port": "22"}],
#             "readme": "",
#             "volumeInGb": 0,
#             "volumeMountPath": "",
#             "config": {},
#             "category": "AMD",
#             "imageName": "rocm/pytorch:rocm7.0.2_ubuntu24.04_py3.12_pytorch_release_2.7.1"
#         }
#     }
#
# Note: Template creation is not currently implemented in this module.
# If needed, implement a save_template() function following the pattern of
# provision_pod() and terminate_pod() above.


# =============================================================================
# Context Manager
# =============================================================================


@asynccontextmanager
async def runpod_ssh_context(target: RunPodTarget) -> AsyncIterator[RunPodSSHInfo]:
    """Context manager for RunPod SSH access.

    Lifecycle:
    1. Acquire per-target lock to prevent concurrent provisioning
    2. Check state file for existing pod
    3. If exists and running, reuse it
    4. If not, provision new pod
    5. Yield SSH info for evaluation
    6. If keep_alive=False, terminate pod

    Usage:
        async with runpod_ssh_context(target) as ssh_info:
            # ssh_info.host, ssh_info.port, ssh_info.user available
            await run_ssh_evaluation(ssh_info)
    """
    pod_id: str | None = None
    should_terminate = False
    provision_lock = _get_provision_lock(target.name)

    try:
        # Acquire lock to prevent concurrent provisioning of same target
        async with provision_lock:
            # Check for existing pod
            existing = get_pod_state(target.name)
            if existing:
                logger.info(f"Found existing pod {existing.pod_id} for target {target.name}")

                # Verify it's still running
                if await check_pod_running(existing.pod_id):
                    logger.info(f"Reusing existing pod {existing.pod_id}")
                    pod_id = existing.pod_id
                    ssh_info = RunPodSSHInfo(
                        host=existing.public_ip,
                        port=existing.ssh_port,
                        user=existing.ssh_username,
                        pod_id=existing.pod_id,
                    )
                    # Don't terminate reused pod unless keep_alive=False
                    should_terminate = not target.keep_alive
                else:
                    logger.info(
                        f"Existing pod {existing.pod_id} no longer running, removing from state"
                    )
                    _remove_pod_from_state(target.name)
                    existing = None

            if not existing or not await check_pod_running(existing.pod_id if existing else ""):
                # Provision new pod (still under lock)
                pod_id, public_ip, ssh_port, ssh_username = await provision_pod(target)

                # Save to state file
                _add_pod_to_state(target.name, pod_id, public_ip, ssh_port, ssh_username)

                should_terminate = not target.keep_alive

                ssh_info = RunPodSSHInfo(
                    host=public_ip,
                    port=ssh_port,
                    user=ssh_username,
                    pod_id=pod_id,
                )

        # Yield outside the lock so concurrent evals can run on the same pod
        yield ssh_info

    finally:
        if should_terminate and pod_id:
            await terminate_pod(pod_id)
            _remove_pod_from_state(target.name)
        elif pod_id and target.keep_alive:
            logger.warning(
                f"Pod {pod_id} left running (keep_alive=True). "
                f"Run 'wafer config targets cleanup {target.name}' to terminate and stop charges."
            )


# =============================================================================
# Cleanup Functions (for CLI)
# =============================================================================


async def cleanup_target(target_name: str) -> bool:
    """Terminate pod for a specific target and remove from state.

    Returns True if pod was terminated, False if no pod found.
    """
    state = get_pod_state(target_name)
    if not state:
        logger.info(f"No running pod found for target {target_name}")
        return False

    success = await terminate_pod(state.pod_id)
    if success:
        _remove_pod_from_state(target_name)
    return success


async def sync_pods_from_api() -> list[PodState]:
    """Query RunPod API for all running pods and update local state.

    This discovers pods that exist on the account but aren't in our state file
    (e.g., created manually or by another machine). Updates the state file with
    any wafer-created pods found.

    Returns list of all running pods with SSH info.
    """
    query = """
    query {
        myself {
            pods {
                id
                name
                desiredStatus
                runtime {
                    ports {
                        ip
                        isIpPublic
                        privatePort
                        publicPort
                    }
                }
            }
        }
    }
    """

    try:
        data = await _graphql_request_async(query)
    except Exception as e:
        logger.warning(f"Failed to query pods from API: {e}")
        return []

    pods = data.get("myself", {}).get("pods", [])
    running_pods = []

    for pod in pods:
        status = pod.get("desiredStatus", "").lower()
        if status != "running":
            continue

        pod_id = pod["id"]
        pod_name = pod.get("name", "")

        # Extract SSH info
        runtime = pod.get("runtime")
        if not runtime:
            continue

        public_ip = None
        ssh_port = None
        for port in runtime.get("ports") or []:
            if port.get("privatePort") == 22 and port.get("isIpPublic"):
                public_ip = port.get("ip")
                ssh_port = port.get("publicPort")
                break

        if not public_ip or not ssh_port:
            continue

        # Extract target name from pod name (wafer-{target_name}-{timestamp})
        target_name = None
        if pod_name.startswith("wafer-"):
            parts = pod_name.split("-")
            if len(parts) >= 3:
                # Handle target names with hyphens: wafer-runpod-mi300x-1234567
                target_name = "-".join(parts[1:-1])

        pod_state = PodState(
            pod_id=pod_id,
            target_name=target_name or pod_name,
            public_ip=public_ip,
            ssh_port=ssh_port,
            ssh_username="root",
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        running_pods.append(pod_state)

        # Update state file if this is a wafer-created pod
        if target_name:
            existing = get_pod_state(target_name)
            if not existing or existing.pod_id != pod_id:
                logger.info(f"Syncing pod {pod_id} to state for target {target_name}")
                _add_pod_to_state(target_name, pod_id, public_ip, ssh_port, "root")

    return running_pods


async def list_running_pods() -> list[PodState]:
    """List all running pods by querying the RunPod API.

    Syncs state file with API to discover pods not in local state.
    Returns list of running pods with SSH info.
    """
    return await sync_pods_from_api()


async def cleanup_all_pods() -> int:
    """Terminate all pods in state file.

    Returns number of pods terminated.
    """
    state = _load_state()
    count = 0

    for name, pod_state in state.items():
        if await terminate_pod(pod_state.pod_id):
            count += 1
        _remove_pod_from_state(name)

    return count
