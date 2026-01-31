"""Evaluation helpers.

Simple utilities for loading tasks. For running evals, use EvalConfig + evaluate() directly.

Example:
    from wafer_core.rollouts.eval_helpers import load_tasks
    from wafer_core.rollouts.evaluation import evaluate
    from wafer_core.rollouts.dtypes import EvalConfig, Endpoint, Message

    tasks = load_tasks("tasks.json")

    config = EvalConfig(
        endpoint=Endpoint(provider="anthropic", model="claude-sonnet-4-20250514", api_key=...),
        prepare_messages=lambda row: [
            Message(role="system", content="..."),
            Message(role="user", content=row["user_prompt"]),
        ],
        score_fn=llm_judge(JUDGE_PROMPT),
        environment=CodingEnvironment(working_dir=..., enabled_tools=[...]),
    )

    report = await evaluate(iter(tasks), config)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_tasks(tasks: list[dict[str, Any]] | Path | str) -> list[dict[str, Any]]:
    """Load tasks from list, Path, or string path.

    Supports:
    - list[dict]: Pass through directly
    - Path or str: Load from JSON file

    Returns the raw task list without normalization. Each task is a dict
    with whatever schema the user defines. The prepare_messages function
    is responsible for extracting the fields it needs.

    Example tasks.json:
        [
            {"problem_id": 0, "lang": "hip", "task": "GEMM", "ref_kernel": "..."},
            {"problem_id": 1, "lang": "cuda", "task": "swiglu", "ref_kernel": "..."},
        ]
    """
    if isinstance(tasks, list):
        return tasks

    path = Path(tasks)
    with open(path) as f:
        return json.load(f)
