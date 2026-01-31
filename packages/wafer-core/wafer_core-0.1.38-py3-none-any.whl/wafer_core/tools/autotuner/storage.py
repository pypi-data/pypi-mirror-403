"""API client for storing autotuner results in Supabase via wafer-api."""

import logging
import os
from typing import Any

import httpx

from wafer_core.tools.autotuner.dtypes import Sweep, Trial

logger = logging.getLogger(__name__)

DEFAULT_API_URL = "http://localhost:8000"


def get_api_url() -> str:
    """Get API URL from environment or default."""
    return os.environ.get("WAFER_API_URL", DEFAULT_API_URL)


def _get_auth_headers() -> dict[str, str]:
    """Get auth headers from stored credentials."""
    # Import here to avoid circular dependency
    try:
        from wafer.auth import get_auth_headers
        return get_auth_headers()
    except ImportError:
        # If running in wafer-core without CLI, check environment
        api_key = os.environ.get("WAFER_API_KEY")
        if api_key:
            return {"Authorization": f"Bearer {api_key}"}
        logger.warning("No authentication credentials found")
        return {}


async def create_sweep(sweep: Sweep) -> str:
    """Create a new sweep in the database.

    Args:
        sweep: Sweep object to create

    Returns:
        Sweep ID

    Raises:
        httpx.HTTPError: If API request fails
    """
    api_url = get_api_url()
    headers = _get_auth_headers()

    # Build request matching CreateSweepRequest model
    request_data = {
        "name": sweep.name,
        "description": sweep.description,
        "config": sweep.config,
        "total_trials": sweep.total_trials,
    }

    async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
        response = await client.post(
            f"{api_url}/v1/autotuner/sweeps",
            json=request_data,
        )
        response.raise_for_status()
        data = response.json()

    logger.info(f"Created sweep: {data['id']}")
    return data["id"]


async def add_trial(trial: Trial) -> None:
    """Add a trial result to the database.

    Args:
        trial: Trial object to store

    Raises:
        httpx.HTTPError: If API request fails
    """
    api_url = get_api_url()
    headers = _get_auth_headers()

    # Build request matching CreateTrialRequest model
    request_data = {
        "trial_number": trial.trial_number,
        "config": trial.config,
        "metrics": trial.metrics,
        "stdout": trial.stdout,
        "stderr": trial.stderr,
        "exit_code": trial.exit_code,
        "duration_ms": trial.duration_ms,
        "status": trial.status.value,  # Convert enum to string
        "passed_constraints": trial.passed_constraints,
        "started_at": trial.started_at.isoformat(),
        "completed_at": trial.completed_at.isoformat(),
    }

    async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
        response = await client.post(
            f"{api_url}/v1/autotuner/sweeps/{trial.sweep_id}/trials",
            json=request_data,
        )
        response.raise_for_status()

    logger.debug(f"Added trial {trial.id} for sweep {trial.sweep_id}")


async def get_sweep(sweep_id: str) -> Sweep:
    """Get sweep by ID.

    Args:
        sweep_id: Sweep ID

    Returns:
        Sweep object

    Raises:
        httpx.HTTPError: If API request fails
    """
    api_url = get_api_url()
    headers = _get_auth_headers()

    async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
        response = await client.get(f"{api_url}/v1/autotuner/sweeps/{sweep_id}")
        response.raise_for_status()
        data = response.json()

    # API returns SweepWithTrialsResponse, extract sweep
    return Sweep.from_dict(data["sweep"])


async def get_trials(sweep_id: str) -> list[Trial]:
    """Get all trials for a sweep.

    Args:
        sweep_id: Sweep ID

    Returns:
        List of Trial objects

    Raises:
        httpx.HTTPError: If API request fails
    """
    api_url = get_api_url()
    headers = _get_auth_headers()

    async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
        response = await client.get(f"{api_url}/v1/autotuner/sweeps/{sweep_id}")
        response.raise_for_status()
        data = response.json()

    # API returns SweepWithTrialsResponse, extract trials
    return [Trial.from_dict(t) for t in data["trials"]]


async def list_sweeps(user_id: str | None = None) -> list[Sweep]:
    """List all sweeps for a user.

    Args:
        user_id: Optional user ID filter (not used - auth determines user)

    Returns:
        List of Sweep objects

    Raises:
        httpx.HTTPError: If API request fails
    """
    api_url = get_api_url()
    headers = _get_auth_headers()

    async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
        response = await client.get(f"{api_url}/v1/autotuner/sweeps")
        response.raise_for_status()
        data = response.json()

    # API returns {"sweeps": list[SweepResponse]}
    return [Sweep.from_dict(s) for s in data["sweeps"]]


async def update_sweep_status(sweep_id: str, status: str, completed_trials: int | None = None) -> None:
    """Update sweep status in the database.

    Args:
        sweep_id: Sweep ID to update
        status: New status (pending, running, completed, failed)
        completed_trials: Optional completed trials count

    Raises:
        httpx.HTTPError: If API request fails
    """
    api_url = get_api_url()
    headers = _get_auth_headers()

    update_data = {"status": status}
    if completed_trials is not None:
        update_data["completed_trials"] = completed_trials

    async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
        response = await client.patch(
            f"{api_url}/v1/autotuner/sweeps/{sweep_id}/status",
            json=update_data,
        )
        response.raise_for_status()

    logger.info(f"Updated sweep {sweep_id} status to {status}")


async def delete_sweep(sweep_id: str) -> None:
    """Delete a sweep and all its trials.

    Args:
        sweep_id: Sweep ID to delete

    Raises:
        httpx.HTTPError: If API request fails
    """
    api_url = get_api_url()
    headers = _get_auth_headers()

    async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
        response = await client.delete(f"{api_url}/v1/autotuner/sweeps/{sweep_id}")
        response.raise_for_status()

    logger.info(f"Deleted sweep: {sweep_id}")
