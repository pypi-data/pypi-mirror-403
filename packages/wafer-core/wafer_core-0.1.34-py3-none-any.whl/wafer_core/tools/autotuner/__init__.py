"""Autotuner tool - Hyperparameter search for performance engineering.

The autotuner package exports core types and functions for running parameter sweeps.
"""

from wafer_core.tools.autotuner.aggregation import aggregate_trials_by_config
from wafer_core.tools.autotuner.core import resume_sweep, run_sweep
from wafer_core.tools.autotuner.dtypes import (
    AggregatedConfig,
    AutotunerConfig,
    Constraint,
    MetricStats,
    Objective,
    SearchSpace,
    Sweep,
    Trial,
    TrialStatus,
)
from wafer_core.tools.autotuner.scoring import (
    compute_pareto_frontier,
    compute_pareto_frontier_configs,
    get_best_configs,
    get_best_trials,
    rank_configs_single_objective,
    rank_pareto_configs,
    rank_pareto_trials,
)
from wafer_core.tools.autotuner.storage import update_sweep_status
from wafer_core.tools.autotuner.streaming import (
    resume_sweep_streaming,
    run_sweep_streaming,
)

__all__ = [
    "AggregatedConfig",
    "AutotunerConfig",
    "Constraint",
    "MetricStats",
    "Objective",
    "SearchSpace",
    "Sweep",
    "Trial",
    "TrialStatus",
    "aggregate_trials_by_config",
    "compute_pareto_frontier",
    "compute_pareto_frontier_configs",
    "get_best_configs",
    "get_best_trials",
    "rank_configs_single_objective",
    "rank_pareto_configs",
    "rank_pareto_trials",
    "resume_sweep",
    "resume_sweep_streaming",
    "run_sweep",
    "run_sweep_streaming",
    "update_sweep_status",
]
