"""Composable scoring utilities.

Score functions can be composed using llm_judge() and compose_scores().

Usage:
    from wafer_core.rollouts.scoring import llm_judge, compose_scores

    # Just LLM judge
    score_fn = llm_judge(JUDGE_PROMPT)

    # Composed: LLM judge + custom metric
    score_fn = compose_scores(
        llm_judge(JUDGE_PROMPT, weight=0.7),
        my_speedup_scorer(weight=0.3),
    )

    run_simple_eval(
        score_fn=score_fn,
        ...
    )
"""

from __future__ import annotations

import json
import logging
import os
from collections.abc import Awaitable, Callable
from typing import Any

from wafer_core.rollouts.dtypes import Metric, Score
from wafer_core.rollouts.training.types import Sample

# Type alias for score functions
ScoreFn = Callable[[Sample], Awaitable[Score]]

logger = logging.getLogger(__name__)


def _format_content_block(block: Any) -> str | None:
    """Format a single content block to text."""
    if hasattr(block, "text"):
        return block.text

    if hasattr(block, "type") and block.type == "toolCall":
        name = getattr(block, "name", "unknown")
        args = getattr(block, "arguments", {})
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except json.JSONDecodeError:
                pass
        args_str = json.dumps(args, indent=2) if isinstance(args, dict) else str(args)
        return f"[Tool Call: {name}]\n{args_str}"

    if isinstance(block, dict):
        if block.get("type") == "text":
            return block.get("text", "")
        if block.get("type") == "toolCall":
            name = block.get("name", "unknown")
            args = block.get("arguments", {})
            args_str = json.dumps(args, indent=2) if isinstance(args, dict) else str(args)
            return f"[Tool Call: {name}]\n{args_str}"

    return None


def _format_message_content(content: Any) -> str:
    """Format message content (string or list of blocks) to text."""
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        text_parts = [_format_content_block(block) for block in content]
        return "\n".join(t for t in text_parts if t)

    return str(content) if content else ""


def format_trajectory_for_judge(trajectory: Any) -> str:
    """Format trajectory messages into readable text for the judge.

    Args:
        trajectory: Trajectory object with messages attribute

    Returns:
        Formatted string showing the conversation flow
    """
    if not trajectory or not trajectory.messages:
        return ""

    parts = []
    for msg in trajectory.messages:
        role = msg.role

        if role == "system":
            continue

        text = _format_message_content(msg.content)
        if not text.strip():
            continue

        if role == "user":
            parts.append(f"USER: {text}")
        elif role == "assistant":
            parts.append(f"ASSISTANT: {text}")
        elif role == "tool":
            if len(text) > 1500:
                text = text[:1500] + "\n... [truncated]"
            parts.append(f"TOOL RESULT: {text}")

    return "\n\n".join(parts)


async def score_with_llm_judge(
    prompt_template: str,
    user_prompt: str,
    expected_answer: str,
    agent_response: str,
    model: str = "claude-sonnet-4-20250514",
    api_key: str | None = None,
) -> dict[str, Any]:
    """Score agent response using LLM-as-judge.

    Args:
        prompt_template: Template with {user_prompt}, {expected_answer}, {agent_response} placeholders
        user_prompt: The original user question
        expected_answer: The gold standard answer
        agent_response: The agent's response to evaluate
        model: Model to use for judging
        api_key: API key (defaults to env var)

    Returns:
        {"score": float (0-10), "reasoning": str, "raw_response": str}
    """
    if not api_key:
        api_key = os.environ.get("WAFER_ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")

    if not api_key:
        logger.warning("No API key for LLM judge, returning default score")
        return {"score": 0.0, "reasoning": "No API key available", "raw_response": ""}

    if not agent_response or not agent_response.strip():
        return {"score": 0.0, "reasoning": "Agent produced no response", "raw_response": ""}

    prompt = prompt_template.format(
        user_prompt=user_prompt,
        expected_answer=expected_answer,
        agent_response=agent_response,
    )

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=model,
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}],
        )

        raw_response = response.content[0].text

        # Parse JSON from response
        text = raw_response.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

        try:
            result = json.loads(text)
            return {
                "score": float(result.get("score", 0)),
                "reasoning": result.get("reasoning", ""),
                "raw_response": raw_response,
            }
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse judge response as JSON: {raw_response[:200]}")
            return {
                "score": 0.0,
                "reasoning": f"Parse error: {raw_response[:200]}",
                "raw_response": raw_response,
            }

    except Exception as e:
        logger.exception(f"LLM judge error: {e}")
        return {"score": 0.0, "reasoning": f"Judge error: {e}", "raw_response": ""}


# ──────────────────────── Composable Score Functions ─────────────────────────


def llm_judge(
    prompt_template: str,
    weight: float = 1.0,
    model: str = "claude-sonnet-4-20250514",
) -> ScoreFn:
    """Create a score function that uses LLM-as-judge.

    Args:
        prompt_template: Template with {user_prompt}, {expected_answer}, {agent_response}
        weight: Weight for the judge_score metric (default 1.0)
        model: Model to use for judging

    Returns:
        Score function that can be passed to run_simple_eval() or composed

    Example:
        score_fn = llm_judge('''
            Score 0-10:
            Question: {user_prompt}
            Expected: {expected_answer}
            Response: {agent_response}
            Output JSON: {{"score": <0-10>, "reasoning": "..."}}
        ''')
    """

    async def score_fn(sample: Sample) -> Score:
        agent_response = format_trajectory_for_judge(sample.trajectory)
        expected_answer = sample.input.get("expected_answer", "")
        user_prompt = sample.input.get("user_prompt", "")

        metrics: list[Metric] = []

        if expected_answer and agent_response:
            result = await score_with_llm_judge(
                prompt_template=prompt_template,
                user_prompt=user_prompt,
                expected_answer=expected_answer,
                agent_response=agent_response,
                model=model,
            )
            metrics.extend([
                Metric(
                    name="judge_score",
                    value=result["score"] / 10.0,
                    weight=weight,
                    metadata={
                        "reasoning": result.get("reasoning", ""),
                        "raw_response": result.get("raw_response", ""),
                    },
                ),
                Metric(name="judge_score_raw", value=result["score"], weight=0.0),
            ])
        else:
            metrics.append(Metric(name="judge_score", value=0.0, weight=weight))

        metrics.append(
            Metric(name="has_response", value=1.0 if agent_response else 0.0, weight=0.0)
        )

        return Score(metrics=tuple(metrics))

    return score_fn


def compose_scores(*scorers: ScoreFn) -> ScoreFn:
    """Compose multiple score functions into one.

    Runs all scorers and combines their metrics. Weights are preserved
    from each scorer's metrics.

    Args:
        *scorers: Score functions to compose

    Returns:
        Combined score function

    Example:
        score_fn = compose_scores(
            llm_judge(JUDGE_PROMPT, weight=0.7),
            my_speedup_scorer(weight=0.3),
        )
    """

    async def combined_score_fn(sample: Sample) -> Score:
        all_metrics: list[Metric] = []

        for scorer in scorers:
            score = await scorer(sample)
            all_metrics.extend(score.metrics)

        return Score(metrics=tuple(all_metrics))

    return combined_score_fn
