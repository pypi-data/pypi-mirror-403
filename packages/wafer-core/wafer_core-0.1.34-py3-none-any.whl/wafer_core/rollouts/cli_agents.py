"""CLI Agent Adapter for Evaluation.

Runs CLI agents (Claude Code, Codex, Cursor) as subprocess and parses their output
into Trajectory format compatible with the existing evaluation framework.

Usage:
    # Direct evaluation
    trajectory = await run_cli_agent("claude-code", instruction, working_dir)
    sample = Sample(id="test", input=data, trajectory=trajectory)
    score = score_fn(sample)

    # With existing evaluate() infrastructure
    results = await evaluate_cli_agents(
        agents=["claude-code", "codex"],
        dataset=problems,
        working_dir=kernels_dir,
        score_fn=my_score_fn,
    )
"""

from __future__ import annotations

import json
import logging
import shlex
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

import trio

from .dtypes import (
    Message,
    Score,
    TextContent,
    ToolCallContent,
    Trajectory,
)
from .training.types import Sample

logger = logging.getLogger(__name__)

# ── Types ─────────────────────────────────────────────────────────────────────

AgentName = Literal["claude-code", "codex", "cursor"]


@dataclass(frozen=True)
class CLIAgentConfig:
    """Configuration for CLI agent execution.

    Frozen dataclass: immutable, serializable, explicit.
    """

    agent: AgentName
    model: str | None = None  # Override model if agent supports it
    timeout_sec: float = 600.0
    allowed_tools: list[str] | None = None  # Agent-specific tool restrictions
    extra_args: list[str] = field(default_factory=list)  # Additional CLI flags


@dataclass(frozen=True)
class CLIAgentResult:
    """Result of running a CLI agent.

    Frozen dataclass: all fields explicit, immutable after creation.
    """

    trajectory: Trajectory
    raw_output: str
    duration_sec: float
    exit_code: int
    error: str | None = None


# ── Parsing Functions (Pure) ──────────────────────────────────────────────────


def parse_claude_code_stream_json(output: str) -> list[Message]:
    """Parse Claude Code --output-format stream-json into list[Message].

    Claude Code emits NDJSON with event types:
    - {"type": "system", "subtype": "init", ...}
    - {"type": "assistant", "message": {"content": [...]}}
    - {"type": "user", "message": {"content": [{"type": "tool_result", ...}]}}
    - {"type": "result", "subtype": "success", ...}

    Pure function: no side effects, explicit input/output.
    """
    assert isinstance(output, str)

    messages: list[Message] = []

    for line in output.strip().split("\n"):
        if not line.strip():
            continue

        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            # Skip non-JSON lines (stderr, logs, etc.)
            continue

        event_type = event.get("type")

        if event_type == "assistant":
            content_blocks = _parse_claude_content_blocks(event)
            if content_blocks:
                messages.append(Message(role="assistant", content=content_blocks))

        elif event_type == "user":
            # Tool results come as user messages
            tool_messages = _parse_claude_tool_results(event)
            messages.extend(tool_messages)

    return messages


def _parse_claude_content_blocks(event: dict[str, Any]) -> list[TextContent | ToolCallContent]:
    """Parse content blocks from Claude Code assistant message.

    Pure function: extracts TextContent and ToolCallContent from event.
    """
    assert "message" in event
    assert "content" in event["message"]

    content_blocks: list[TextContent | ToolCallContent] = []
    raw_content = event["message"]["content"]

    for block in raw_content:
        block_type = block.get("type")

        if block_type == "text":
            content_blocks.append(TextContent(text=block.get("text", "")))

        elif block_type == "tool_use":
            content_blocks.append(
                ToolCallContent(
                    id=block.get("id", ""),
                    name=block.get("name", ""),
                    arguments=block.get("input", {}),
                )
            )

    return content_blocks


def _parse_claude_tool_results(event: dict[str, Any]) -> list[Message]:
    """Parse tool results from Claude Code user message.

    Pure function: extracts tool result messages.
    """
    assert "message" in event
    assert "content" in event["message"]

    messages: list[Message] = []
    raw_content = event["message"]["content"]

    for block in raw_content:
        if block.get("type") == "tool_result":
            messages.append(
                Message(
                    role="tool",
                    content=block.get("content", ""),
                    tool_call_id=block.get("tool_use_id", ""),
                )
            )

    return messages


def parse_codex_json(output: str) -> list[Message]:
    """Parse Codex --json output into list[Message].

    Codex emits NDJSON events. Structure is similar to Claude Code.

    Pure function: no side effects, explicit input/output.
    """
    assert isinstance(output, str)

    messages: list[Message] = []

    for line in output.strip().split("\n"):
        if not line.strip():
            continue

        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue

        event_type = event.get("type")

        if event_type == "message" and event.get("role") == "assistant":
            # Codex assistant message
            content = event.get("content", "")
            if content:
                messages.append(Message(role="assistant", content=content))

        elif event_type == "function_call":
            # Codex tool call
            messages.append(
                Message(
                    role="assistant",
                    content=[
                        ToolCallContent(
                            id=event.get("id", ""),
                            name=event.get("name", ""),
                            arguments=event.get("arguments", {}),
                        )
                    ],
                )
            )

        elif event_type == "function_result":
            # Codex tool result
            messages.append(
                Message(
                    role="tool",
                    content=event.get("output", ""),
                    tool_call_id=event.get("call_id", ""),
                )
            )

    return messages


def parse_cursor_stream_json(output: str) -> list[Message]:
    """Parse Cursor CLI --output-format stream-json into list[Message].

    Cursor emits NDJSON similar to Claude Code:
    - {"type": "assistant", "message": {"content": [...]}}
    - {"type": "tool_call", "subtype": "started|completed", ...}

    Pure function: no side effects, explicit input/output.
    """
    assert isinstance(output, str)

    messages: list[Message] = []

    for line in output.strip().split("\n"):
        if not line.strip():
            continue

        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue

        event_type = event.get("type")

        if event_type == "assistant":
            # Parse same as Claude Code
            content_blocks = _parse_claude_content_blocks(event)
            if content_blocks:
                messages.append(Message(role="assistant", content=content_blocks))

        elif event_type == "tool_call":
            subtype = event.get("subtype")

            if subtype == "completed":
                # Tool execution finished
                tool_id = event.get("id", "")
                output_content = event.get("output", "")
                messages.append(
                    Message(
                        role="tool",
                        content=output_content,
                        tool_call_id=tool_id,
                    )
                )

    return messages


def parse_raw_text_fallback(output: str) -> list[Message]:
    """Fallback parser: treat entire output as single assistant message.

    Used when agent doesn't support structured output.

    Pure function: simple transformation.
    """
    assert isinstance(output, str)

    if not output.strip():
        return []

    return [Message(role="assistant", content=output.strip())]


# ── Command Building (Pure) ───────────────────────────────────────────────────


def build_cli_command(config: CLIAgentConfig, instruction: str) -> list[str]:
    """Build CLI command for the specified agent.

    Pure function: config + instruction -> command list.
    """
    assert config is not None
    assert instruction is not None
    assert len(instruction) > 0

    if config.agent == "claude-code":
        return _build_claude_code_command(config, instruction)
    elif config.agent == "codex":
        return _build_codex_command(config, instruction)
    elif config.agent == "cursor":
        return _build_cursor_command(config, instruction)
    else:
        raise ValueError(f"Unknown agent: {config.agent}")


def _build_claude_code_command(config: CLIAgentConfig, instruction: str) -> list[str]:
    """Build Claude Code CLI command.

    claude -p "instruction" --output-format stream-json --verbose [--allowedTools ...]
    """
    cmd = [
        "claude",
        "-p",
        instruction,
        "--output-format",
        "stream-json",
        "--verbose",  # Required for stream-json with --print
    ]

    if config.allowed_tools:
        cmd.extend(["--allowedTools", ",".join(config.allowed_tools)])

    if config.model:
        cmd.extend(["--model", config.model])

    cmd.extend(config.extra_args)

    return cmd


def _build_codex_command(config: CLIAgentConfig, instruction: str) -> list[str]:
    """Build Codex CLI command.

    codex exec --json --sandbox danger-full-access -- "instruction"
    """
    cmd = [
        "codex",
        "exec",
        "--json",
        "--sandbox",
        "danger-full-access",
        "--skip-git-repo-check",
    ]

    if config.model:
        cmd.extend(["--model", config.model])

    cmd.extend(config.extra_args)
    cmd.extend(["--", instruction])

    return cmd


def _build_cursor_command(config: CLIAgentConfig, instruction: str) -> list[str]:
    """Build Cursor CLI command.

    cursor -p "instruction" --output-format stream-json
    """
    cmd = [
        "cursor",
        "-p",
        instruction,
        "--output-format",
        "stream-json",
    ]

    if config.model:
        cmd.extend(["--model", config.model])

    cmd.extend(config.extra_args)

    return cmd


# ── Agent Execution ───────────────────────────────────────────────────────────


async def run_cli_agent(
    config: CLIAgentConfig,
    instruction: str,
    working_dir: Path,
) -> CLIAgentResult:
    """Run CLI agent and return structured result.

    Args:
        config: Agent configuration (agent name, model, timeout)
        instruction: Task instruction for the agent
        working_dir: Directory where agent will execute

    Returns:
        CLIAgentResult with trajectory, raw output, timing, exit code
    """
    assert config is not None
    assert instruction is not None
    assert len(instruction) > 0
    assert working_dir.exists()  # noqa: ASYNC240 - sync assertion before async work
    assert working_dir.is_dir()  # noqa: ASYNC240 - sync assertion before async work

    cmd = build_cli_command(config, instruction)
    logger.info(f"Running {config.agent}: {shlex.join(cmd[:5])}...")

    start_time = time.perf_counter()

    try:
        # Run with timeout
        with trio.move_on_after(config.timeout_sec) as cancel_scope:
            result = await trio.run_process(
                cmd,
                cwd=working_dir,
                capture_stdout=True,
                capture_stderr=True,
                check=False,  # Don't raise on non-zero exit
            )

        if cancel_scope.cancelled_caught:
            duration_sec = time.perf_counter() - start_time
            return CLIAgentResult(
                trajectory=Trajectory(messages=[]),
                raw_output="",
                duration_sec=duration_sec,
                exit_code=-1,
                error=f"Timeout after {config.timeout_sec}s",
            )

        duration_sec = time.perf_counter() - start_time
        raw_output = result.stdout.decode("utf-8", errors="replace")
        stderr = result.stderr.decode("utf-8", errors="replace")

        # Parse output based on agent
        messages = _parse_agent_output(config.agent, raw_output)

        # Check for errors
        error = None
        if result.returncode != 0:
            error = f"Exit code {result.returncode}: {stderr[:500]}"

        return CLIAgentResult(
            trajectory=Trajectory(messages=messages),
            raw_output=raw_output,
            duration_sec=duration_sec,
            exit_code=result.returncode,
            error=error,
        )

    except FileNotFoundError:
        duration_sec = time.perf_counter() - start_time
        return CLIAgentResult(
            trajectory=Trajectory(messages=[]),
            raw_output="",
            duration_sec=duration_sec,
            exit_code=-1,
            error=f"Agent not found: {config.agent}. Is it installed?",
        )

    except Exception as e:
        duration_sec = time.perf_counter() - start_time
        return CLIAgentResult(
            trajectory=Trajectory(messages=[]),
            raw_output="",
            duration_sec=duration_sec,
            exit_code=-1,
            error=f"Execution failed: {type(e).__name__}: {e}",
        )


def _parse_agent_output(agent: AgentName, output: str) -> list[Message]:
    """Route to appropriate parser based on agent.

    Pure function: dispatches to agent-specific parser.
    """
    assert agent in ("claude-code", "codex", "cursor")

    if agent == "claude-code":
        messages = parse_claude_code_stream_json(output)
    elif agent == "codex":
        messages = parse_codex_json(output)
    elif agent == "cursor":
        messages = parse_cursor_stream_json(output)
    else:
        messages = parse_raw_text_fallback(output)

    # Fallback if parsing found nothing
    if not messages and output.strip():
        messages = parse_raw_text_fallback(output)

    return messages


# ── Evaluation Integration ────────────────────────────────────────────────────


async def evaluate_cli_agent_sample(
    config: CLIAgentConfig,
    sample_data: dict[str, Any],
    sample_id: str,
    working_dir: Path,
    build_instruction: Callable[[dict[str, Any]], str],
    score_fn: Callable[[Sample], Score],
) -> Sample:
    """Evaluate a single sample with a CLI agent.

    Drop-in replacement for evaluate_sample() but uses CLI agent instead of LLM API.

    Args:
        config: CLI agent configuration
        sample_data: Raw sample data (problem definition)
        sample_id: Unique identifier for this sample
        working_dir: Directory where agent executes
        build_instruction: Function that builds instruction from sample_data
        score_fn: Scoring function (Sample -> Score)

    Returns:
        Sample with trajectory, score, and metadata
    """
    assert config is not None
    assert sample_data is not None
    assert sample_id is not None
    assert working_dir.exists()  # noqa: ASYNC240 - sync assertion before async work

    # Build instruction from sample data
    instruction = build_instruction(sample_data)
    assert instruction is not None
    assert len(instruction) > 0

    # Run CLI agent
    result = await run_cli_agent(config, instruction, working_dir)

    # Build sample
    sample = Sample(
        id=sample_id,
        input=sample_data,
        trajectory=result.trajectory,
        ground_truth=sample_data.get("expected_answer") or sample_data.get("ground_truth"),
        metadata={
            "agent": config.agent,
            "model": config.model,
            "duration_sec": result.duration_sec,
            "exit_code": result.exit_code,
            "error": result.error,
            "status": "success" if result.error is None else "failed",
        },
    )

    # Compute score
    import inspect

    score_result = score_fn(sample)
    if inspect.iscoroutine(score_result):
        score = await score_result
    else:
        score = score_result

    sample.score = score
    sample.reward = score.reward if score else 0.0

    return sample


async def evaluate_cli_agents(
    configs: list[CLIAgentConfig],
    dataset: list[dict[str, Any]],
    working_dir: Path,
    build_instruction: Callable[[dict[str, Any]], str],
    score_fn: Callable[[Sample], Score],
    max_concurrent: int = 4,
) -> dict[str, list[Sample]]:
    """Evaluate multiple CLI agents on a dataset.

    Runs all (agent, sample) pairs with concurrency control.

    Args:
        configs: List of CLI agent configurations to evaluate
        dataset: List of sample data dicts
        working_dir: Base directory for agent execution
        build_instruction: Function that builds instruction from sample_data
        score_fn: Scoring function (Sample -> Score)
        max_concurrent: Max concurrent agent executions

    Returns:
        Dict mapping agent name to list of Sample results
    """
    assert configs is not None
    assert len(configs) > 0
    assert dataset is not None
    assert len(dataset) > 0
    assert working_dir.exists()  # noqa: ASYNC240 - sync assertion before async work
    assert max_concurrent > 0

    results: dict[str, list[Sample]] = {cfg.agent: [] for cfg in configs}
    limiter = trio.CapacityLimiter(max_concurrent)

    async def run_one(
        config: CLIAgentConfig,
        sample_data: dict[str, Any],
        sample_idx: int,
    ) -> tuple[str, Sample]:
        async with limiter:
            sample_id = f"{config.agent}_{sample_idx:04d}"

            # Create isolated working dir for each run
            sample_dir = working_dir / sample_id
            sample_dir.mkdir(parents=True, exist_ok=True)

            sample = await evaluate_cli_agent_sample(
                config=config,
                sample_data=sample_data,
                sample_id=sample_id,
                working_dir=sample_dir,
                build_instruction=build_instruction,
                score_fn=score_fn,
            )

            return config.agent, sample

    async with trio.open_nursery() as nursery:
        for config in configs:
            for idx, sample_data in enumerate(dataset):

                async def task(
                    c: CLIAgentConfig = config,
                    s: dict[str, Any] = sample_data,
                    i: int = idx,
                ) -> None:
                    agent_name, sample = await run_one(c, s, i)
                    results[agent_name].append(sample)

                nursery.start_soon(task)

    return results


# ── Convenience Functions ─────────────────────────────────────────────────────


def trajectory_to_text(trajectory: Trajectory) -> str:
    """Convert trajectory to human-readable text.

    Useful for logging and debugging.

    Pure function: trajectory -> string.
    """
    assert trajectory is not None

    lines = []

    for msg in trajectory.messages:
        role = msg.role.upper()

        if isinstance(msg.content, str):
            lines.append(f"[{role}]\n{msg.content}\n")
        elif isinstance(msg.content, list):
            parts = []
            for block in msg.content:
                if isinstance(block, TextContent):
                    parts.append(block.text)
                elif isinstance(block, ToolCallContent):
                    parts.append(f"[TOOL: {block.name}({json.dumps(block.arguments)})]")
            lines.append(f"[{role}]\n{''.join(parts)}\n")
        else:
            lines.append(f"[{role}]\n{msg.content}\n")

    return "\n".join(lines)
