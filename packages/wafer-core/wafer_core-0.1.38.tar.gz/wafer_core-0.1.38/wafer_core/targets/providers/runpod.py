"""RunPod provider — adapts existing RunPod GraphQL API to TargetProvider protocol."""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone

from wafer_core.targets.runpod import (
    RunPodError,
    _graphql_request_async,
    _wait_for_ssh,
)
from wafer_core.targets.runpod import (
    terminate_pod as _terminate_pod,
)
from wafer_core.targets.types import Target, TargetSpec
from wafer_core.utils.kernel_utils.targets.config import RunPodTarget

logger = logging.getLogger(__name__)


def _parse_pod_to_target(pod: dict) -> Target | None:
    """Parse a RunPod API pod response into a Target.

    Returns None if the pod has no usable SSH info.
    """
    pod_id = pod.get("id", "")
    pod_name = pod.get("name", "")
    status_raw = pod.get("desiredStatus", "").lower()

    # Map RunPod statuses to our status values
    status = status_raw if status_raw else "unknown"

    # Extract SSH info from runtime ports
    public_ip = None
    ssh_port = None
    runtime = pod.get("runtime")
    if runtime:
        for port in runtime.get("ports") or []:
            if port.get("privatePort") == 22 and port.get("isIpPublic"):
                ip = port.get("ip")
                # Skip proxy SSH (ssh.runpod.io), want direct IP
                if ip and ip != "ssh.runpod.io":
                    public_ip = ip
                    ssh_port = port.get("publicPort")
                    break

    # Infer spec_name from pod naming convention: wafer-{spec_name}-{timestamp}
    spec_name = None
    if pod_name.startswith("wafer-"):
        parts = pod_name.split("-")
        if len(parts) >= 3:
            spec_name = "-".join(parts[1:-1])

    # Extract GPU type
    gpu_type = ""
    machine = pod.get("machine")
    if machine:
        gpu_type_info = machine.get("gpuType")
        if gpu_type_info:
            gpu_type = gpu_type_info.get("displayName", "")

    cost = pod.get("costPerHr")

    return Target(
        resource_id=pod_id,
        provider="runpod",
        status=status,
        public_ip=public_ip,
        ssh_port=ssh_port,
        ssh_username="root",
        gpu_type=gpu_type,
        name=pod_name or None,
        created_at=None,  # RunPod API doesn't expose creation time in list query
        spec_name=spec_name,
        price_per_hour=float(cost) if cost else None,
    )


class RunPodProvider:
    """RunPod implementation of TargetProvider.

    Wraps existing GraphQL API calls:
    - list_targets: myself { pods { ... } }
    - get_target: pod(input: { podId }) { ... }
    - provision: podFindAndDeployOnDemand
    - terminate: podTerminate
    """

    async def list_targets(self) -> list[Target]:
        """List all running pods on the RunPod account."""
        query = """
        query {
            myself {
                pods {
                    id
                    name
                    desiredStatus
                    costPerHr
                    machine {
                        podHostId
                        gpuType {
                            displayName
                        }
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
        }
        """

        try:
            data = await _graphql_request_async(query)
        except RunPodError:
            raise
        except Exception as e:
            logger.warning(f"Failed to list RunPod pods: {e}")
            return []

        pods = data.get("myself", {}).get("pods", [])
        targets = []

        for pod in pods:
            target = _parse_pod_to_target(pod)
            if target is not None:
                targets.append(target)

        return targets

    async def get_target(self, resource_id: str) -> Target | None:
        """Get a specific pod by ID."""
        query = """
        query pod($input: PodFilter!) {
            pod(input: $input) {
                id
                name
                desiredStatus
                costPerHr
                machine {
                    podHostId
                    gpuType {
                        displayName
                    }
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
        variables = {"input": {"podId": resource_id}}

        try:
            data = await _graphql_request_async(query, variables)
        except Exception as e:
            logger.warning(f"Failed to get RunPod pod {resource_id}: {e}")
            return None

        pod = data.get("pod")
        if not pod:
            return None

        return _parse_pod_to_target(pod)

    async def provision(self, spec: TargetSpec) -> Target:
        """Provision a new RunPod pod from a spec.

        Blocks until SSH is ready.
        """
        assert isinstance(spec, RunPodTarget), (
            f"RunPodProvider.provision requires RunPodTarget, got {type(spec).__name__}"
        )

        pod_name = f"wafer-{spec.name}-{int(time.time())}"

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

        pod_input: dict = {
            "gpuTypeId": spec.gpu_type_id,
            "gpuCount": spec.gpu_count,
            "cloudType": "SECURE",
            "name": pod_name,
            "supportPublicIp": True,
            "containerDiskInGb": spec.container_disk_gb,
            "minVcpuCount": 1,
            "minMemoryInGb": 4,
            "ports": "22/tcp",
            "startSsh": True,
            "startJupyter": False,
            "env": [],
        }

        if spec.template_id:
            pod_input["templateId"] = spec.template_id
        else:
            pod_input["imageName"] = spec.image

        logger.info(f"Provisioning RunPod pod: {pod_name}")
        data = await _graphql_request_async(mutation, {"input": pod_input})

        pod_data = data.get("podFindAndDeployOnDemand")
        if not pod_data:
            raise RunPodError("No pod returned from deployment")

        pod_id = pod_data["id"]
        logger.info(f"Pod created: {pod_id}")

        public_ip, ssh_port, ssh_username = await _wait_for_ssh(pod_id, spec.provision_timeout)

        return Target(
            resource_id=pod_id,
            provider="runpod",
            status="running",
            public_ip=public_ip,
            ssh_port=ssh_port,
            ssh_username=ssh_username,
            gpu_type=spec.gpu_type,
            name=pod_name,
            created_at=datetime.now(timezone.utc).isoformat(),
            spec_name=spec.name,
        )

    async def terminate(self, resource_id: str) -> bool:
        """Terminate a RunPod pod."""
        return await _terminate_pod(resource_id)
