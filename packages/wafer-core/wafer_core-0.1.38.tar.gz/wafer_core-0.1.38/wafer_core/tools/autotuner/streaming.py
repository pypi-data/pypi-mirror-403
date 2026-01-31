"""Streaming support for autotuner - writes trial results to file for real-time updates."""

import json
import logging
from pathlib import Path
from typing import Any

import trio

from wafer_core.tools.autotuner.core import resume_sweep, run_sweep
from wafer_core.tools.autotuner.dtypes import AutotunerConfig, Sweep, Trial
from wafer_core.tools.autotuner.storage import create_sweep, get_sweep

logger = logging.getLogger(__name__)


async def run_sweep_streaming(
    config: dict[str, Any] | AutotunerConfig,
    working_dir: str | Path,
    progress_file: str | Path,
) -> str:
    """Run a sweep and stream trial results to a file for extension to read.

    Args:
        config: Sweep configuration (dict or AutotunerConfig object)
        working_dir: Directory to execute trials in
        progress_file: File path to write trial updates (one JSON per line)

    Returns:
        Sweep ID

    The progress file format is newline-delimited JSON, where each line is a trial result:
    ```
    {"id": "abc", "trial_number": 0, "status": "success", "metrics": {"acc": 0.95}, ...}
    {"id": "def", "trial_number": 1, "status": "failed", ...}
    ```

    This allows the extension to tail the file and get real-time updates as trials complete.
    """
    # Convert config dict to AutotunerConfig if needed
    if isinstance(config, dict):
        config = AutotunerConfig.from_dict(config)

    # Convert paths to Path objects if needed
    if isinstance(working_dir, str):
        working_dir = Path(working_dir)
    if isinstance(progress_file, str):
        progress_file = Path(progress_file)

    # Create sweep object
    import uuid
    from datetime import datetime, timezone

    sweep_id = str(uuid.uuid4())
    # Total trials = number of configs × trials per config
    total_trials = len(config.get_search_space().grid_configs()) * config.trials_per_config

    sweep = Sweep(
        id=sweep_id,
        user_id="",  # Will be set by create_sweep if needed
        name=config.name,
        description=config.description,
        config={
            "search_space": config.search_space,
            "command": config.command,
            "metrics": config.metrics,
            "objectives": [
                {
                    "metric": obj.metric,
                    "direction": obj.direction,
                    "weight": obj.weight
                }
                for obj in (config.objectives or [])
            ] if config.objectives else None,
            "constraints": [
                {
                    "metric": c.metric,
                    "min": c.min,
                    "max": c.max,
                    "equals": c.equals
                }
                for c in (config.constraints or [])
            ] if config.constraints else None,
            "max_trials": config.max_trials,
            "parallel": config.parallel,
            "timeout": config.timeout,
            "trials_per_config": config.trials_per_config,
        },
        status="running",
        total_trials=total_trials,
        completed_trials=0,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    # Create sweep in database
    try:
        db_sweep_id = await create_sweep(sweep)
        # Use the ID returned from the database
        sweep_id = db_sweep_id
        logger.info(f"Created sweep {sweep_id} in database: {config.name}")
    except Exception as e:
        # If database creation fails (e.g., no API server in tests), continue anyway
        logger.warning(f"Failed to create sweep in database: {e}. Continuing with local execution.")


    # Ensure progress file directory exists
    progress_file.parent.mkdir(parents=True, exist_ok=True)

    # Write initial status
    with open(progress_file, 'w') as f:
        f.write(json.dumps({
            "type": "sweep_started",
            "sweep_id": sweep_id,
            "name": config.name,
            "total_trials": sweep.total_trials
        }) + '\n')
        f.flush()

    # Define callback to write each trial result
    async def on_trial_complete(trial: Trial) -> None:
        """Write trial result to progress file and save to database."""
        try:
            # Save trial to database
            from wafer_core.tools.autotuner.storage import add_trial
            try:
                await add_trial(trial)
            except Exception as db_err:
                logger.warning(f"Failed to save trial to database: {db_err}")

            # Open in append mode and write trial as JSON line
            with open(progress_file, 'a') as f:
                f.write(json.dumps(trial.to_dict()) + '\n')
                f.flush()  # Ensure it's written immediately
        except Exception as e:
            logger.error(f"Failed to write trial result to progress file: {e}")

    try:
        # Update sweep status to running
        from wafer_core.tools.autotuner.storage import update_sweep_status
        try:
            await update_sweep_status(sweep_id, "running")
        except Exception as db_err:
            logger.warning(f"Failed to update sweep status to running: {db_err}")

        # Run the sweep with streaming callback
        await run_sweep(
            config=config,
            sweep_id=sweep_id,
            working_dir=working_dir,
            on_trial_complete=on_trial_complete
        )

        # Update sweep status to completed
        try:
            await update_sweep_status(sweep_id, "completed", sweep.total_trials)
        except Exception as db_err:
            logger.warning(f"Failed to update sweep status to completed: {db_err}")

        # Write completion marker
        with open(progress_file, 'a') as f:
            f.write(json.dumps({
                "type": "sweep_completed",
                "sweep_id": sweep_id
            }) + '\n')
            f.flush()

        logger.info(f"Sweep {sweep_id} completed successfully")

    except Exception as e:
        logger.error(f"Sweep {sweep_id} failed: {e}")

        # Write error marker
        with open(progress_file, 'a') as f:
            f.write(json.dumps({
                "type": "sweep_failed",
                "sweep_id": sweep_id,
                "error": str(e)
            }) + '\n')
            f.flush()

        raise

    return sweep_id


async def resume_sweep_streaming(
    sweep_id: str,
    working_dir: str | Path,
    progress_file: str | Path,
) -> str:
    """Resume a sweep and stream trial results to a file for extension to read.

    Args:
        sweep_id: ID of the sweep to resume
        working_dir: Directory to execute trials in
        progress_file: File path to write trial updates (one JSON per line)

    Returns:
        Sweep ID

    The progress file format is newline-delimited JSON, where each line is a trial result.
    This allows the extension to tail the file and get real-time updates as trials complete.
    """
    # Convert paths to Path objects if needed
    if isinstance(working_dir, str):
        working_dir = Path(working_dir)
    if isinstance(progress_file, str):
        progress_file = Path(progress_file)

    # Load sweep from database
    try:
        sweep = await get_sweep(sweep_id)
        logger.info(f"Resuming sweep {sweep_id}: {sweep.name}")
    except Exception as e:
        logger.error(f"Failed to load sweep {sweep_id}: {e}")
        raise

    # Ensure progress file directory exists
    progress_file.parent.mkdir(parents=True, exist_ok=True)

    # Write initial status
    with open(progress_file, 'w') as f:
        f.write(json.dumps({
            "type": "sweep_started",
            "sweep_id": sweep_id,
            "name": sweep.name,
            "total_trials": sweep.total_trials
        }) + '\n')
        f.flush()

    # Define callback to write each trial result
    async def on_trial_complete(trial: Trial) -> None:
        """Write trial result to progress file and save to database."""
        try:
            # Save trial to database
            from wafer_core.tools.autotuner.storage import add_trial
            try:
                await add_trial(trial)
            except Exception as db_err:
                logger.warning(f"Failed to save trial to database: {db_err}")

            # Open in append mode and write trial as JSON line
            with open(progress_file, 'a') as f:
                f.write(json.dumps(trial.to_dict()) + '\n')
                f.flush()  # Ensure it's written immediately
        except Exception as e:
            logger.error(f"Failed to write trial result to progress file: {e}")

    try:
        # Update sweep status to running
        from wafer_core.tools.autotuner.storage import update_sweep_status
        try:
            await update_sweep_status(sweep_id, "running")
        except Exception as db_err:
            logger.warning(f"Failed to update sweep status to running: {db_err}")

        # Resume the sweep with streaming callback
        await resume_sweep(
            sweep_id=sweep_id,
            working_dir=working_dir,
            on_trial_complete=on_trial_complete
        )

        # Update sweep status to completed
        try:
            await update_sweep_status(sweep_id, "completed", sweep.total_trials)
        except Exception as db_err:
            logger.warning(f"Failed to update sweep status to completed: {db_err}")

        # Write completion marker
        with open(progress_file, 'a') as f:
            f.write(json.dumps({
                "type": "sweep_completed",
                "sweep_id": sweep_id
            }) + '\n')
            f.flush()

        logger.info(f"Sweep {sweep_id} resumed and completed successfully")

    except Exception as e:
        logger.error(f"Sweep {sweep_id} failed during resume: {e}")

        # Write error marker
        with open(progress_file, 'a') as f:
            f.write(json.dumps({
                "type": "sweep_failed",
                "sweep_id": sweep_id,
                "error": str(e)
            }) + '\n')
            f.flush()

        raise

    return sweep_id
