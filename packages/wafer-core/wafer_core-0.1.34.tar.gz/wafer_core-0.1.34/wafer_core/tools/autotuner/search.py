"""Search strategies for generating trial configurations."""

from typing import Any

from wafer_core.tools.autotuner.dtypes import SearchSpace


def generate_grid_trials(search_space: SearchSpace, max_trials: int | None = None) -> list[dict[str, Any]]:
    """Generate trial configs via grid search (Cartesian product).

    Args:
        search_space: Parameter space definition
        max_trials: Optional limit on number of trials

    Returns:
        List of trial configurations (dicts of param -> value)
    """
    configs = search_space.grid_configs()

    if max_trials is not None and len(configs) > max_trials:
        configs = configs[:max_trials]

    return configs
