"""API client for baseline kernel trace results.

Interacts with the Supabase baselines table to store and retrieve kernel dispatch info.
Results are keyed by (op, shape, dtype, pytorch_version, runtime_version, gpu_arch).
Since kernel dispatch is deterministic for a given environment, this serves as a
shared lookup table across all users.
"""

import logging

import httpx

from wafer_core.tools.dispatch_baseline.dtypes import (
    KernelInfo,
    KernelTraceResult,
    OpSpec,
)

logger = logging.getLogger(__name__)

# API timeout for baseline lookups
API_TIMEOUT = 30.0


def _get_api_config() -> tuple[str, dict[str, str]]:
    """Get API URL and auth headers.

    Returns:
        Tuple of (api_url, headers)
    """
    # Import here to avoid circular imports and allow use without CLI
    try:
        from wafer.api_client import get_api_url
        from wafer.auth import get_auth_headers

        return get_api_url(), get_auth_headers()
    except ImportError:
        # If CLI not installed, return defaults (won't work without auth)
        return "https://api.wafer.ai", {}


def lookup_baseline(
    op_spec: OpSpec,
    hardware: str,
    pytorch_version: str,
    runtime_version: str,
    gpu_arch: str,
) -> KernelTraceResult | None:
    """Look up baseline result from the database.

    Args:
        op_spec: Operation specification
        hardware: Hardware name (for display, not part of cache key)
        pytorch_version: PyTorch version string
        runtime_version: CUDA version string
        gpu_arch: GPU architecture (e.g., "sm_90")

    Returns:
        KernelTraceResult if found, None otherwise
    """
    api_url, headers = _get_api_config()

    if not headers.get("Authorization"):
        logger.debug("No auth headers, skipping baseline lookup")
        return None

    # Build request
    request_data = {
        "op": op_spec.op,
        "inputs": [
            {"name": t.name, "shape": list(t.shape), "dtype": t.dtype}
            for t in op_spec.inputs
        ],
        "kwargs": op_spec.kwargs,
        "pytorch_version": pytorch_version,
        "runtime_version": runtime_version,
        "gpu_arch": gpu_arch,
    }

    try:
        with httpx.Client(timeout=API_TIMEOUT, headers=headers) as client:
            response = client.post(f"{api_url}/v1/baselines/lookup", json=request_data)
            response.raise_for_status()
            data = response.json()

        if not data.get("found"):
            return None

        # Reconstruct result
        kernels = [
            KernelInfo(
                name=k["name"],
                duration_us=k["duration_us"],
            )
            for k in data.get("kernels", [])
        ]

        primary_data = data.get("primary_kernel")
        primary_kernel = KernelInfo(
            name=primary_data["name"],
            duration_us=primary_data["duration_us"],
        ) if primary_data else (kernels[0] if kernels else None)

        return KernelTraceResult(
            op_spec=op_spec,
            hardware=hardware,
            kernels=kernels,
            primary_kernel=primary_kernel,
            # Note: roofline will be recomputed by the caller
        )

    except httpx.HTTPError as e:
        logger.warning(f"Baseline lookup failed: {e}")
        return None
    except Exception as e:
        logger.warning(f"Baseline lookup error: {e}")
        return None


def store_baseline(
    result: KernelTraceResult,
    pytorch_version: str,
    runtime_version: str,
    gpu_arch: str,
) -> bool:
    """Store baseline result in the database.

    Args:
        result: Trace result to cache
        pytorch_version: PyTorch version string
        runtime_version: CUDA version string
        gpu_arch: GPU architecture

    Returns:
        True if stored successfully, False otherwise
    """
    if result.error:
        # Don't cache errors
        return False

    if not result.primary_kernel:
        # Don't cache empty results
        return False

    api_url, headers = _get_api_config()

    if not headers.get("Authorization"):
        logger.debug("No auth headers, skipping baseline store")
        return False

    # Build request
    request_data = {
        "op": result.op_spec.op,
        "inputs": [
            {"name": t.name, "shape": list(t.shape), "dtype": t.dtype}
            for t in result.op_spec.inputs
        ],
        "kwargs": result.op_spec.kwargs,
        "pytorch_version": pytorch_version,
        "runtime_version": runtime_version,
        "gpu_arch": gpu_arch,
        "hardware_name": result.hardware,
        "primary_kernel": {
            "name": result.primary_kernel.name,
            "duration_us": result.primary_kernel.duration_us,
        },
        "kernels": [
            {
                "name": k.name,
                "duration_us": k.duration_us,
            }
            for k in result.kernels
        ],
    }

    try:
        with httpx.Client(timeout=API_TIMEOUT, headers=headers) as client:
            response = client.post(f"{api_url}/v1/baselines/store", json=request_data)
            response.raise_for_status()
            data = response.json()

        if data.get("created"):
            logger.info(f"Stored baseline: {result.op_spec.op} ({gpu_arch})")
        else:
            logger.debug(f"Baseline already exists: {result.op_spec.op} ({gpu_arch})")

        return True

    except httpx.HTTPError as e:
        logger.warning(f"Baseline store failed: {e}")
        return False
    except Exception as e:
        logger.warning(f"Baseline store error: {e}")
        return False


