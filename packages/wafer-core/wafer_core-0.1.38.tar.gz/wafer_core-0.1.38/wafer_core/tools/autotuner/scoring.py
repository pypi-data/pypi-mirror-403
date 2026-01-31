"""Scoring and Pareto frontier computation."""

import logging
from typing import Any

from wafer_core.tools.autotuner.dtypes import AggregatedConfig, Objective, Trial

logger = logging.getLogger(__name__)


def dominates(trial_a: Trial, trial_b: Trial, objectives: list[Objective]) -> bool:
    """Check if trial_a dominates trial_b.

    Trial A dominates Trial B if:
    - A is better or equal in all objectives
    - A is strictly better in at least one objective

    Args:
        trial_a: First trial
        trial_b: Second trial
        objectives: List of objectives to compare

    Returns:
        True if trial_a dominates trial_b
    """
    better_in_any = False
    worse_in_any = False

    for obj in objectives:
        metric = obj.metric

        # Skip if either trial doesn't have this metric
        if metric not in trial_a.metrics or metric not in trial_b.metrics:
            continue

        value_a = trial_a.metrics[metric]
        value_b = trial_b.metrics[metric]

        # Compare based on direction
        if obj.direction == "maximize":
            if value_a > value_b:
                better_in_any = True
            elif value_a < value_b:
                worse_in_any = True
        else:  # minimize
            if value_a < value_b:
                better_in_any = True
            elif value_a > value_b:
                worse_in_any = True

    # A dominates B if better in at least one and not worse in any
    return better_in_any and not worse_in_any


def compute_pareto_frontier(trials: list[Trial], objectives: list[Objective]) -> list[Trial]:
    """Compute the Pareto frontier from a list of trials.

    The Pareto frontier contains all non-dominated trials.

    Args:
        trials: List of trials to analyze
        objectives: List of objectives

    Returns:
        List of Pareto-optimal trials
    """
    # Only consider trials that passed constraints
    valid_trials = [t for t in trials if t.passed_constraints]

    if not valid_trials:
        logger.warning("No trials passed constraints")
        return []

    # Find non-dominated trials
    pareto_trials = []

    for trial in valid_trials:
        is_dominated = False

        for other in valid_trials:
            if trial.id == other.id:
                continue

            if dominates(other, trial, objectives):
                is_dominated = True
                break

        if not is_dominated:
            pareto_trials.append(trial)

    logger.info(f"Found {len(pareto_trials)} Pareto-optimal trials out of {len(valid_trials)} valid trials")

    return pareto_trials


def rank_trials_single_objective(
    trials: list[Trial],
    objective: Objective,
) -> list[Trial]:
    """Rank trials by a single objective.

    Args:
        trials: List of trials
        objective: Objective to optimize

    Returns:
        Trials sorted by objective (best first)
    """
    # Only consider trials that passed constraints
    valid_trials = [t for t in trials if t.passed_constraints]

    if not valid_trials:
        return []

    # Filter trials that have the metric
    trials_with_metric = [
        t for t in valid_trials if objective.metric in t.metrics
    ]

    if not trials_with_metric:
        logger.warning(f"No trials have metric '{objective.metric}'")
        return []

    # Sort by metric
    reverse = objective.direction == "maximize"
    sorted_trials = sorted(
        trials_with_metric,
        key=lambda t: t.metrics[objective.metric],
        reverse=reverse,
    )

    return sorted_trials


def rank_pareto_trials(
    pareto_trials: list[Trial],
    objectives: list[Objective],
) -> list[Trial]:
    """Rank Pareto-optimal trials by weighted score.

    Uses weights to compute a normalized weighted score for each trial.
    Higher weights mean the objective is more important.

    Normalization: For each objective, normalize values to [0, 1] across all trials,
    then compute weighted sum: score = w1*norm(obj1) + w2*norm(obj2) + ...

    Args:
        pareto_trials: List of Pareto-optimal trials
        objectives: List of objectives with weights

    Returns:
        Trials sorted by weighted score (best first)
    """
    if not pareto_trials:
        return []

    # If only one trial, no need to rank
    if len(pareto_trials) == 1:
        return pareto_trials

    # Collect all metric values for normalization
    metric_ranges: dict[str, tuple[float, float]] = {}  # metric -> (min, max)

    for obj in objectives:
        metric = obj.metric
        values = [
            t.metrics[metric]
            for t in pareto_trials
            if metric in t.metrics and isinstance(t.metrics[metric], (int, float))
        ]

        if not values:
            continue

        metric_ranges[metric] = (min(values), max(values))

    # Compute weighted score for each trial
    def compute_score(trial: Trial) -> float:
        score = 0.0
        total_weight = 0.0

        for obj in objectives:
            metric = obj.metric

            # Skip if metric not present or not normalized
            if metric not in trial.metrics or metric not in metric_ranges:
                continue

            value = trial.metrics[metric]
            if not isinstance(value, (int, float)):
                continue

            min_val, max_val = metric_ranges[metric]

            # Normalize to [0, 1]
            if max_val == min_val:
                # All values are the same, normalized value is 0.5
                normalized = 0.5
            else:
                normalized = (value - min_val) / (max_val - min_val)

            # For minimize objectives, invert the normalized value
            # (lower is better → higher normalized score)
            if obj.direction == "minimize":
                normalized = 1.0 - normalized

            score += obj.weight * normalized
            total_weight += obj.weight

        # Return average weighted score (normalized by total weight)
        return score / total_weight if total_weight > 0 else 0.0

    # Sort by weighted score (higher is better)
    ranked = sorted(pareto_trials, key=compute_score, reverse=True)

    return ranked


def get_best_trials(trials: list[Trial], objectives: list[Objective] | None) -> list[Trial]:
    """Get the best trial(s) based on objectives.

    If no objectives provided: returns all trials that passed constraints (no ranking)
    If single objective: returns top trial
    If multi-objective: returns Pareto frontier ranked by weights

    Args:
        trials: List of trials
        objectives: List of objectives (optional)

    Returns:
        Best trial(s) - all valid trials if no objectives, singleton list for single objective,
        ranked Pareto frontier for multi-objective
    """
    if not objectives:
        # No objectives - return all valid trials without ranking
        return [t for t in trials if t.passed_constraints]

    if len(objectives) == 1:
        # Single objective - return best trial
        ranked = rank_trials_single_objective(trials, objectives[0])
        return [ranked[0]] if ranked else []
    else:
        # Multi-objective - return Pareto frontier ranked by weights
        pareto_trials = compute_pareto_frontier(trials, objectives)
        return rank_pareto_trials(pareto_trials, objectives)


# ============================================================================
# Aggregated Config Scoring (for trials_per_config > 1)
# ============================================================================


def dominates_config(
    config_a: AggregatedConfig, config_b: AggregatedConfig, objectives: list[Objective]
) -> bool:
    """Check if config_a dominates config_b (using mean values).

    Args:
        config_a: First config
        config_b: Second config
        objectives: List of objectives to compare

    Returns:
        True if config_a dominates config_b
    """
    better_in_any = False
    worse_in_any = False

    for obj in objectives:
        metric = obj.metric

        # Skip if either config doesn't have this metric
        if metric not in config_a.metrics or metric not in config_b.metrics:
            continue

        value_a = config_a.metrics[metric].mean
        value_b = config_b.metrics[metric].mean

        # Compare based on direction
        if obj.direction == "maximize":
            if value_a > value_b:
                better_in_any = True
            elif value_a < value_b:
                worse_in_any = True
        else:  # minimize
            if value_a < value_b:
                better_in_any = True
            elif value_a > value_b:
                worse_in_any = True

    # A dominates B if better in at least one and not worse in any
    return better_in_any and not worse_in_any


def compute_pareto_frontier_configs(
    configs: list[AggregatedConfig], objectives: list[Objective]
) -> list[AggregatedConfig]:
    """Compute the Pareto frontier from aggregated configs.

    Args:
        configs: List of aggregated configs
        objectives: List of objectives

    Returns:
        List of Pareto-optimal configs
    """
    # Only consider configs where all trials passed constraints
    valid_configs = [c for c in configs if c.all_passed_constraints]

    if not valid_configs:
        logger.warning("No configs passed constraints")
        return []

    # Find non-dominated configs
    pareto_configs = []

    for config in valid_configs:
        is_dominated = False

        for other in valid_configs:
            if config.config_number == other.config_number:
                continue

            if dominates_config(other, config, objectives):
                is_dominated = True
                break

        if not is_dominated:
            pareto_configs.append(config)

    logger.info(
        f"Found {len(pareto_configs)} Pareto-optimal configs out of {len(valid_configs)} valid configs"
    )

    return pareto_configs


def rank_configs_single_objective(
    configs: list[AggregatedConfig], objective: Objective
) -> list[AggregatedConfig]:
    """Rank configs by a single objective (using mean values).

    Args:
        configs: List of aggregated configs
        objective: Objective to optimize

    Returns:
        Configs sorted by objective (best first)
    """
    # Only consider configs where all trials passed constraints
    valid_configs = [c for c in configs if c.all_passed_constraints]

    if not valid_configs:
        return []

    # Filter configs that have the metric
    configs_with_metric = [c for c in valid_configs if objective.metric in c.metrics]

    if not configs_with_metric:
        logger.warning(f"No configs have metric '{objective.metric}'")
        return []

    # Sort by mean metric value
    reverse = objective.direction == "maximize"
    sorted_configs = sorted(
        configs_with_metric,
        key=lambda c: c.metrics[objective.metric].mean,
        reverse=reverse,
    )

    return sorted_configs


def rank_pareto_configs(
    pareto_configs: list[AggregatedConfig], objectives: list[Objective]
) -> list[AggregatedConfig]:
    """Rank Pareto-optimal configs by weighted score (using mean values).

    Args:
        pareto_configs: List of Pareto-optimal configs
        objectives: List of objectives with weights

    Returns:
        Configs sorted by weighted score (best first)
    """
    if not pareto_configs:
        return []

    if len(pareto_configs) == 1:
        return pareto_configs

    # Collect all metric values for normalization
    metric_ranges: dict[str, tuple[float, float]] = {}

    for obj in objectives:
        metric = obj.metric
        values = [
            c.metrics[metric].mean
            for c in pareto_configs
            if metric in c.metrics
        ]

        if not values:
            continue

        metric_ranges[metric] = (min(values), max(values))

    # Compute weighted score for each config
    def compute_score(config: AggregatedConfig) -> float:
        score = 0.0
        total_weight = 0.0

        for obj in objectives:
            metric = obj.metric

            if metric not in config.metrics or metric not in metric_ranges:
                continue

            value = config.metrics[metric].mean
            min_val, max_val = metric_ranges[metric]

            # Normalize to [0, 1]
            if max_val == min_val:
                normalized = 0.5
            else:
                normalized = (value - min_val) / (max_val - min_val)

            # For minimize objectives, invert
            if obj.direction == "minimize":
                normalized = 1.0 - normalized

            score += obj.weight * normalized
            total_weight += obj.weight

        return score / total_weight if total_weight > 0 else 0.0

    # Sort by weighted score (higher is better)
    ranked = sorted(pareto_configs, key=compute_score, reverse=True)

    return ranked


def get_best_configs(
    configs: list[AggregatedConfig], objectives: list[Objective] | None
) -> list[AggregatedConfig]:
    """Get the best config(s) based on objectives.

    Args:
        configs: List of aggregated configs
        objectives: List of objectives (optional)

    Returns:
        Best config(s)
    """
    if not objectives:
        return [c for c in configs if c.all_passed_constraints]

    if len(objectives) == 1:
        ranked = rank_configs_single_objective(configs, objectives[0])
        return [ranked[0]] if ranked else []
    else:
        pareto_configs = compute_pareto_frontier_configs(configs, objectives)
        return rank_pareto_configs(pareto_configs, objectives)
