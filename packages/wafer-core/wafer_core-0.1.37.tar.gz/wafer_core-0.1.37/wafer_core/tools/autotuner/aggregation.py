"""Utilities for aggregating trials by configuration."""

import math
from collections import defaultdict

from wafer_core.tools.autotuner.dtypes import AggregatedConfig, MetricStats, Trial, TrialStatus


def aggregate_trials_by_config(
    trials: list[Trial], trials_per_config: int
) -> list[AggregatedConfig]:
    """Group trials by configuration and compute aggregated statistics.

    Args:
        trials: List of all trials
        trials_per_config: Number of trials per configuration

    Returns:
        List of aggregated configurations with statistics
    """
    if trials_per_config == 1:
        # No aggregation needed - return empty list
        # Caller should use trials directly
        return []

    # Group trials by config_number
    config_groups: dict[int, list[Trial]] = defaultdict(list)
    for trial in trials:
        config_number = trial.trial_number // trials_per_config
        config_groups[config_number].append(trial)

    # Compute aggregated statistics for each config
    aggregated_configs: list[AggregatedConfig] = []

    for config_number, config_trials in sorted(config_groups.items()):
        # Only include successful trials in aggregation
        successful_trials = [
            t for t in config_trials if t.status == TrialStatus.SUCCESS
        ]

        if not successful_trials:
            # Skip configs with no successful trials
            continue

        # Use config from first trial (should be same for all trials in group)
        config = successful_trials[0].config

        # Collect all metric names
        all_metrics = set()
        for trial in successful_trials:
            all_metrics.update(trial.metrics.keys())

        # Aggregate metrics
        aggregated_metrics: dict[str, MetricStats] = {}

        for metric in all_metrics:
            # Get all values for this metric
            values = [
                trial.metrics[metric]
                for trial in successful_trials
                if metric in trial.metrics and isinstance(trial.metrics[metric], (int, float))
            ]

            if values:
                # Compute statistics
                mean = sum(values) / len(values)
                variance = sum((v - mean) ** 2 for v in values) / len(values)
                std = math.sqrt(variance)
                min_val = min(values)
                max_val = max(values)

                aggregated_metrics[metric] = MetricStats(
                    mean=mean, std=std, min=min_val, max=max_val, values=values
                )

        # Check if all trials passed constraints
        all_passed = all(t.passed_constraints for t in successful_trials)

        # Check if any trial is pareto optimal
        is_pareto = any(t.is_pareto_optimal for t in successful_trials)

        aggregated_configs.append(
            AggregatedConfig(
                config_number=config_number,
                config=config,
                trials=config_trials,
                metrics=aggregated_metrics,
                all_passed_constraints=all_passed,
                is_pareto_optimal=is_pareto,
            )
        )

    return sorted(aggregated_configs, key=lambda c: c.config_number)
