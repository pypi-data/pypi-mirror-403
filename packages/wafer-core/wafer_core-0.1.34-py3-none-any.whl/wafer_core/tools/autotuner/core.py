"""Core sweep execution logic."""

import logging
import re
import time
import uuid
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import trio

from wafer_core.tools.autotuner.dtypes import (
    AutotunerConfig,
    Constraint,
    Objective,
    Sweep,
    Trial,
    TrialStatus,
)
from wafer_core.tools.autotuner.metrics import extract_metrics_from_output
from wafer_core.tools.autotuner.search import generate_grid_trials
from wafer_core.tools.autotuner.storage import get_sweep, get_trials

logger = logging.getLogger(__name__)


async def run_trial(
    config: dict[str, Any],
    sweep_id: str,
    trial_number: int,
    command_template: str,
    metrics_patterns: dict[str, str],
    constraints: list[Constraint],
    working_dir: Path,
    timeout: int = 300,
) -> Trial:
    """Execute a single trial.

    Args:
        config: Parameter configuration to test
        sweep_id: ID of the parent sweep
        trial_number: Sequential trial number
        command_template: Command with {param} placeholders
        metrics_patterns: Dict of metric_name -> regex pattern
        constraints: List of constraints to check
        working_dir: Directory to execute command in
        timeout: Timeout in seconds

    Returns:
        Trial result with metrics and status
    """
    trial_id = str(uuid.uuid4())
    start_time = time.time()
    started_at = datetime.now(timezone.utc)

    try:
        # Substitute params into command template
        command = command_template.format(**config)

        # Execute command with timeout
        with trio.fail_after(timeout):
            result = await trio.run_process(
                command,
                shell=True,
                cwd=str(working_dir),
                capture_stdout=True,
                capture_stderr=True,
                check=False,
            )

        completed_at = datetime.now(timezone.utc)
        duration_ms = int((time.time() - start_time) * 1000)
        stdout = result.stdout.decode("utf-8", errors="replace")
        stderr = result.stderr.decode("utf-8", errors="replace")
        exit_code = result.returncode

        # Extract metrics using new extraction logic (supports "auto" and regex)
        metrics = extract_metrics_from_output(stdout, metrics_patterns)

        # Check constraints
        passed_constraints = all(c.check(metrics) for c in constraints)

        # Determine status
        if exit_code != 0:
            status = TrialStatus.FAILED
        elif not passed_constraints:
            status = TrialStatus.CONSTRAINT_VIOLATION
        else:
            status = TrialStatus.SUCCESS

        return Trial(
            id=trial_id,
            sweep_id=sweep_id,
            trial_number=trial_number,
            config=config,
            metrics=metrics,
            status=status,
            stdout=stdout,
            stderr=stderr,
            exit_code=exit_code,
            duration_ms=duration_ms,
            started_at=started_at,
            completed_at=completed_at,
            passed_constraints=passed_constraints,
        )

    except trio.TooSlowError:
        completed_at = datetime.now(timezone.utc)
        duration_ms = int((time.time() - start_time) * 1000)
        return Trial(
            id=trial_id,
            sweep_id=sweep_id,
            trial_number=trial_number,
            config=config,
            metrics={},
            status=TrialStatus.TIMEOUT,
            stdout="",
            stderr=f"Command timed out after {timeout} seconds",
            exit_code=-1,
            duration_ms=duration_ms,
            started_at=started_at,
            completed_at=completed_at,
            passed_constraints=False,
        )

    except trio.Cancelled:
        # Handle cancellation (also timeout-related)
        completed_at = datetime.now(timezone.utc)
        duration_ms = int((time.time() - start_time) * 1000)
        return Trial(
            id=trial_id,
            sweep_id=sweep_id,
            trial_number=trial_number,
            config=config,
            metrics={},
            status=TrialStatus.TIMEOUT,
            stdout="",
            stderr=f"Command timed out after {timeout} seconds",
            exit_code=-1,
            duration_ms=duration_ms,
            started_at=started_at,
            completed_at=completed_at,
            passed_constraints=False,
        )

    except Exception as e:
        completed_at = datetime.now(timezone.utc)
        duration_ms = int((time.time() - start_time) * 1000)
        return Trial(
            id=trial_id,
            sweep_id=sweep_id,
            trial_number=trial_number,
            config=config,
            metrics={},
            status=TrialStatus.FAILED,
            stdout="",
            stderr=f"Execution error: {str(e)}",
            exit_code=-1,
            duration_ms=duration_ms,
            started_at=started_at,
            completed_at=completed_at,
            passed_constraints=False,
        )


async def run_sweep(
    config: AutotunerConfig,
    sweep_id: str,
    working_dir: Path,
    on_trial_complete: Callable[[Trial], None] | None = None,
    existing_trials: list[Trial] | None = None,
) -> list[Trial]:
    """Run a hyperparameter sweep.

    Args:
        config: Sweep configuration
        sweep_id: ID of the sweep
        working_dir: Directory to execute trials in
        on_trial_complete: Optional callback called after each trial completes
        existing_trials: Optional list of already-completed trials (for resume)

    Returns:
        List of all trial results (including existing ones)
    """
    # Generate trial configs
    search_space = config.get_search_space()
    base_configs = generate_grid_trials(search_space, config.max_trials)

    # Expand each config into multiple runs if trials_per_config > 1
    # Each run gets a unique trial_number: config_idx * trials_per_config + run_idx
    trial_configs = []
    for config_idx, cfg in enumerate(base_configs):
        for run_idx in range(config.trials_per_config):
            trial_num = config_idx * config.trials_per_config + run_idx
            trial_configs.append((trial_num, cfg, run_idx))

    logger.info(
        f"Generated {len(trial_configs)} total trials "
        f"({len(base_configs)} configs × {config.trials_per_config} runs each)"
    )

    # Build list of (trial_num, config, run_idx) tuples to maintain grid position
    # Filter out already-completed trials if resuming
    if existing_trials:
        # For trials_per_config > 1, we need all trials for a config to succeed
        # If any trial for a config failed, we re-run ALL trials for that config
        # This ensures consistent sample sizes and handles environmental issues

        # Group existing trials by config_idx
        config_status = {}  # config_idx -> all_trials_successful
        for trial in existing_trials:
            # Calculate which config this trial belongs to
            config_idx = trial.trial_number // config.trials_per_config
            if config_idx not in config_status:
                config_status[config_idx] = {'total': 0, 'success': 0}
            config_status[config_idx]['total'] += 1
            if trial.status == TrialStatus.SUCCESS:
                config_status[config_idx]['success'] += 1

        # A config is complete only if ALL its trials succeeded
        completed_configs = {
            config_idx
            for config_idx, status in config_status.items()
            if status['success'] == config.trials_per_config and status['total'] == config.trials_per_config
        }

        # Build list of (trial_num, config, run_idx) for trials to run
        # Skip entire configs that are fully complete
        configs_to_run = [
            (trial_num, cfg, run_idx)
            for trial_num, cfg, run_idx in trial_configs
            if (trial_num // config.trials_per_config) not in completed_configs
        ]

        skipped_count = len(trial_configs) - len(configs_to_run)
        if skipped_count > 0:
            logger.info(
                f"Resuming sweep '{config.name}': skipping {len(completed_configs)} fully completed configs "
                f"({skipped_count} trials), running {len(configs_to_run)} remaining trials"
            )
    else:
        # New sweep: all configs with their trial numbers
        configs_to_run = trial_configs

    logger.info(f"Starting sweep '{config.name}' with {len(configs_to_run)} trials")

    # Get constraints (use empty list if None)
    constraints = config.constraints or []

    # Run trials with parallelism limit
    results: list[Trial] = []
    semaphore = trio.Semaphore(config.parallel)

    async def run_one_trial(trial_config: dict[str, Any], trial_num: int) -> Trial:
        async with semaphore:
            trial = await run_trial(
                config=trial_config,
                sweep_id=sweep_id,
                trial_number=trial_num,
                command_template=config.command,
                metrics_patterns=config.metrics,
                constraints=constraints,
                working_dir=working_dir,
                timeout=config.timeout,
            )

            # Call callback if provided (support both sync and async)
            if on_trial_complete:
                import inspect
                if inspect.iscoroutinefunction(on_trial_complete):
                    await on_trial_complete(trial)
                else:
                    await trio.to_thread.run_sync(lambda: on_trial_complete(trial))

            return trial

    # Run all trials in parallel (limited by semaphore)
    async def run_and_collect(trial_config: dict[str, Any], trial_num: int) -> None:
        trial = await run_one_trial(trial_config, trial_num)
        results.append(trial)

    async with trio.open_nursery() as nursery:
        for trial_num, trial_config, run_idx in configs_to_run:
            # Each trial has a unique trial_number
            nursery.start_soon(run_and_collect, trial_config, trial_num)

    # Combine new results with existing trials if resuming
    all_results = (existing_trials or []) + results

    logger.info(
        f"Sweep '{config.name}' completed: {len(results)} new trials, "
        f"{len(all_results)} total trials"
    )

    return all_results


async def resume_sweep(
    sweep_id: str,
    working_dir: Path,
    on_trial_complete: Callable[[Trial], None] | None = None,
) -> list[Trial]:
    """Resume a previously started sweep that crashed or was interrupted.

    This function loads the sweep configuration and existing trials from the database,
    filters out already-completed configs, and runs only the remaining trials.

    Args:
        sweep_id: ID of the sweep to resume
        working_dir: Directory to execute trials in
        on_trial_complete: Optional callback called after each trial completes

    Returns:
        List of all trial results (both existing and newly executed)

    Raises:
        httpx.HTTPError: If sweep cannot be loaded from database
    """
    logger.info(f"Resuming sweep {sweep_id}")

    # Load sweep metadata from database
    sweep = await get_sweep(sweep_id)

    # Reconstruct AutotunerConfig from stored config dict
    # Parse objectives from dicts to Objective dataclasses (optional)
    objectives = None
    if sweep.config.get("objectives"):
        objectives = [
            Objective(
                metric=obj["metric"],
                direction=obj["direction"],
                weight=obj.get("weight", 1.0),
            )
            for obj in sweep.config["objectives"]
        ]

    # Parse constraints from dicts to Constraint dataclasses
    constraints = None
    if sweep.config.get("constraints"):
        constraints = [
            Constraint(
                metric=c["metric"],
                min=c.get("min"),
                max=c.get("max"),
                equals=c.get("equals"),
            )
            for c in sweep.config["constraints"]
        ]

    config = AutotunerConfig(
        name=sweep.name,
        search_space=sweep.config["search_space"],
        command=sweep.config["command"],
        metrics=sweep.config["metrics"],
        objectives=objectives,
        constraints=constraints,
        max_trials=sweep.config.get("max_trials"),
        parallel=sweep.config.get("parallel", 1),
        timeout=sweep.config.get("timeout", 300),
        trials_per_config=sweep.config.get("trials_per_config", 1),
        description=sweep.description,
    )

    # Load existing trials
    existing_trials = await get_trials(sweep_id)

    logger.info(
        f"Found {len(existing_trials)} existing trials for sweep '{sweep.name}'"
    )

    # Run sweep with existing trials (run_sweep will filter out completed ones)
    return await run_sweep(
        config=config,
        sweep_id=sweep_id,
        working_dir=working_dir,
        on_trial_complete=on_trial_complete,
        existing_trials=existing_trials,
    )
