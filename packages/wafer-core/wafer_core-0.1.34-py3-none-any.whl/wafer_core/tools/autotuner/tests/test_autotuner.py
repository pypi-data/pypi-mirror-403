"""Tests for autotuner core logic.

Only tests the functions we implemented:
- search.py: Grid search generation
- scoring.py: Pareto frontier, ranking, constraints
- core.py: Trial execution
- dtypes.py: Data structures
"""

import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest
import trio

from wafer_core.tools.autotuner.core import run_sweep, run_trial
from wafer_core.tools.autotuner.dtypes import (
    AutotunerConfig,
    Constraint,
    Objective,
    SearchSpace,
    Trial,
    TrialStatus,
)
from wafer_core.tools.autotuner.scoring import (
    compute_pareto_frontier,
    dominates,
    get_best_trials,
    rank_pareto_trials,
    rank_trials_single_objective,
)
from wafer_core.tools.autotuner.search import generate_grid_trials

# ── Unit Tests ──────────────────────────────────────────────────────────────


def test_search_space_grid_configs():
    """Test grid search generates Cartesian product."""
    space = SearchSpace(params={
        "tile_size": [16, 32],
        "batch_size": [64, 128],
    })

    configs = space.grid_configs()

    assert len(configs) == 4  # 2 × 2
    assert {"tile_size": 16, "batch_size": 64} in configs
    assert {"tile_size": 16, "batch_size": 128} in configs
    assert {"tile_size": 32, "batch_size": 64} in configs
    assert {"tile_size": 32, "batch_size": 128} in configs


def test_generate_grid_trials_respects_max():
    """Test max_trials limits number of configs."""
    space = SearchSpace(params={
        "a": [1, 2, 3],
        "b": [1, 2, 3],
    })

    configs = generate_grid_trials(space, max_trials=5)

    assert len(configs) == 5  # Should stop at 5, not generate all 9


def test_constraint_checking():
    """Test constraint validation logic."""
    # Min constraint
    c1 = Constraint(metric="accuracy", min=0.9)
    assert c1.check({"accuracy": 0.95})
    assert not c1.check({"accuracy": 0.85})

    # Max constraint
    c2 = Constraint(metric="latency", max=100)
    assert c2.check({"latency": 50})
    assert not c2.check({"latency": 150})

    # Equals constraint
    c3 = Constraint(metric="correctness", equals="PASS")
    assert c3.check({"correctness": "PASS"})
    assert not c3.check({"correctness": "FAIL"})

    # Metric must be absent (equals=None)
    c4 = Constraint(metric="oom", equals=None)
    assert c4.check({})  # No OOM = pass
    assert not c4.check({"oom": True})  # OOM present = fail


def test_single_objective_ranking():
    """Test ranking trials by single objective."""
    trials = [
        Trial(
            id="1", sweep_id="sweep", config={"x": 1}, metrics={"throughput": 100},
            status=TrialStatus.SUCCESS, trial_number=0, stdout="", stderr="", exit_code=0, duration_ms=1000, started_at=datetime.now(timezone.utc), completed_at=datetime.now(timezone.utc), passed_constraints=True,
        ),
        Trial(
            id="2", sweep_id="sweep", config={"x": 2}, metrics={"throughput": 200},
            status=TrialStatus.SUCCESS, trial_number=0, stdout="", stderr="", exit_code=0, duration_ms=1000, started_at=datetime.now(timezone.utc), completed_at=datetime.now(timezone.utc), passed_constraints=True,
        ),
        Trial(
            id="3", sweep_id="sweep", config={"x": 3}, metrics={"throughput": 150},
            status=TrialStatus.SUCCESS, trial_number=0, stdout="", stderr="", exit_code=0, duration_ms=1000, started_at=datetime.now(timezone.utc), completed_at=datetime.now(timezone.utc), passed_constraints=True,
        ),
    ]

    obj_max = Objective(metric="throughput", direction="maximize")
    ranked = rank_trials_single_objective(trials, obj_max)

    assert len(ranked) == 3
    assert ranked[0].id == "2"  # Highest throughput
    assert ranked[1].id == "3"
    assert ranked[2].id == "1"

    obj_min = Objective(metric="throughput", direction="minimize")
    ranked_min = rank_trials_single_objective(trials, obj_min)

    assert ranked_min[0].id == "1"  # Lowest throughput


def test_dominates():
    """Test Pareto dominance checking."""
    obj1 = Objective(metric="throughput", direction="maximize")
    obj2 = Objective(metric="latency", direction="minimize")
    objectives = [obj1, obj2]

    # Trial A: high throughput, low latency (ideal)
    trial_a = Trial(
        id="a", sweep_id="sweep", config={}, metrics={"throughput": 200, "latency": 50},
        status=TrialStatus.SUCCESS, trial_number=0, stdout="", stderr="", exit_code=0, duration_ms=1000, started_at=datetime.now(timezone.utc), completed_at=datetime.now(timezone.utc), passed_constraints=True,
    )

    # Trial B: low throughput, high latency (clearly worse)
    trial_b = Trial(
        id="b", sweep_id="sweep", config={}, metrics={"throughput": 100, "latency": 150},
        status=TrialStatus.SUCCESS, trial_number=0, stdout="", stderr="", exit_code=0, duration_ms=1000, started_at=datetime.now(timezone.utc), completed_at=datetime.now(timezone.utc), passed_constraints=True,
    )

    # Trial C: high throughput, high latency (trade-off)
    trial_c = Trial(
        id="c", sweep_id="sweep", config={}, metrics={"throughput": 250, "latency": 200},
        status=TrialStatus.SUCCESS, trial_number=0, stdout="", stderr="", exit_code=0, duration_ms=1000, started_at=datetime.now(timezone.utc), completed_at=datetime.now(timezone.utc), passed_constraints=True,
    )

    # A dominates B (better in both)
    assert dominates(trial_a, trial_b, objectives)

    # A does not dominate C (A has lower latency, C has higher throughput)
    assert not dominates(trial_a, trial_c, objectives)

    # C does not dominate A (trade-off)
    assert not dominates(trial_c, trial_a, objectives)


def test_pareto_frontier():
    """Test Pareto frontier computation."""
    obj1 = Objective(metric="throughput", direction="maximize")
    obj2 = Objective(metric="latency", direction="minimize")
    objectives = [obj1, obj2]

    trials = [
        # Pareto optimal: high throughput, low latency
        Trial(
            id="1", sweep_id="sweep", config={"x": 1},
            metrics={"throughput": 200, "latency": 50},
            status=TrialStatus.SUCCESS, trial_number=0, stdout="", stderr="", exit_code=0, duration_ms=1000, started_at=datetime.now(timezone.utc), completed_at=datetime.now(timezone.utc), passed_constraints=True,
        ),
        # Dominated: low throughput, high latency
        Trial(
            id="2", sweep_id="sweep", config={"x": 2},
            metrics={"throughput": 100, "latency": 150},
            status=TrialStatus.SUCCESS, trial_number=0, stdout="", stderr="", exit_code=0, duration_ms=1000, started_at=datetime.now(timezone.utc), completed_at=datetime.now(timezone.utc), passed_constraints=True,
        ),
        # Pareto optimal: higher throughput, higher latency (trade-off)
        Trial(
            id="3", sweep_id="sweep", config={"x": 3},
            metrics={"throughput": 250, "latency": 100},
            status=TrialStatus.SUCCESS, trial_number=0, stdout="", stderr="", exit_code=0, duration_ms=1000, started_at=datetime.now(timezone.utc), completed_at=datetime.now(timezone.utc), passed_constraints=True,
        ),
        # Pareto optimal: lower throughput, lower latency (trade-off)
        Trial(
            id="4", sweep_id="sweep", config={"x": 4},
            metrics={"throughput": 150, "latency": 30},
            status=TrialStatus.SUCCESS, trial_number=0, stdout="", stderr="", exit_code=0, duration_ms=1000, started_at=datetime.now(timezone.utc), completed_at=datetime.now(timezone.utc), passed_constraints=True,
        ),
    ]

    pareto = compute_pareto_frontier(trials, objectives)

    assert len(pareto) == 3
    pareto_ids = {t.id for t in pareto}
    assert pareto_ids == {"1", "3", "4"}  # Trial 2 is dominated


def test_get_best_trials_single_objective():
    """Test get_best_trials returns top trial for single objective."""
    trials = [
        Trial(
            id="1", sweep_id="sweep", config={}, metrics={"score": 100},
            status=TrialStatus.SUCCESS, trial_number=0, stdout="", stderr="", exit_code=0, duration_ms=1000, started_at=datetime.now(timezone.utc), completed_at=datetime.now(timezone.utc), passed_constraints=True,
        ),
        Trial(
            id="2", sweep_id="sweep", config={}, metrics={"score": 200},
            status=TrialStatus.SUCCESS, trial_number=0, stdout="", stderr="", exit_code=0, duration_ms=1000, started_at=datetime.now(timezone.utc), completed_at=datetime.now(timezone.utc), passed_constraints=True,
        ),
    ]

    obj = Objective(metric="score", direction="maximize")
    best = get_best_trials(trials, [obj])

    assert len(best) == 1
    assert best[0].id == "2"


def test_get_best_trials_multi_objective():
    """Test get_best_trials returns Pareto frontier for multiple objectives."""
    objectives = [
        Objective(metric="throughput", direction="maximize"),
        Objective(metric="latency", direction="minimize"),
    ]

    trials = [
        Trial(
            id="1", sweep_id="sweep", config={},
            metrics={"throughput": 200, "latency": 50},
            status=TrialStatus.SUCCESS, trial_number=0, stdout="", stderr="", exit_code=0, duration_ms=1000, started_at=datetime.now(timezone.utc), completed_at=datetime.now(timezone.utc), passed_constraints=True,
        ),
        Trial(
            id="2", sweep_id="sweep", config={},
            metrics={"throughput": 100, "latency": 150},
            status=TrialStatus.SUCCESS, trial_number=0, stdout="", stderr="", exit_code=0, duration_ms=1000, started_at=datetime.now(timezone.utc), completed_at=datetime.now(timezone.utc), passed_constraints=True,
        ),
    ]

    best = get_best_trials(trials, objectives)

    assert len(best) == 1  # Only trial 1 is on Pareto frontier
    assert best[0].id == "1"


def test_rank_pareto_trials_with_equal_weights():
    """Test weighted ranking of Pareto frontier with equal weights."""
    objectives = [
        Objective(metric="throughput", direction="maximize", weight=1.0),
        Objective(metric="latency", direction="minimize", weight=1.0),
    ]

    # All three are Pareto optimal (different tradeoffs)
    pareto_trials = [
        # High throughput, medium latency
        Trial(
            id="1", sweep_id="sweep", config={},
            metrics={"throughput": 300, "latency": 100},
            status=TrialStatus.SUCCESS, trial_number=0, stdout="", stderr="", exit_code=0, duration_ms=1000, started_at=datetime.now(timezone.utc), completed_at=datetime.now(timezone.utc), passed_constraints=True,
        ),
        # Medium throughput, low latency (best balance with equal weights)
        Trial(
            id="2", sweep_id="sweep", config={},
            metrics={"throughput": 200, "latency": 50},
            status=TrialStatus.SUCCESS, trial_number=0, stdout="", stderr="", exit_code=0, duration_ms=1000, started_at=datetime.now(timezone.utc), completed_at=datetime.now(timezone.utc), passed_constraints=True,
        ),
        # Low throughput, very low latency
        Trial(
            id="3", sweep_id="sweep", config={},
            metrics={"throughput": 150, "latency": 30},
            status=TrialStatus.SUCCESS, trial_number=0, stdout="", stderr="", exit_code=0, duration_ms=1000, started_at=datetime.now(timezone.utc), completed_at=datetime.now(timezone.utc), passed_constraints=True,
        ),
    ]

    ranked = rank_pareto_trials(pareto_trials, objectives)

    assert len(ranked) == 3
    # With equal weights, trial 2 should rank highest (best balance)
    # throughput normalized: (200-150)/(300-150) = 0.33
    # latency normalized: 1 - (50-30)/(100-30) = 1 - 0.29 = 0.71
    # score = (0.33 + 0.71) / 2 = 0.52
    assert ranked[0].id == "2"


def test_rank_pareto_trials_prefer_throughput():
    """Test weighted ranking prefers throughput when weight is higher."""
    objectives = [
        Objective(metric="throughput", direction="maximize", weight=3.0),  # 3x more important
        Objective(metric="latency", direction="minimize", weight=1.0),
    ]

    pareto_trials = [
        # High throughput, high latency (should win with high throughput weight)
        Trial(
            id="1", sweep_id="sweep", config={},
            metrics={"throughput": 300, "latency": 100},
            status=TrialStatus.SUCCESS, trial_number=0, stdout="", stderr="", exit_code=0, duration_ms=1000, started_at=datetime.now(timezone.utc), completed_at=datetime.now(timezone.utc), passed_constraints=True,
        ),
        # Medium throughput, low latency
        Trial(
            id="2", sweep_id="sweep", config={},
            metrics={"throughput": 200, "latency": 50},
            status=TrialStatus.SUCCESS, trial_number=0, stdout="", stderr="", exit_code=0, duration_ms=1000, started_at=datetime.now(timezone.utc), completed_at=datetime.now(timezone.utc), passed_constraints=True,
        ),
    ]

    ranked = rank_pareto_trials(pareto_trials, objectives)

    assert len(ranked) == 2
    # With 3x weight on throughput, trial 1 should rank higher
    assert ranked[0].id == "1"


def test_rank_pareto_trials_prefer_latency():
    """Test weighted ranking prefers latency when weight is higher."""
    objectives = [
        Objective(metric="throughput", direction="maximize", weight=1.0),
        Objective(metric="latency", direction="minimize", weight=3.0),  # 3x more important
    ]

    pareto_trials = [
        # High throughput, high latency
        Trial(
            id="1", sweep_id="sweep", config={},
            metrics={"throughput": 300, "latency": 100},
            status=TrialStatus.SUCCESS, trial_number=0, stdout="", stderr="", exit_code=0, duration_ms=1000, started_at=datetime.now(timezone.utc), completed_at=datetime.now(timezone.utc), passed_constraints=True,
        ),
        # Medium throughput, low latency (should win with high latency weight)
        Trial(
            id="2", sweep_id="sweep", config={},
            metrics={"throughput": 200, "latency": 50},
            status=TrialStatus.SUCCESS, trial_number=0, stdout="", stderr="", exit_code=0, duration_ms=1000, started_at=datetime.now(timezone.utc), completed_at=datetime.now(timezone.utc), passed_constraints=True,
        ),
    ]

    ranked = rank_pareto_trials(pareto_trials, objectives)

    assert len(ranked) == 2
    # With 3x weight on latency, trial 2 should rank higher (lower latency)
    assert ranked[0].id == "2"


# ── Integration Tests ───────────────────────────────────────────────────────


@pytest.mark.trio
async def test_run_trial_success():
    """Test running a single trial end-to-end."""
    with tempfile.TemporaryDirectory() as tmpdir:
        working_dir = Path(tmpdir)

        # Create a simple test script
        script = working_dir / "bench.sh"
        script.write_text("#!/bin/bash\necho 'Throughput: 1234.5 tokens/s'\nexit 0")
        script.chmod(0o755)

        config = {"batch_size": 64}
        command_template = str(script.absolute())
        metrics_patterns = {"throughput": r"Throughput: ([0-9.]+)"}
        constraints = []

        trial = await run_trial(
            trial_number=0,
            config=config,
            sweep_id="test-sweep",
            command_template=command_template,
            metrics_patterns=metrics_patterns,
            constraints=constraints,
            working_dir=working_dir,
            timeout=10,
        )

        assert trial.status == TrialStatus.SUCCESS
        assert trial.metrics["throughput"] == 1234.5
        assert trial.passed_constraints is True
        assert trial.exit_code == 0


@pytest.mark.trio
async def test_run_trial_failure():
    """Test trial handles command failure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        working_dir = Path(tmpdir)

        # Script that fails
        script = working_dir / "fail.sh"
        script.write_text("#!/bin/bash\necho 'Error: something broke' >&2\nexit 1")
        script.chmod(0o755)

        trial = await run_trial(
            trial_number=0,
            config={},
            sweep_id="test-sweep",
            command_template=str(script.absolute()),
            metrics_patterns={},
            constraints=[],
            working_dir=working_dir,
            timeout=10,
        )

        assert trial.status == TrialStatus.FAILED
        assert "Error: something broke" in trial.stderr or trial.exit_code == 1


@pytest.mark.trio
async def test_run_trial_timeout():
    """Test trial handles timeout."""
    with tempfile.TemporaryDirectory() as tmpdir:
        working_dir = Path(tmpdir)

        # Script that sleeps forever
        script = working_dir / "slow.sh"
        script.write_text("#!/bin/bash\nsleep 100")
        script.chmod(0o755)

        trial = await run_trial(
            trial_number=0,
            config={},
            sweep_id="test-sweep",
            command_template=str(script.absolute()),
            metrics_patterns={},
            constraints=[],
            working_dir=working_dir,
            timeout=1,  # Very short timeout
        )

        assert trial.status == TrialStatus.TIMEOUT
        assert "timed out" in trial.stderr.lower()


@pytest.mark.trio
async def test_run_trial_constraint_violation():
    """Test trial fails when constraints not met."""
    with tempfile.TemporaryDirectory() as tmpdir:
        working_dir = Path(tmpdir)

        # Script outputs low accuracy
        script = working_dir / "bench.sh"
        script.write_text("#!/bin/bash\necho 'Accuracy: 0.50'")
        script.chmod(0o755)

        constraints = [Constraint(metric="accuracy", min=0.90)]

        trial = await run_trial(
            trial_number=0,
            config={},
            sweep_id="test-sweep",
            command_template=str(script.absolute()),
            metrics_patterns={"accuracy": r"Accuracy: ([0-9.]+)"},
            constraints=constraints,
            working_dir=working_dir,
            timeout=10,
        )

        assert trial.status == TrialStatus.CONSTRAINT_VIOLATION
        assert trial.passed_constraints is False
        assert trial.passed_constraints is False


@pytest.mark.trio
async def test_run_trial_parameter_substitution():
    """Test config parameters are correctly substituted into command."""
    with tempfile.TemporaryDirectory() as tmpdir:
        working_dir = Path(tmpdir)

        # Script echoes environment variable
        script = working_dir / "echo_param.sh"
        script.write_text("#!/bin/bash\necho \"Value: $PARAM\"")
        script.chmod(0o755)

        trial = await run_trial(
            trial_number=0,
            config={"param": 42},
            sweep_id="test-sweep",
            command_template=f"PARAM={{param}} {script.absolute()}",
            metrics_patterns={"value": r"Value: ([0-9]+)"},
            constraints=[],
            working_dir=working_dir,
            timeout=10,
        )

        assert trial.status == TrialStatus.SUCCESS
        assert trial.metrics["value"] == 42.0


# ── Resume/Crash Recovery Tests ────────────────────────────────────────────


@pytest.mark.trio
async def test_run_sweep_with_existing_trials_filters_completed():
    """Test that run_sweep filters out already-completed configs when resuming."""
    with tempfile.TemporaryDirectory() as tmpdir:
        working_dir = Path(tmpdir)

        # Create a simple test script
        script = working_dir / "bench.sh"
        script.write_text("#!/bin/bash\necho 'Score: 100'\nexit 0")
        script.chmod(0o755)

        # Config with 4 configs (2×2 grid)
        config = AutotunerConfig(
            name="test-sweep",
            search_space={"a": [1, 2], "b": [3, 4]},  # 2×2 = 4 configs
            command=str(script.absolute()),
            metrics={"score": r"Score: ([0-9]+)"},
            objectives=[Objective(metric="score", direction="maximize")],
            parallel=2,
            timeout=10,
            trials_per_config=1,  # One trial per config
        )

        # Grid order: (1,3), (1,4), (2,3), (2,4) with trial numbers 0, 1, 2, 3
        # Simulate that trials 0 and 3 already completed
        existing_trials = [
            Trial(
                id="trial-0",
                sweep_id="sweep-1",
                config={"a": 1, "b": 3},
                metrics={"score": 100},
                status=TrialStatus.SUCCESS,
                trial_number=0, stdout="", stderr="", exit_code=0, duration_ms=1000, started_at=datetime.now(timezone.utc), completed_at=datetime.now(timezone.utc),
                passed_constraints=True,
            ),
            Trial(
                id="trial-3",
                sweep_id="sweep-1",
                config={"a": 2, "b": 4},
                metrics={"score": 95},
                status=TrialStatus.SUCCESS,
                trial_number=3, stdout="", stderr="", exit_code=0, duration_ms=1000, started_at=datetime.now(timezone.utc), completed_at=datetime.now(timezone.utc),
                passed_constraints=True,
            ),
        ]

        # Run sweep with existing trials
        results = await run_sweep(
            config=config,
            sweep_id="sweep-1",
            working_dir=working_dir,
            existing_trials=existing_trials,
        )

        # Should have run only 2 new trials (skipped the 2 existing ones)
        # Total results = 2 existing + 2 new = 4
        assert len(results) == 4

        # Check that the existing trials are in the results
        result_configs = {frozenset(t.config.items()) for t in results}

        # All 4 possible configs should be present
        all_configs = {
            frozenset({"a": 1, "b": 3}.items()),
            frozenset({"a": 1, "b": 4}.items()),
            frozenset({"a": 2, "b": 3}.items()),
            frozenset({"a": 2, "b": 4}.items()),
        }
        assert result_configs == all_configs


@pytest.mark.trio
async def test_run_sweep_with_failed_trials_reruns_them():
    """Test that run_sweep re-runs failed trials (doesn't skip them)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        working_dir = Path(tmpdir)

        # Create a simple test script
        script = working_dir / "bench.sh"
        script.write_text("#!/bin/bash\necho 'Score: 100'\nexit 0")
        script.chmod(0o755)

        # Config with 2 configs
        config = AutotunerConfig(
            name="test-sweep",
            search_space={"a": [1, 2]},
            command=str(script.absolute()),
            metrics={"score": r"Score: ([0-9]+)"},
            objectives=[Objective(metric="score", direction="maximize")],
            parallel=2,
            timeout=10,
            trials_per_config=1,
        )

        # Simulate one successful and one failed trial
        # Grid order: a=1 (trial 0), a=2 (trial 1)
        existing_trials = [
            Trial(
                id="trial-0",
                sweep_id="sweep-1",
                config={"a": 1},
                metrics={"score": 100},
                status=TrialStatus.SUCCESS,
                trial_number=0, stdout="", stderr="", exit_code=0, duration_ms=1000, started_at=datetime.now(timezone.utc), completed_at=datetime.now(timezone.utc),
                passed_constraints=True,
            ),
            Trial(
                id="trial-1-failed",
                sweep_id="sweep-1",
                config={"a": 2},
                metrics={},
                status=TrialStatus.FAILED,
                trial_number=1, stdout="", stderr="Command failed", exit_code=1, duration_ms=1000, started_at=datetime.now(timezone.utc), completed_at=datetime.now(timezone.utc),
                passed_constraints=False,
            ),
        ]

        # Run sweep with existing trials
        results = await run_sweep(
            config=config,
            sweep_id="sweep-1",
            working_dir=working_dir,
            existing_trials=existing_trials,
        )

        # Should have:
        # - 1 existing successful trial (a=1)
        # - 1 existing failed trial (a=2)
        # - 1 new trial for a=2 (re-run the failed config)
        # Total = 3 trials (2 existing + 1 new)
        assert len(results) == 3

        # Count how many trials for config a=2
        a2_trials = [t for t in results if t.config == {"a": 2}]
        assert len(a2_trials) == 2  # One failed (old) + one new attempt


@pytest.mark.trio
async def test_run_sweep_without_existing_trials_runs_all():
    """Test that run_sweep without existing_trials runs all configs normally."""
    with tempfile.TemporaryDirectory() as tmpdir:
        working_dir = Path(tmpdir)

        # Create a simple test script
        script = working_dir / "bench.sh"
        script.write_text("#!/bin/bash\necho 'Score: 100'\nexit 0")
        script.chmod(0o755)

        # Config with 3 trials
        config = AutotunerConfig(
            name="test-sweep",
            search_space={"a": [1, 2, 3]},
            command=str(script.absolute()),
            metrics={"score": r"Score: ([0-9]+)"},
            objectives=[Objective(metric="score", direction="maximize")],
            parallel=2,
            timeout=10,
        )

        # Run sweep without existing trials
        results = await run_sweep(
            config=config,
            sweep_id="sweep-1",
            working_dir=working_dir,
            existing_trials=None,
        )

        # Should run all 3 trials
        assert len(results) == 3
        configs = [t.config for t in results]
        assert {"a": 1} in configs
        assert {"a": 2} in configs
        assert {"a": 3} in configs


@pytest.mark.trio
async def test_resume_continues_from_last_not_done():
    """Test that resume properly continues from the last not-done config.

    Simulates a crash scenario where:
    - Grid has 6 configs ordered: [1,1], [1,2], [1,3], [2,1], [2,2], [2,3]
    - First 3 completed successfully
    - Next one failed
    - Last 2 were never attempted
    - Resume should skip the 3 successful, retry the failed, and run the never-attempted
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        working_dir = Path(tmpdir)

        # Create a script that succeeds
        script = working_dir / "bench.sh"
        script.write_text("#!/bin/bash\necho 'Score: 100'\nexit 0")
        script.chmod(0o755)

        # Config with 6 configs (2x3 grid)
        config = AutotunerConfig(
            name="test-resume-sweep",
            search_space={"a": [1, 2], "b": [1, 2, 3]},  # 2×3 = 6 configs
            command=str(script.absolute()),
            metrics={"score": r"Score: ([0-9]+)"},
            objectives=[Objective(metric="score", direction="maximize")],
            parallel=2,
            timeout=10,
            trials_per_config=1,
        )

        # Simulate crash scenario:
        # Grid order: (1,1)=0, (1,2)=1, (1,3)=2, (2,1)=3, (2,2)=4, (2,3)=5
        # Completed: trials 0, 1, 2
        # Failed: trial 3
        # Never attempted: trials 4, 5
        existing_trials = [
            # Successful trials
            Trial(
                id="trial-0",
                sweep_id="sweep-resume",
                config={"a": 1, "b": 1},
                metrics={"score": 100},
                status=TrialStatus.SUCCESS,
                trial_number=0, stdout="", stderr="", exit_code=0, duration_ms=1000, started_at=datetime.now(timezone.utc), completed_at=datetime.now(timezone.utc),
                passed_constraints=True,
            ),
            Trial(
                id="trial-1",
                sweep_id="sweep-resume",
                config={"a": 1, "b": 2},
                metrics={"score": 105},
                status=TrialStatus.SUCCESS,
                trial_number=1, stdout="", stderr="", exit_code=0, duration_ms=1000, started_at=datetime.now(timezone.utc), completed_at=datetime.now(timezone.utc),
                passed_constraints=True,
            ),
            Trial(
                id="trial-2",
                sweep_id="sweep-resume",
                config={"a": 1, "b": 3},
                metrics={"score": 110},
                status=TrialStatus.SUCCESS,
                trial_number=2, stdout="", stderr="", exit_code=0, duration_ms=1000, started_at=datetime.now(timezone.utc), completed_at=datetime.now(timezone.utc),
                passed_constraints=True,
            ),
            # Failed trial (should be retried)
            Trial(
                id="trial-3-failed",
                sweep_id="sweep-resume",
                config={"a": 2, "b": 1},
                metrics={},
                status=TrialStatus.FAILED,
                trial_number=3, stdout="", stderr="Previous run failed", exit_code=1, duration_ms=500, started_at=datetime.now(timezone.utc), completed_at=datetime.now(timezone.utc),
                passed_constraints=False,
            ),
        ]

        # Resume the sweep
        results = await run_sweep(
            config=config,
            sweep_id="sweep-resume",
            working_dir=working_dir,
            existing_trials=existing_trials,
        )

        # Verify results
        # Should have: 4 existing + 3 new = 7 total trials
        # (3 successful existing, 1 failed existing, 3 new: retry (2,1) + first-time (2,2) + first-time (2,3))
        assert len(results) == 7

        # Count trials by config
        config_counts = {}
        for trial in results:
            key = frozenset(trial.config.items())
            config_counts[key] = config_counts.get(key, 0) + 1

        # Verify: 3 successful configs appear once
        assert config_counts[frozenset({"a": 1, "b": 1}.items())] == 1
        assert config_counts[frozenset({"a": 1, "b": 2}.items())] == 1
        assert config_counts[frozenset({"a": 1, "b": 3}.items())] == 1

        # Verify: Failed config was retried (appears twice: 1 failed + 1 new)
        assert config_counts[frozenset({"a": 2, "b": 1}.items())] == 2

        # Verify: Never-attempted configs appear once
        assert config_counts[frozenset({"a": 2, "b": 2}.items())] == 1
        assert config_counts[frozenset({"a": 2, "b": 3}.items())] == 1

        # Verify that the retried config now has a successful trial
        a2b1_trials = [t for t in results if t.config == {"a": 2, "b": 1}]
        assert len(a2b1_trials) == 2
        # One should be failed (old), one should be successful (new)
        statuses = {t.status for t in a2b1_trials}
        assert TrialStatus.FAILED in statuses
        assert TrialStatus.SUCCESS in statuses


# ── Streaming Tests ─────────────────────────────────────────────────────────


@pytest.mark.trio
async def test_run_sweep_streaming_creates_progress_file():
    """Test that run_sweep_streaming creates and writes to progress file."""
    import json
    from wafer_core.tools.autotuner.streaming import run_sweep_streaming

    with tempfile.TemporaryDirectory() as tmpdir:
        working_dir = Path(tmpdir)
        progress_file = Path(tmpdir) / "progress.jsonl"

        # Create a simple test script
        script = working_dir / "bench.sh"
        script.write_text("#!/bin/bash\necho 'Score: 100'\nexit 0")
        script.chmod(0o755)

        # Config with 2 trials
        config_dict = {
            "name": "test-streaming",
            "search_space": {"a": [1, 2]},
            "command": str(script.absolute()),
            "metrics": {"score": r"Score: ([0-9]+)"},
            "objectives": [{"metric": "score", "direction": "maximize"}],
            "parallel": 1,
            "timeout": 10,
        }

        # Run sweep with streaming
        sweep_id = await run_sweep_streaming(
            config=config_dict,
            working_dir=str(working_dir),
            progress_file=str(progress_file),
        )

        assert sweep_id is not None

        # Verify progress file was created and contains expected structure
        assert progress_file.exists()

        # Read and parse all lines
        with open(progress_file, 'r') as f:
            lines = [json.loads(line) for line in f if line.strip()]

        # Should have: sweep_started, 2 trials, sweep_completed
        assert len(lines) >= 4

        # First line should be sweep_started
        assert lines[0]["type"] == "sweep_started"
        assert lines[0]["sweep_id"] == sweep_id
        assert lines[0]["name"] == "test-streaming"
        assert lines[0]["total_trials"] == 2

        # Last line should be sweep_completed
        assert lines[-1]["type"] == "sweep_completed"
        assert lines[-1]["sweep_id"] == sweep_id

        # Middle lines should be trial results
        trial_lines = [line for line in lines if line.get("status")]
        assert len(trial_lines) == 2
        for trial in trial_lines:
            assert "id" in trial
            assert "config" in trial
            assert "metrics" in trial
            assert trial["status"] == "success"


@pytest.mark.trio
async def test_run_sweep_streaming_handles_failure():
    """Test that run_sweep_streaming handles failed trials correctly."""
    import json
    from wafer_core.tools.autotuner.streaming import run_sweep_streaming

    with tempfile.TemporaryDirectory() as tmpdir:
        working_dir = Path(tmpdir)
        progress_file = Path(tmpdir) / "progress.jsonl"

        # Config with invalid command - trials will fail but sweep completes
        config_dict = {
            "name": "test-streaming-fail",
            "search_space": {"a": [1]},
            "command": "/this/command/does/not/exist {a}",  # Non-existent executable
            "metrics": {"value": r"Value: ([0-9]+)"},
            "parallel": 1,
            "timeout": 10,
        }

        # Run sweep - should complete even with failed trials
        await run_sweep_streaming(
            config=config_dict,
            working_dir=str(working_dir),
            progress_file=str(progress_file),
        )

        # Verify progress file contains expected markers
        assert progress_file.exists()

        with open(progress_file, 'r') as f:
            lines = [json.loads(line) for line in f if line.strip()]

        # Should have sweep_started, trial with failed status, and sweep_completed
        assert any(line.get("type") == "sweep_started" for line in lines)
        assert any(line.get("type") == "sweep_completed" for line in lines)

        # Find trial result line (not a type marker)
        trial_lines = [line for line in lines if "type" not in line]
        assert len(trial_lines) == 1

        # Verify trial has failed status
        trial = trial_lines[0]
        assert trial["status"] == "failed"


@pytest.mark.trio
async def test_run_sweep_streaming_trial_updates():
    """Test that run_sweep_streaming writes each trial as it completes."""
    import json
    from wafer_core.tools.autotuner.streaming import run_sweep_streaming

    with tempfile.TemporaryDirectory() as tmpdir:
        working_dir = Path(tmpdir)
        progress_file = Path(tmpdir) / "progress.jsonl"

        # Create scripts with different outputs
        script1 = working_dir / "bench1.sh"
        script1.write_text("#!/bin/bash\necho 'Score: 100'\nexit 0")
        script1.chmod(0o755)

        # Config with 3 trials
        config_dict = {
            "name": "test-streaming-updates",
            "search_space": {"a": [1, 2, 3]},
            "command": str(script1.absolute()),
            "metrics": {"score": r"Score: ([0-9]+)"},
            "parallel": 1,  # Run serially to ensure order
            "timeout": 10,
        }

        # Run sweep
        await run_sweep_streaming(
            config=config_dict,
            working_dir=str(working_dir),
            progress_file=str(progress_file),
        )

        # Read progress file
        with open(progress_file, 'r') as f:
            lines = [json.loads(line) for line in f if line.strip()]

        # Extract trial updates (lines with 'status' field)
        trial_updates = [line for line in lines if "status" in line and line.get("type") != "sweep_failed"]

        # Should have 3 trial updates
        assert len(trial_updates) == 3

        # Each should have proper structure
        for trial in trial_updates:
            assert "id" in trial
            assert "config" in trial
            assert "metrics" in trial
            assert "status" in trial
            assert trial["config"]["a"] in [1, 2, 3]
            assert trial["metrics"]["score"] == 100.0


@pytest.mark.trio
async def test_run_sweep_streaming_with_autotuner_config_object():
    """Test that run_sweep_streaming accepts AutotunerConfig object directly."""
    from wafer_core.tools.autotuner.streaming import run_sweep_streaming

    with tempfile.TemporaryDirectory() as tmpdir:
        working_dir = Path(tmpdir)
        progress_file = Path(tmpdir) / "progress.jsonl"

        # Create test script
        script = working_dir / "bench.sh"
        script.write_text("#!/bin/bash\necho 'Score: 50'\nexit 0")
        script.chmod(0o755)

        # Create AutotunerConfig object (not dict)
        config = AutotunerConfig(
            name="test-with-object",
            search_space={"x": [1]},
            command=str(script.absolute()),
            metrics={"score": r"Score: ([0-9]+)"},
            objectives=[Objective(metric="score", direction="maximize")],
            parallel=1,
            timeout=10,
        )

        # Run with object (not dict)
        sweep_id = await run_sweep_streaming(
            config=config,  # Pass object directly
            working_dir=working_dir,
            progress_file=progress_file,
        )

        assert sweep_id is not None
        assert progress_file.exists()


@pytest.mark.trio
async def test_run_sweep_streaming_with_path_objects():
    """Test that run_sweep_streaming accepts Path objects for directories."""
    from wafer_core.tools.autotuner.streaming import run_sweep_streaming

    with tempfile.TemporaryDirectory() as tmpdir:
        working_dir = Path(tmpdir)
        progress_file = Path(tmpdir) / "progress.jsonl"

        # Create test script
        script = working_dir / "bench.sh"
        script.write_text("#!/bin/bash\necho 'Value: 123'\nexit 0")
        script.chmod(0o755)

        config_dict = {
            "name": "test-path-objects",
            "search_space": {"y": [1]},
            "command": str(script.absolute()),
            "metrics": {"value": r"Value: ([0-9]+)"},
            "parallel": 1,
            "timeout": 10,
        }

        # Pass Path objects (not strings)
        sweep_id = await run_sweep_streaming(
            config=config_dict,
            working_dir=working_dir,  # Path object
            progress_file=progress_file,  # Path object
        )

        assert sweep_id is not None
        assert progress_file.exists()


@pytest.mark.trio
async def test_run_trial_case_insensitive_metrics():
    """Test that metric extraction is case-insensitive."""
    with tempfile.TemporaryDirectory() as tmpdir:
        working_dir = Path(tmpdir)

        # Create script with mixed-case output
        script = working_dir / "bench.sh"
        script.write_text("#!/bin/bash\necho 'ACCURACY: 0.95'\necho 'Loss: 0.05'\nexit 0")
        script.chmod(0o755)

        # Pattern uses lowercase, output uses uppercase
        trial = await run_trial(
            config={},
            sweep_id="test",
            trial_number=0,
            command_template=str(script.absolute()),
            metrics_patterns={
                "accuracy": r"accuracy[:\s=]+([0-9.]+)",  # lowercase pattern
                "loss": r"loss[:\s=]+([0-9.]+)",  # lowercase pattern
            },
            constraints=[],
            working_dir=working_dir,
            timeout=10,
        )

        # Should match despite case mismatch
        assert trial.status == TrialStatus.SUCCESS
        assert trial.metrics["accuracy"] == 0.95
        assert trial.metrics["loss"] == 0.05


@pytest.mark.trio
async def test_run_trial_auto_metric_detection():
    """Test that auto metric detection works with common patterns."""
    with tempfile.TemporaryDirectory() as tmpdir:
        working_dir = Path(tmpdir)

        # Create script with various output formats
        script = working_dir / "bench.sh"
        script.write_text("""#!/bin/bash
echo 'throughput: 1234.5'
echo 'latency = 50'
echo 'accuracy 0.95'
exit 0
""")
        script.chmod(0o755)

        # Use "auto" for all metrics
        trial = await run_trial(
            config={},
            sweep_id="test",
            trial_number=0,
            command_template=str(script.absolute()),
            metrics_patterns={
                "throughput": "auto",
                "latency": "auto",
                "accuracy": "auto",
            },
            constraints=[],
            working_dir=working_dir,
            timeout=10,
        )

        # Should auto-detect all metrics
        assert trial.status == TrialStatus.SUCCESS
        assert trial.metrics["throughput"] == 1234.5
        assert trial.metrics["latency"] == 50.0
        assert trial.metrics["accuracy"] == 0.95


@pytest.mark.trio
async def test_run_trial_json_output():
    """Test that metrics can be extracted from JSON output."""
    with tempfile.TemporaryDirectory() as tmpdir:
        working_dir = Path(tmpdir)

        # Create script that outputs JSON
        script = working_dir / "bench.sh"
        script.write_text("""#!/bin/bash
echo '{"throughput": 1234.5, "latency": 50, "accuracy": 0.95}'
exit 0
""")
        script.chmod(0o755)

        # Use "auto" for all metrics
        trial = await run_trial(
            config={},
            sweep_id="test",
            trial_number=0,
            command_template=str(script.absolute()),
            metrics_patterns={
                "throughput": "auto",
                "latency": "auto",
                "accuracy": "auto",
            },
            constraints=[],
            working_dir=working_dir,
            timeout=10,
        )

        # Should extract from JSON
        assert trial.status == TrialStatus.SUCCESS
        assert trial.metrics["throughput"] == 1234.5
        assert trial.metrics["latency"] == 50.0
        assert trial.metrics["accuracy"] == 0.95


@pytest.mark.trio
async def test_run_trial_mixed_auto_and_regex():
    """Test that auto and regex patterns can be mixed."""
    with tempfile.TemporaryDirectory() as tmpdir:
        working_dir = Path(tmpdir)

        # Create script with mixed output
        script = working_dir / "bench.sh"
        script.write_text("""#!/bin/bash
echo 'throughput: 1234.5'
echo 'Custom metric format: Value=999'
exit 0
""")
        script.chmod(0o755)

        # Mix auto and regex
        trial = await run_trial(
            config={},
            sweep_id="test",
            trial_number=0,
            command_template=str(script.absolute()),
            metrics_patterns={
                "throughput": "auto",
                "custom": r"Value=([0-9]+)",  # regex for non-standard format
            },
            constraints=[],
            working_dir=working_dir,
            timeout=10,
        )

        # Should work with both
        assert trial.status == TrialStatus.SUCCESS
        assert trial.metrics["throughput"] == 1234.5
        assert trial.metrics["custom"] == 999.0


# ── Aggregation Tests ───────────────────────────────────────────────────────


def test_aggregate_trials_by_config_basic():
    """Test basic aggregation of trials by configuration."""
    from wafer_core.tools.autotuner.aggregation import aggregate_trials_by_config

    # Create 4 configs × 3 trials = 12 trials
    trials = []
    for config_idx in range(4):
        for trial_idx in range(3):
            trial_number = config_idx * 3 + trial_idx
            trials.append(
                Trial(
                    id=f"trial-{trial_number}",
                    sweep_id="sweep-1",
                    trial_number=trial_number,
                    config={"param": config_idx * 10},
                    metrics={"score": 100.0 + trial_idx, "latency": 50.0 - trial_idx},
                    status=TrialStatus.SUCCESS,
                    stdout="",
                    stderr="",
                    exit_code=0,
                    duration_ms=1000,
                    started_at=datetime.now(timezone.utc),
                    completed_at=datetime.now(timezone.utc),
                    passed_constraints=True,
                )
            )

    # Aggregate
    aggregated = aggregate_trials_by_config(trials, trials_per_config=3)

    # Should have 4 aggregated configs
    assert len(aggregated) == 4

    # Check first config
    config0 = aggregated[0]
    assert config0.config_number == 0
    assert config0.config == {"param": 0}
    assert len(config0.trials) == 3
    assert config0.all_passed_constraints is True

    # Check statistics for score metric (values: 100, 101, 102)
    score_stats = config0.metrics["score"]
    assert score_stats.mean == 101.0
    assert score_stats.min == 100.0
    assert score_stats.max == 102.0
    assert abs(score_stats.std - 0.816496580927726) < 0.01  # Sample std

    # Check statistics for latency metric (values: 50, 49, 48)
    latency_stats = config0.metrics["latency"]
    assert latency_stats.mean == 49.0
    assert latency_stats.min == 48.0
    assert latency_stats.max == 50.0


def test_aggregate_trials_by_config_with_failures():
    """Test aggregation excludes failed trials."""
    from wafer_core.tools.autotuner.aggregation import aggregate_trials_by_config

    # Create 2 configs × 3 trials = 6 trials
    # Config 0: all successful
    # Config 1: 2 successful, 1 failed
    trials = []

    # Config 0: all successful
    for trial_idx in range(3):
        trials.append(
            Trial(
                id=f"trial-{trial_idx}",
                sweep_id="sweep-1",
                trial_number=trial_idx,
                config={"param": 0},
                metrics={"score": 100.0 + trial_idx},
                status=TrialStatus.SUCCESS,
                stdout="",
                stderr="",
                exit_code=0,
                duration_ms=1000,
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc),
                passed_constraints=True,
            )
        )

    # Config 1: 2 successful, 1 failed
    trials.append(
        Trial(
            id="trial-3",
            sweep_id="sweep-1",
            trial_number=3,
            config={"param": 10},
            metrics={"score": 200.0},
            status=TrialStatus.SUCCESS,
            stdout="",
            stderr="",
            exit_code=0,
            duration_ms=1000,
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            passed_constraints=True,
        )
    )
    trials.append(
        Trial(
            id="trial-4",
            sweep_id="sweep-1",
            trial_number=4,
            config={"param": 10},
            metrics={},
            status=TrialStatus.FAILED,  # Failed trial
            stdout="",
            stderr="Error",
            exit_code=1,
            duration_ms=500,
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            passed_constraints=False,
        )
    )
    trials.append(
        Trial(
            id="trial-5",
            sweep_id="sweep-1",
            trial_number=5,
            config={"param": 10},
            metrics={"score": 202.0},
            status=TrialStatus.SUCCESS,
            stdout="",
            stderr="",
            exit_code=0,
            duration_ms=1000,
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            passed_constraints=True,
        )
    )

    # Aggregate
    aggregated = aggregate_trials_by_config(trials, trials_per_config=3)

    # Should have 2 configs
    assert len(aggregated) == 2

    # Config 0: mean of 100, 101, 102 = 101
    assert aggregated[0].metrics["score"].mean == 101.0
    assert len(aggregated[0].metrics["score"].values) == 3

    # Config 1: mean of 200, 202 = 201 (failed trial excluded)
    assert aggregated[1].metrics["score"].mean == 201.0
    assert len(aggregated[1].metrics["score"].values) == 2


def test_aggregate_trials_by_config_single_trial():
    """Test that trials_per_config=1 returns empty list (no aggregation needed)."""
    from wafer_core.tools.autotuner.aggregation import aggregate_trials_by_config

    trials = [
        Trial(
            id="trial-0",
            sweep_id="sweep-1",
            trial_number=0,
            config={"param": 0},
            metrics={"score": 100.0},
            status=TrialStatus.SUCCESS,
            stdout="",
            stderr="",
            exit_code=0,
            duration_ms=1000,
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            passed_constraints=True,
        )
    ]

    # With trials_per_config=1, no aggregation needed
    aggregated = aggregate_trials_by_config(trials, trials_per_config=1)
    assert len(aggregated) == 0


def test_aggregate_trials_by_config_all_failed():
    """Test that configs with all failed trials are excluded."""
    from wafer_core.tools.autotuner.aggregation import aggregate_trials_by_config

    # Create config where all trials failed
    trials = []
    for trial_idx in range(3):
        trials.append(
            Trial(
                id=f"trial-{trial_idx}",
                sweep_id="sweep-1",
                trial_number=trial_idx,
                config={"param": 0},
                metrics={},
                status=TrialStatus.FAILED,
                stdout="",
                stderr="Error",
                exit_code=1,
                duration_ms=500,
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc),
                passed_constraints=False,
            )
        )

    # Aggregate
    aggregated = aggregate_trials_by_config(trials, trials_per_config=3)

    # Should have 0 configs (all failed)
    assert len(aggregated) == 0


def test_aggregate_trials_by_config_constraint_check():
    """Test that all_passed_constraints is set correctly."""
    from wafer_core.tools.autotuner.aggregation import aggregate_trials_by_config

    # Create config where 2 passed, 1 violated constraint
    trials = []
    for trial_idx in range(3):
        passed = trial_idx < 2  # First 2 pass, last one fails constraint
        trials.append(
            Trial(
                id=f"trial-{trial_idx}",
                sweep_id="sweep-1",
                trial_number=trial_idx,
                config={"param": 0},
                metrics={"score": 100.0 + trial_idx},
                status=TrialStatus.SUCCESS,
                stdout="",
                stderr="",
                exit_code=0,
                duration_ms=1000,
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc),
                passed_constraints=passed,
            )
        )

    # Aggregate
    aggregated = aggregate_trials_by_config(trials, trials_per_config=3)

    # Should have 1 config
    assert len(aggregated) == 1

    # all_passed_constraints should be False (not all passed)
    assert aggregated[0].all_passed_constraints is False


# ── Config-based Scoring Tests ──────────────────────────────────────────────


def test_dominates_config():
    """Test dominance comparison between configs."""
    from wafer_core.tools.autotuner.scoring import dominates_config
    from wafer_core.tools.autotuner.dtypes import AggregatedConfig, MetricStats

    # Create two configs
    config_a = AggregatedConfig(
        config_number=0,
        config={"param": 0},
        trials=[],
        metrics={
            "throughput": MetricStats(mean=100.0, std=1.0, min=99.0, max=101.0, values=[99.0, 100.0, 101.0]),
            "latency": MetricStats(mean=50.0, std=1.0, min=49.0, max=51.0, values=[49.0, 50.0, 51.0]),
        },
        all_passed_constraints=True,
    )

    config_b = AggregatedConfig(
        config_number=1,
        config={"param": 10},
        trials=[],
        metrics={
            "throughput": MetricStats(mean=90.0, std=1.0, min=89.0, max=91.0, values=[89.0, 90.0, 91.0]),
            "latency": MetricStats(mean=60.0, std=1.0, min=59.0, max=61.0, values=[59.0, 60.0, 61.0]),
        },
        all_passed_constraints=True,
    )

    objectives = [
        Objective(metric="throughput", direction="maximize"),
        Objective(metric="latency", direction="minimize"),
    ]

    # Config A dominates B (higher throughput, lower latency)
    assert dominates_config(config_a, config_b, objectives) is True
    assert dominates_config(config_b, config_a, objectives) is False


def test_dominates_config_equal():
    """Test that equal configs don't dominate each other."""
    from wafer_core.tools.autotuner.scoring import dominates_config
    from wafer_core.tools.autotuner.dtypes import AggregatedConfig, MetricStats

    config_a = AggregatedConfig(
        config_number=0,
        config={"param": 0},
        trials=[],
        metrics={
            "score": MetricStats(mean=100.0, std=1.0, min=99.0, max=101.0, values=[99.0, 100.0, 101.0]),
        },
        all_passed_constraints=True,
    )

    config_b = AggregatedConfig(
        config_number=1,
        config={"param": 10},
        trials=[],
        metrics={
            "score": MetricStats(mean=100.0, std=2.0, min=98.0, max=102.0, values=[98.0, 100.0, 102.0]),
        },
        all_passed_constraints=True,
    )

    objectives = [Objective(metric="score", direction="maximize")]

    # Equal means - neither dominates
    assert dominates_config(config_a, config_b, objectives) is False
    assert dominates_config(config_b, config_a, objectives) is False


def test_compute_pareto_frontier_configs():
    """Test Pareto frontier computation for configs."""
    from wafer_core.tools.autotuner.scoring import compute_pareto_frontier_configs
    from wafer_core.tools.autotuner.dtypes import AggregatedConfig, MetricStats

    # Create 3 configs
    configs = [
        AggregatedConfig(
            config_number=0,
            config={"param": 0},
            trials=[],
            metrics={
                "throughput": MetricStats(mean=100.0, std=1.0, min=99.0, max=101.0, values=[]),
                "latency": MetricStats(mean=50.0, std=1.0, min=49.0, max=51.0, values=[]),
            },
            all_passed_constraints=True,
        ),
        AggregatedConfig(
            config_number=1,
            config={"param": 10},
            trials=[],
            metrics={
                "throughput": MetricStats(mean=90.0, std=1.0, min=89.0, max=91.0, values=[]),
                "latency": MetricStats(mean=40.0, std=1.0, min=39.0, max=41.0, values=[]),
            },
            all_passed_constraints=True,
        ),
        AggregatedConfig(
            config_number=2,
            config={"param": 20},
            trials=[],
            metrics={
                "throughput": MetricStats(mean=80.0, std=1.0, min=79.0, max=81.0, values=[]),
                "latency": MetricStats(mean=60.0, std=1.0, min=59.0, max=61.0, values=[]),
            },
            all_passed_constraints=True,
        ),
    ]

    objectives = [
        Objective(metric="throughput", direction="maximize"),
        Objective(metric="latency", direction="minimize"),
    ]

    # Compute Pareto frontier
    pareto = compute_pareto_frontier_configs(configs, objectives)

    # Config 0: high throughput, medium latency (Pareto optimal)
    # Config 1: medium throughput, low latency (Pareto optimal)
    # Config 2: low throughput, high latency (dominated by both)
    assert len(pareto) == 2
    assert configs[0] in pareto
    assert configs[1] in pareto
    assert configs[2] not in pareto


def test_compute_pareto_frontier_configs_filters_constraints():
    """Test that Pareto frontier only includes configs that passed constraints."""
    from wafer_core.tools.autotuner.scoring import compute_pareto_frontier_configs
    from wafer_core.tools.autotuner.dtypes import AggregatedConfig, MetricStats

    configs = [
        AggregatedConfig(
            config_number=0,
            config={"param": 0},
            trials=[],
            metrics={
                "score": MetricStats(mean=100.0, std=1.0, min=99.0, max=101.0, values=[]),
            },
            all_passed_constraints=True,  # Passed
        ),
        AggregatedConfig(
            config_number=1,
            config={"param": 10},
            trials=[],
            metrics={
                "score": MetricStats(mean=200.0, std=1.0, min=199.0, max=201.0, values=[]),
            },
            all_passed_constraints=False,  # Failed constraints
        ),
    ]

    objectives = [Objective(metric="score", direction="maximize")]

    # Compute Pareto frontier
    pareto = compute_pareto_frontier_configs(configs, objectives)

    # Only config 0 should be included (config 1 failed constraints)
    assert len(pareto) == 1
    assert configs[0] in pareto


def test_rank_configs_single_objective_maximize():
    """Test ranking configs by single objective (maximize)."""
    from wafer_core.tools.autotuner.scoring import rank_configs_single_objective
    from wafer_core.tools.autotuner.dtypes import AggregatedConfig, MetricStats

    configs = [
        AggregatedConfig(
            config_number=0,
            config={"param": 0},
            trials=[],
            metrics={
                "score": MetricStats(mean=100.0, std=1.0, min=99.0, max=101.0, values=[]),
            },
            all_passed_constraints=True,
        ),
        AggregatedConfig(
            config_number=1,
            config={"param": 10},
            trials=[],
            metrics={
                "score": MetricStats(mean=150.0, std=1.0, min=149.0, max=151.0, values=[]),
            },
            all_passed_constraints=True,
        ),
        AggregatedConfig(
            config_number=2,
            config={"param": 20},
            trials=[],
            metrics={
                "score": MetricStats(mean=120.0, std=1.0, min=119.0, max=121.0, values=[]),
            },
            all_passed_constraints=True,
        ),
    ]

    objective = Objective(metric="score", direction="maximize")

    # Rank configs
    ranked = rank_configs_single_objective(configs, objective)

    # Should be sorted: 150, 120, 100
    assert len(ranked) == 3
    assert ranked[0].config_number == 1  # score=150
    assert ranked[1].config_number == 2  # score=120
    assert ranked[2].config_number == 0  # score=100


def test_rank_configs_single_objective_minimize():
    """Test ranking configs by single objective (minimize)."""
    from wafer_core.tools.autotuner.scoring import rank_configs_single_objective
    from wafer_core.tools.autotuner.dtypes import AggregatedConfig, MetricStats

    configs = [
        AggregatedConfig(
            config_number=0,
            config={"param": 0},
            trials=[],
            metrics={
                "latency": MetricStats(mean=50.0, std=1.0, min=49.0, max=51.0, values=[]),
            },
            all_passed_constraints=True,
        ),
        AggregatedConfig(
            config_number=1,
            config={"param": 10},
            trials=[],
            metrics={
                "latency": MetricStats(mean=30.0, std=1.0, min=29.0, max=31.0, values=[]),
            },
            all_passed_constraints=True,
        ),
        AggregatedConfig(
            config_number=2,
            config={"param": 20},
            trials=[],
            metrics={
                "latency": MetricStats(mean=40.0, std=1.0, min=39.0, max=41.0, values=[]),
            },
            all_passed_constraints=True,
        ),
    ]

    objective = Objective(metric="latency", direction="minimize")

    # Rank configs
    ranked = rank_configs_single_objective(configs, objective)

    # Should be sorted: 30, 40, 50
    assert len(ranked) == 3
    assert ranked[0].config_number == 1  # latency=30
    assert ranked[1].config_number == 2  # latency=40
    assert ranked[2].config_number == 0  # latency=50


def test_rank_pareto_configs_weighted():
    """Test ranking Pareto configs by weighted score."""
    from wafer_core.tools.autotuner.scoring import rank_pareto_configs
    from wafer_core.tools.autotuner.dtypes import AggregatedConfig, MetricStats

    # Create 3 Pareto-optimal configs with different trade-offs
    configs = [
        AggregatedConfig(
            config_number=0,
            config={"param": 0},
            trials=[],
            metrics={
                "throughput": MetricStats(mean=100.0, std=1.0, min=99.0, max=101.0, values=[]),
                "latency": MetricStats(mean=50.0, std=1.0, min=49.0, max=51.0, values=[]),
            },
            all_passed_constraints=True,
        ),
        AggregatedConfig(
            config_number=1,
            config={"param": 10},
            trials=[],
            metrics={
                "throughput": MetricStats(mean=80.0, std=1.0, min=79.0, max=81.0, values=[]),
                "latency": MetricStats(mean=30.0, std=1.0, min=29.0, max=31.0, values=[]),
            },
            all_passed_constraints=True,
        ),
        AggregatedConfig(
            config_number=2,
            config={"param": 20},
            trials=[],
            metrics={
                "throughput": MetricStats(mean=90.0, std=1.0, min=89.0, max=91.0, values=[]),
                "latency": MetricStats(mean=40.0, std=1.0, min=39.0, max=41.0, values=[]),
            },
            all_passed_constraints=True,
        ),
    ]

    # Weight throughput more heavily
    objectives = [
        Objective(metric="throughput", direction="maximize", weight=2.0),
        Objective(metric="latency", direction="minimize", weight=1.0),
    ]

    # Rank configs
    ranked = rank_pareto_configs(configs, objectives)

    # Should rank by weighted score (config 0 has highest throughput)
    assert len(ranked) == 3
    assert ranked[0].config_number == 0  # Highest throughput (weighted 2x)


def test_get_best_configs_single_objective():
    """Test get_best_configs with single objective."""
    from wafer_core.tools.autotuner.scoring import get_best_configs
    from wafer_core.tools.autotuner.dtypes import AggregatedConfig, MetricStats

    configs = [
        AggregatedConfig(
            config_number=0,
            config={"param": 0},
            trials=[],
            metrics={
                "score": MetricStats(mean=100.0, std=1.0, min=99.0, max=101.0, values=[]),
            },
            all_passed_constraints=True,
        ),
        AggregatedConfig(
            config_number=1,
            config={"param": 10},
            trials=[],
            metrics={
                "score": MetricStats(mean=150.0, std=1.0, min=149.0, max=151.0, values=[]),
            },
            all_passed_constraints=True,
        ),
    ]

    objectives = [Objective(metric="score", direction="maximize")]

    # Get best config
    best = get_best_configs(configs, objectives)

    # Should return single best config (score=150)
    assert len(best) == 1
    assert best[0].config_number == 1


def test_get_best_configs_multi_objective():
    """Test get_best_configs with multiple objectives returns Pareto frontier."""
    from wafer_core.tools.autotuner.scoring import get_best_configs
    from wafer_core.tools.autotuner.dtypes import AggregatedConfig, MetricStats

    configs = [
        AggregatedConfig(
            config_number=0,
            config={"param": 0},
            trials=[],
            metrics={
                "throughput": MetricStats(mean=100.0, std=1.0, min=99.0, max=101.0, values=[]),
                "latency": MetricStats(mean=50.0, std=1.0, min=49.0, max=51.0, values=[]),
            },
            all_passed_constraints=True,
        ),
        AggregatedConfig(
            config_number=1,
            config={"param": 10},
            trials=[],
            metrics={
                "throughput": MetricStats(mean=80.0, std=1.0, min=79.0, max=81.0, values=[]),
                "latency": MetricStats(mean=30.0, std=1.0, min=29.0, max=31.0, values=[]),
            },
            all_passed_constraints=True,
        ),
        AggregatedConfig(
            config_number=2,
            config={"param": 20},
            trials=[],
            metrics={
                "throughput": MetricStats(mean=70.0, std=1.0, min=69.0, max=71.0, values=[]),
                "latency": MetricStats(mean=60.0, std=1.0, min=59.0, max=61.0, values=[]),
            },
            all_passed_constraints=True,
        ),
    ]

    objectives = [
        Objective(metric="throughput", direction="maximize"),
        Objective(metric="latency", direction="minimize"),
    ]

    # Get best configs (Pareto frontier)
    best = get_best_configs(configs, objectives)

    # Should return Pareto frontier (configs 0 and 1)
    assert len(best) == 2
    config_numbers = {c.config_number for c in best}
    assert 0 in config_numbers
    assert 1 in config_numbers


def test_get_best_configs_no_objectives():
    """Test get_best_configs with no objectives returns all valid configs."""
    from wafer_core.tools.autotuner.scoring import get_best_configs
    from wafer_core.tools.autotuner.dtypes import AggregatedConfig, MetricStats

    configs = [
        AggregatedConfig(
            config_number=0,
            config={"param": 0},
            trials=[],
            metrics={
                "score": MetricStats(mean=100.0, std=1.0, min=99.0, max=101.0, values=[]),
            },
            all_passed_constraints=True,
        ),
        AggregatedConfig(
            config_number=1,
            config={"param": 10},
            trials=[],
            metrics={
                "score": MetricStats(mean=150.0, std=1.0, min=149.0, max=151.0, values=[]),
            },
            all_passed_constraints=False,  # Failed constraints
        ),
        AggregatedConfig(
            config_number=2,
            config={"param": 20},
            trials=[],
            metrics={
                "score": MetricStats(mean=120.0, std=1.0, min=119.0, max=121.0, values=[]),
            },
            all_passed_constraints=True,
        ),
    ]

    # Get best configs (no objectives)
    best = get_best_configs(configs, objectives=None)

    # Should return all configs that passed constraints
    assert len(best) == 2
    config_numbers = {c.config_number for c in best}
    assert 0 in config_numbers
    assert 2 in config_numbers


