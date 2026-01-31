#!/usr/bin/env python3
"""Test script for nested progress display.

This simulates the GEPA + KernelBench pattern where:
1. Outer progress group is created (GEPA optimization)
2. Inner progress group is created with tasks (minibatch eval)
3. Blocking work happens (imports, Modal calls)

Without flush(), the tasks won't be visible before blocking work.
With flush(), you see the tasks immediately.

Run:
    python packages/wafer-core/tests/test_nested_progress.py
"""

import sys
import time

sys.path.insert(0, "packages/wafer-core")

from wafer_core.rollouts.progress import ProgressGroup


def simulate_blocking_work(seconds: float = 2.0) -> None:
    """Simulate blocking work like imports or Modal cold start."""
    time.sleep(seconds)


def main():
    print("Testing nested progress with blocking work...")
    print("You should see tasks BEFORE the 2-second blocking wait.\n")

    with ProgressGroup("GEPA Optimization", total=3) as outer:
        outer.update(status="initial validation...")

        # This simulates evaluate_kernelbench_gepa
        with ProgressGroup("Minibatch Eval", total=2) as inner:
            # Add tasks
            for j, name in enumerate(["ReLU", "Softmax"]):
                inner.add_task(f"task_{j}", name=name)
                inner.update_task(f"task_{j}", status="pending...")

            inner.update(status="loading Modal...")
            inner.flush()  # <-- This makes tasks visible before blocking

            # Simulate slow imports / Modal cold start
            simulate_blocking_work(2.0)

            # Now complete the tasks
            inner.update(status="evaluating...")
            for j, _name in enumerate(["ReLU", "Softmax"]):
                inner.update_task(f"task_{j}", status="running...")
                time.sleep(0.3)
                inner.complete_task(f"task_{j}", success=True, message="1.2x")

        outer.update(completed=1, status="done!")
        time.sleep(0.5)

    print("\nDone!")


if __name__ == "__main__":
    main()
