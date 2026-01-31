"""Data types for autotuner."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Literal


class TrialStatus(str, Enum):
    """Status of a trial execution."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CONSTRAINT_VIOLATION = "constraint_violation"


@dataclass
class Constraint:
    """A constraint that trial results must satisfy.

    Examples:
        Constraint(metric="accuracy", min=0.95)
        Constraint(metric="correctness", equals="PASS")
        Constraint(metric="oom", equals=None)  # Must not be present
    """

    metric: str
    min: float | None = None
    max: float | None = None
    equals: Any | None = None

    def check(self, metrics: dict[str, Any]) -> bool:
        """Check if metrics satisfy this constraint."""
        if self.metric not in metrics:
            # If equals=None, metric must be absent (pass)
            # Otherwise, metric is required but missing (fail)
            return self.equals is None

        # Metric is present
        value = metrics[self.metric]

        # Check equals constraint (including equals=None case)
        if self.equals is not None:
            return value == self.equals
        elif self.min is None and self.max is None:
            # If only equals=None is set (no min/max), metric must be absent
            # But we're here, so metric is present - fail
            return False

        # Check min/max constraints (only for numeric values)
        if not isinstance(value, (int, float)):
            return True

        if self.min is not None and value < self.min:
            return False
        if self.max is not None and value > self.max:
            return False

        return True


@dataclass
class Objective:
    """An objective to optimize.

    Examples:
        Objective(metric="throughput", direction="maximize")
        Objective(metric="latency", direction="minimize", weight=2.0)
    """

    metric: str
    direction: Literal["maximize", "minimize"]
    weight: float = 1.0


@dataclass
class SearchSpace:
    """Defines the parameter space to search.

    Each parameter maps to a list of values to try (grid search).

    Example:
        SearchSpace(params={
            "tile_size": [16, 32, 64],
            "batch_size": [32, 64, 128]
        })
    """

    params: dict[str, list[Any]]

    def grid_configs(self) -> list[dict[str, Any]]:
        """Generate all configs via grid search (Cartesian product)."""
        from itertools import product

        if not self.params:
            return [{}]

        keys = list(self.params.keys())
        values = [self.params[k] for k in keys]

        configs = []
        for combo in product(*values):
            configs.append(dict(zip(keys, combo)))

        return configs


@dataclass
class Trial:
    """Result from evaluating a single config."""

    id: str
    sweep_id: str
    trial_number: int
    config: dict[str, Any]
    metrics: dict[str, Any]
    status: TrialStatus
    stdout: str
    stderr: str
    exit_code: int
    duration_ms: int
    started_at: datetime
    completed_at: datetime
    passed_constraints: bool = False
    is_pareto_optimal: bool | None = None  # Computed later

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Trial":
        """Deserialize from dict."""
        return cls(
            id=data["id"],
            sweep_id=data["sweep_id"],
            trial_number=data["trial_number"],
            config=data["config"],
            metrics=data["metrics"],
            status=TrialStatus(data["status"]),
            stdout=data["stdout"],
            stderr=data["stderr"],
            exit_code=data["exit_code"],
            duration_ms=data["duration_ms"],
            started_at=datetime.fromisoformat(data["started_at"]),
            completed_at=datetime.fromisoformat(data["completed_at"]),
            passed_constraints=data.get("passed_constraints", False),
            is_pareto_optimal=data.get("is_pareto_optimal"),
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict for storage."""
        return {
            "id": self.id,
            "sweep_id": self.sweep_id,
            "trial_number": self.trial_number,
            "config": self.config,
            "metrics": self.metrics,
            "status": self.status.value,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "exit_code": self.exit_code,
            "duration_ms": self.duration_ms,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat(),
            "passed_constraints": self.passed_constraints,
            "is_pareto_optimal": self.is_pareto_optimal,
        }


@dataclass
class MetricStats:
    """Statistics for a metric across multiple trials."""

    mean: float
    std: float
    min: float
    max: float
    values: list[float]


@dataclass
class AggregatedConfig:
    """Aggregated results for a configuration run multiple times.

    When trials_per_config > 1, this represents the aggregated statistics
    for all trials of the same parameter configuration.
    """

    config_number: int
    config: dict[str, Any]
    trials: list[Trial]
    metrics: dict[str, MetricStats]  # metric_name -> stats
    all_passed_constraints: bool
    is_pareto_optimal: bool = False


@dataclass
class AutotunerConfig:
    """Configuration for a hyperparameter sweep.

    This is loaded from the user's JSON config file.
    """

    name: str
    search_space: dict[str, list[Any]]
    command: str
    metrics: dict[str, str]  # metric_name -> regex pattern
    objectives: list[Objective] | None = None  # Optional - provides default ranking
    constraints: list[Constraint] | None = None
    max_trials: int | None = None
    parallel: int = 1
    timeout: int = 300
    trials_per_config: int = 1  # Run each config multiple times for statistical stability
    description: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AutotunerConfig":
        """Create AutotunerConfig from a dictionary.

        Args:
            data: Dictionary containing config fields

        Returns:
            AutotunerConfig instance
        """
        # Validate required fields and provide helpful error messages
        required_fields = ["name", "search_space", "command", "metrics"]
        missing_fields = [field for field in required_fields if field not in data]

        if missing_fields:
            raise ValueError(
                f"Config dict is missing required field(s): {', '.join(missing_fields)}\n"
                f"Required fields: {', '.join(required_fields)}\n"
                f"Optional fields: objectives, constraints, max_trials, parallel, timeout, description"
            )

        # Parse objectives from dicts to Objective dataclasses (optional)
        objectives = None
        if data.get("objectives"):
            objectives = [
                Objective(
                    metric=obj["metric"],
                    direction=obj["direction"],
                    weight=obj.get("weight", 1.0),
                )
                for obj in data["objectives"]
            ]

        # Parse constraints from dicts to Constraint dataclasses
        constraints = None
        if data.get("constraints"):
            constraints = [
                Constraint(
                    metric=c["metric"],
                    min=c.get("min"),
                    max=c.get("max"),
                    equals=c.get("equals"),
                )
                for c in data["constraints"]
            ]

        return cls(
            name=data["name"],
            search_space=data["search_space"],
            command=data["command"],
            metrics=data["metrics"],
            objectives=objectives,
            constraints=constraints,
            max_trials=data.get("max_trials"),
            parallel=data.get("parallel", 1),
            timeout=data.get("timeout", 300),
            trials_per_config=data.get("trials_per_config", 1),
            description=data.get("description"),
        )

    @classmethod
    def from_json(cls, path: Path) -> "AutotunerConfig":
        """Load config from JSON file."""
        import json

        with open(path) as f:
            data = json.load(f)

        return cls.from_dict(data)

    def get_search_space(self) -> SearchSpace:
        """Get search space object."""
        return SearchSpace(params=self.search_space)


@dataclass
class Sweep:
    """A collection of trials for one hyperparameter search.

    This is the top-level entity stored in the database.
    """

    id: str
    user_id: str
    name: str
    description: str | None
    config: dict[str, Any]  # The original AutotunerConfig as dict
    status: Literal["pending", "running", "completed", "failed"]
    total_trials: int
    completed_trials: int
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize for database storage."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "description": self.description,
            "config": self.config,
            "status": self.status,
            "total_trials": self.total_trials,
            "completed_trials": self.completed_trials,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Sweep":
        """Deserialize from database."""
        return cls(
            id=data["id"],
            user_id=data["user_id"],
            name=data["name"],
            description=data.get("description"),
            config=data["config"],
            status=data["status"],
            total_trials=data["total_trials"],
            completed_trials=data["completed_trials"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            completed_at=datetime.fromisoformat(data["completed_at"])
            if data.get("completed_at")
            else None,
        )
