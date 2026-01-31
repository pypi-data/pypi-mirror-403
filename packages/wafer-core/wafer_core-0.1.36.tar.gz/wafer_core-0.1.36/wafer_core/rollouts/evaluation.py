"""Composable evaluation framework with first-class rewards.

Design mirrors run_agent/run_agent_step for easy parallelization.
Tiger Style: Pure functions, explicit configuration, no hidden state.
"""

import json
import logging
import re
import sys
import time
from collections.abc import Callable, Iterator
from dataclasses import asdict, dataclass, field, replace
from datetime import datetime
from pathlib import Path
from typing import Any

import trio

from .agents import run_agent
from .dtypes import (
    Actor,
    AgentState,
    Environment,
    EvalConfig,
    LLMCallEnd,
    Metric,
    RunConfig,
    Score,
    StopReason,
    StreamChunk,
    TextEnd,
    ToolExecutionEnd,
    Trajectory,
)
from .events import EventEmitter, emit_event
from .progress import MultiProgress
from .training.types import Sample, Status

logger = logging.getLogger(__name__)


# ── Runtime Context ───────────────────────────────────────────────────────────


@dataclass
class EvalRuntime:
    """Runtime context for evaluation execution.

    Bundles EvalConfig with instantiated handles (limiters, progress).
    Config stays pure/serializable; runtime holds live execution state.

    Created once in evaluate(), passed to all evaluate_sample() calls.
    """

    config: EvalConfig
    api_limiter: trio.CapacityLimiter | None = None
    tool_limiter: trio.CapacityLimiter | None = None
    progress: MultiProgress | None = None


# JSON-like recursive type for sanitize_api_keys
# Using string literals for forward references to avoid import cycle
JsonValue = dict[str, "JsonValue"] | list["JsonValue"] | str | int | float | bool | None


# ── Progress Helpers ──────────────────────────────────────────────────────────


def _get_progress_status_for_event(event: object) -> str | None:
    """Extract progress status string from a streaming event.

    Returns status string to display, or None if event doesn't affect status.
    Pure function - no side effects.
    """
    # Handle StreamChunk events (turn lifecycle, modal progress)
    if isinstance(event, StreamChunk):
        if event.type == "turn_start":
            return "waiting..."
        elif event.type == "turn_end":
            return ""  # Clear status
        elif event.type == "modal_progress":
            phase = event.data.get("phase", "")
            return {
                "importing": "importing...",
                "compiling": "compiling...",
                "correctness": "checking...",
                "performance": "benchmarking...",
            }.get(phase, phase)
        return None

    # Handle streaming events from LLM (generic - works with any tool names)
    event_type = getattr(event, "type", "")

    # Semaphore/concurrency visibility - distinguish queue wait from API wait
    if event_type == "semaphore_wait_start":
        limiter_type = getattr(event, "limiter_type", "")
        if limiter_type == "api":
            return "queued (api)..."
        elif limiter_type == "tool":
            return "queued (tool)..."
        return "queued..."
    elif event_type == "semaphore_acquired":
        # After acquiring semaphore, status will be updated by next event (LLMCallStart)
        return None
    elif event_type == "llm_call_start":
        return "calling api..."

    if event_type == "start":
        return "streaming..."
    elif event_type == "text_delta":
        return "streaming..."
    elif event_type == "thinking_start":
        return "thinking..."
    elif event_type == "thinking_delta":
        return "thinking..."
    elif event_type == "toolcall_start":
        tool_name = getattr(event, "name", "tool")
        # Truncate long tool names for display
        short_name = tool_name[:12] + "…" if len(tool_name) > 12 else tool_name
        return f"calling {short_name}..."
    elif event_type == "tool_execution_start":
        tool_name = getattr(event, "tool_name", "tool")
        short_name = tool_name[:12] + "…" if len(tool_name) > 12 else tool_name
        return f"→ {short_name}..."
    elif event_type == "tool_result":
        is_error = getattr(event, "is_error", False)
        if is_error:
            return "tool error"
    return None


def _get_turn_from_event(event: object) -> int | None:
    """Extract turn number from event if applicable."""
    if isinstance(event, StreamChunk):
        if event.type == "turn_start":
            return event.data.get("turn", 0)
        elif event.type == "turn_end":
            return event.data.get("turn", 0) + 1
    return None


def _wrap_event_with_sample_id(event: object, sample_id: str) -> StreamChunk:
    """Wrap event with sample_id for concurrent sample tracking."""
    if isinstance(event, StreamChunk):
        return StreamChunk(
            type=event.type,
            data={**event.data, "sample_id": sample_id},
            timestamp=event.timestamp,
        )
    else:
        return StreamChunk(
            type="event_wrapper",
            data={"sample_id": sample_id, "event": event},
        )


def _extract_text_from_content(content: object) -> str:
    """Extract text from message content (str or list of ContentBlocks)."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        texts = []
        for block in content:
            if hasattr(block, "text"):
                texts.append(block.text)
            elif hasattr(block, "content"):
                texts.append(str(block.content))
        return "\n".join(texts) if texts else ""
    return str(content) if content else ""


async def _evaluate_batch(
    samples: list[tuple[str, dict[str, Any]]],
    runtime: EvalRuntime,
    on_sample_complete: Callable[[Sample, list[Sample]], None] | None = None,
) -> list[Sample]:
    """Evaluate a batch of samples, handling sequential vs parallel execution.

    This is the core evaluation loop, used for both initial runs and retries.

    Args:
        samples: List of (sample_id, sample_data) tuples to evaluate
        runtime: Runtime context with config and limiters
        on_sample_complete: Optional callback called after each sample completes.
                           Receives (completed_sample, all_results_so_far).
                           Used for incremental report writing.
    """
    config = runtime.config
    progress = runtime.progress
    results: list[Sample] = []
    # Lock for thread-safe results access during concurrent execution
    results_lock = trio.Lock()

    async def run_one(sample_id: str, sample_data: dict[str, Any]) -> Sample:
        """Evaluate a single sample."""
        task_name = sample_data.get("name", sample_id)
        if progress:
            progress.add_task(sample_id, name=task_name)

        # Get environment: prefer direct environment, fall back to factory
        if config.environment is not None:
            env = config.environment
        elif config.environment_factory is not None:
            env = await config.environment_factory(sample_data)
        else:
            env = None
        result = await evaluate_sample(
            sample_data=sample_data,
            sample_id=sample_id,
            runtime=runtime,
            environment=env,
        )

        # Mark task complete
        if progress:
            reward = result.score.reward if result.score else 0.0
            success = result.metadata.get("status") == "success"
            if success:
                message = f"reward={reward:.2f}"
            else:
                error = result.metadata.get("error", "failed")
                message = error[:30] if len(error) > 30 else error
            progress.complete_task(sample_id, success=success, message=message)

        return result

    if config.max_concurrent == 1:
        # Sequential
        for sample_id, sample_data in samples:
            result = await run_one(sample_id, sample_data)
            results.append(result)
            if on_sample_complete:
                on_sample_complete(result, results)
    else:
        # Parallel
        async with trio.open_nursery() as nursery:
            limiter = trio.CapacityLimiter(config.max_concurrent)

            async def run_with_limit(sid: str, sdata: dict[str, Any]) -> None:
                async with limiter:
                    result = await run_one(sid, sdata)
                    async with results_lock:
                        results.append(result)
                        if on_sample_complete:
                            on_sample_complete(result, results)

            for sample_id, sample_data in samples:
                nursery.start_soon(run_with_limit, sample_id, sample_data)

    return results


async def _compute_score(score_fn: Callable[..., Any], sample: Sample) -> Score:
    """Compute score, handling both sync and async score functions."""
    import inspect
    from typing import cast

    try:
        score_result = score_fn(sample)
        if inspect.iscoroutine(score_result):
            return await score_result
        else:
            return cast(Score, score_result)
    except Exception as e:
        logger.exception(f"❌ SCORE COMPUTATION FAILED: {e}")
        return Score(metrics=(Metric("error", 0.0, weight=1.0, metadata={"error": str(e)}),))


def _log_sample_completion(
    sample_id: str,
    reward: float,
    exec_metadata: dict[str, Any],
    final_trajectory: Trajectory,
    score: Score | None,
    verbose: bool,
) -> None:
    """Log sample completion with structured logging and rollout record."""
    duration_seconds = exec_metadata.get("duration_seconds", 0.0)

    logger.info(
        f"Sample {sample_id} completed: reward={reward:.3f}, "
        f"turns={exec_metadata['turns_used']}, duration={duration_seconds:.2f}s, "
        f"status={exec_metadata['status']}",
        extra={
            "sample_id": sample_id,
            "reward": reward,
            "turns": exec_metadata["turns_used"],
            "duration_seconds": duration_seconds,
            "status": exec_metadata["status"],
            "stop_reason": exec_metadata.get("stop_reason"),
        },
    )

    # Emit rollout record for TUI trace viewer (matches grpo.py format)
    messages = [
        {"role": m.role, "content": _extract_text_from_content(m.content)}
        for m in final_trajectory.messages
    ]
    logger.info(
        "rollout",
        extra={
            "step": sample_id,
            "prompt": messages[0]["content"] if messages else "",
            "response": messages[-1]["content"] if len(messages) > 1 else "",
            "reward": reward,
            "status": exec_metadata["status"],
            "turns": exec_metadata["turns_used"],
            "stop_reason": exec_metadata.get("stop_reason"),
            "messages": messages,
        },
    )

    if verbose and score:
        metric_str = ", ".join(f"{m.name}={m.value:.3f}" for m in score.metrics[:3])
        logger.info(f"  {metric_str}")


def _build_base_run_config(
    config: "EvalConfig",
    api_limiter: trio.CapacityLimiter | None,
    tool_limiter: trio.CapacityLimiter | None,
) -> RunConfig:
    """Build the base RunConfig from EvalConfig.

    Handles:
    - Using user-provided run_config or creating default
    - Setting up on_chunk handler (streaming vs silent)
    - Injecting concurrency limiters
    """
    show_turn_progress = config.show_progress and config.max_concurrent == 1

    if config.run_config:
        base_run_config = replace(config.run_config, show_progress=show_turn_progress)
    else:
        # Determine on_chunk handler based on stream_tokens flag
        has_stream_tokens = hasattr(config, "stream_tokens")
        stream_tokens_value = getattr(config, "stream_tokens", None)
        logger.debug(
            f"🔍 Checking stream_tokens: hasattr={has_stream_tokens}, value={stream_tokens_value}"
        )

        if has_stream_tokens and stream_tokens_value:
            from .agents import stdout_handler

            on_chunk_handler = stdout_handler
            logger.debug("🔍 Using stdout_handler for token streaming")
        else:

            async def silent_chunk_handler(_: object) -> None:
                await trio.lowlevel.checkpoint()

            on_chunk_handler = silent_chunk_handler
            logger.debug("🔍 Using silent mode (no token streaming)")

        base_run_config = RunConfig(on_chunk=on_chunk_handler, show_progress=show_turn_progress)
        logger.debug(
            f"🔍 RunConfig.on_chunk: {on_chunk_handler.__name__ if hasattr(on_chunk_handler, '__name__') else type(on_chunk_handler)}"
        )

    # Inject two-level concurrency limiters if provided
    if api_limiter is not None or tool_limiter is not None:
        base_run_config = replace(
            base_run_config,
            api_limiter=api_limiter,
            tool_limiter=tool_limiter,
        )

    return base_run_config


# EvalSample deleted - use Sample from training.types instead


def get_config_path(file_path: str) -> str | None:
    """Get config file path relative to git repository root.

    Args:
        file_path: Absolute or relative path to config file (usually __file__)

    Returns:
        Path relative to git root, or None if not in a git repo
    """
    import subprocess
    from pathlib import Path

    try:
        # Get git root
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            return None

        git_root = Path(result.stdout.strip())
        config_abs = Path(file_path).resolve()

        # Get relative path from git root
        try:
            return str(config_abs.relative_to(git_root))
        except ValueError:
            # Config file is outside git repo
            return None

    except Exception:
        return None


def _get_git_info() -> dict[str, Any]:
    """Get git repository info for reproducibility.

    Returns dict with:
        commit: Current commit hash (short)
        branch: Current branch name
        dirty: Whether working directory has uncommitted changes
        commit_full: Full commit hash
    """
    import subprocess

    info: dict[str, Any] = {
        "commit": None,
        "branch": None,
        "dirty": None,
        "commit_full": None,
    }

    try:
        # Get commit hash
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            info["commit_full"] = result.stdout.strip()
            info["commit"] = info["commit_full"][:8]

        # Get branch name
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            info["branch"] = result.stdout.strip()

        # Check if dirty
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            info["dirty"] = len(result.stdout.strip()) > 0

    except Exception:
        pass  # Git info is best-effort

    return info


# ── Sample to Markdown ────────────────────────────────────────────────────────

# Regex to strip ANSI escape codes
_ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*m|\x1b\[m")


def _strip_ansi(text: str) -> str:
    """Strip ANSI escape codes from text."""
    return _ANSI_ESCAPE.sub("", text)


def _truncate(text: str, max_len: int = 2000) -> str:
    """Truncate long text and strip ANSI codes."""
    text = _strip_ansi(text)
    if len(text) <= max_len:
        return text
    return text[:max_len] + f"\n\n... (truncated, {len(text)} chars total)"


def _format_message_content(content: Any) -> str:
    """Format message content (string or list of blocks)."""
    if isinstance(content, str):
        return content

    parts = []
    for block in content:
        if isinstance(block, dict):
            if block.get("type") == "text":
                parts.append(block.get("text", ""))
            elif block.get("type") == "toolCall":
                name = block.get("name", "unknown")
                args = block.get("arguments", {})
                args_str = json.dumps(args, indent=2)
                parts.append(f"**Tool Call: `{name}`**\n```json\n{args_str}\n```")
        elif hasattr(block, "type"):
            if block.type == "text":
                parts.append(block.text)
            elif block.type == "toolCall":
                args_str = json.dumps(block.arguments, indent=2)
                parts.append(f"**Tool Call: `{block.name}`**\n```json\n{args_str}\n```")

    return "\n\n".join(parts)


def sample_to_markdown(sample_dict: dict[str, Any]) -> str:
    """Convert sample dict to human-readable markdown.

    Args:
        sample_dict: Sample as dictionary (from sample.to_dict())

    Returns:
        Markdown string representation of the trajectory
    """
    lines = []

    # Header
    lines.append(f"# Trajectory: {sample_dict.get('id', 'unknown')}")
    lines.append("")

    # Input
    input_data = sample_dict.get("input", {})
    lines.append("## Input")
    if isinstance(input_data, dict):
        for key, value in input_data.items():
            if key in ("expected_answer", "metadata"):
                continue
            if isinstance(value, str) and len(value) > 200:
                value = _truncate(value, 200)
            lines.append(f"**{key}:** {value}")
    else:
        lines.append(str(input_data))
    lines.append("")

    # Score
    score = sample_dict.get("score", {})
    metric_metadata = []  # Collect any metrics with metadata
    if score:
        lines.append("## Score")
        metrics = score.get("metrics", [])
        for m in metrics:
            if isinstance(m, dict):
                name = m.get("name", "")
                value = m.get("value", 0)
                if isinstance(value, float):
                    lines.append(f"- **{name}:** {value:.3f}")
                else:
                    lines.append(f"- **{name}:** {value}")
                # Collect any non-empty metadata
                metadata = m.get("metadata", {})
                if metadata:
                    metric_metadata.append((name, metadata))
        lines.append("")

    # Metric metadata (reasoning, errors, etc.)
    for name, metadata in metric_metadata:
        lines.append(f"### {name} - Details")
        for key, value in metadata.items():
            if isinstance(value, str) and len(value) > 500:
                # Long strings get their own block
                lines.append(f"**{key}:**")
                lines.append(f"```\n{_truncate(value, 2000)}\n```")
            elif isinstance(value, str) and "\n" in value:
                # Multi-line strings
                lines.append(f"**{key}:**")
                lines.append(value)
            else:
                lines.append(f"**{key}:** {value}")
        lines.append("")

    # Trajectory
    trajectory = sample_dict.get("trajectory", {})
    messages = trajectory.get("messages", []) if trajectory else []

    if messages:
        lines.append("## Conversation")
        lines.append("")

        turn = 0
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")

            if role == "system":
                lines.append("### System Prompt")
                lines.append("```")
                lines.append(_truncate(content, 1000))
                lines.append("```")
                lines.append("")
            elif role == "user":
                lines.append("### User")
                lines.append(_truncate(content, 2000))
                lines.append("")
            elif role == "assistant":
                turn += 1
                lines.append(f"### Assistant (Turn {turn})")
                formatted = _format_message_content(content)
                lines.append(formatted)
                lines.append("")
            elif role == "tool":
                lines.append("### Tool Result")
                result_text = _truncate(content, 1500)
                lines.append(f"```\n{result_text}\n```")
                lines.append("")

    # Expected answer
    if isinstance(input_data, dict):
        expected = input_data.get("expected_answer", "")
        if expected:
            lines.append("## Expected Answer")
            lines.append(_truncate(expected, 2000))
            lines.append("")

    # Final response from environment state
    env_state = sample_dict.get("environment_state", {})
    if env_state:
        final = env_state.get("final_response", "")
        if final:
            lines.append("## Final Response (Captured)")
            lines.append(_strip_ansi(final))
            lines.append("")

    return "\n".join(lines)


@dataclass
class EvalReport:
    """Summary report for an evaluation run."""

    eval_name: str
    dataset_path: str
    total_samples: int
    summary_metrics: dict[str, float]
    sample_results: list[Sample]
    config: dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    git_info: dict[str, Any] = field(default_factory=_get_git_info)
    config_path: str | None = None  # Path to config file relative to repo root
    metadata: dict[str, Any] | None = None  # Custom metadata (waferbench_category, github_runner, etc.)

    async def save(self, output_dir: Path) -> None:
        """Save evaluation results to directory."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save individual samples (JSON + markdown)
        samples_dir = output_dir / "samples"
        samples_dir.mkdir(exist_ok=True)
        for sample in self.sample_results:
            sample_dict = sample.to_dict()
            sample_dict = sanitize_api_keys(sample_dict)

            # JSON
            sample_file = samples_dir / f"{sample.id}.json"
            sample_file.write_text(json.dumps(sample_dict, indent=2, default=str))

            # Markdown (human-readable)
            md_file = samples_dir / f"{sample.id}.md"
            md_file.write_text(sample_to_markdown(sample_dict))

        # Save summary report
        summary = {
            "eval_name": self.eval_name,
            "dataset_path": self.dataset_path,
            "total_samples": self.total_samples,
            "summary_metrics": self.summary_metrics,
            "config": self.config,
            "timestamp": self.timestamp,
            "git_info": self.git_info,
            "config_path": self.config_path,
            "sample_ids": [s.id for s in self.sample_results],
        }
        if self.metadata:
            summary["metadata"] = self.metadata
        # Sanitize API keys in the summary before saving
        summary = sanitize_api_keys(summary)
        report_file = output_dir / "report.json"
        report_file.write_text(json.dumps(summary, indent=2))

        # Save trajectories separately for easy loading
        trajectories_dir = output_dir / "trajectories"
        trajectories_dir.mkdir(exist_ok=True)
        for sample in self.sample_results:
            if sample.trajectory:
                traj_file = trajectories_dir / f"{sample.id}.jsonl"
                Trajectory.save_jsonl([sample.trajectory], str(traj_file))

        logger.info(f"saved evaluation to {output_dir}")
        logger.info(f"  summary: {report_file}")
        logger.info(f"  samples: {samples_dir}")
        logger.info(f"  trajectories: {trajectories_dir}")


def sanitize_api_keys(data: JsonValue) -> JsonValue:
    """Recursively sanitize API keys from nested data structures."""
    if isinstance(data, dict):
        sanitized = {}
        for key, value in data.items():
            if key == "api_key" and isinstance(value, str) and value.startswith("sk-"):
                sanitized[key] = "***REDACTED***"
            else:
                sanitized[key] = sanitize_api_keys(value)
        return sanitized
    elif isinstance(data, list):
        return [sanitize_api_keys(item) for item in data]
    else:
        return data


# ── Interrupt/Resume Support ──────────────────────────────────────────────────


def _write_partial_report(
    output_dir: Path,
    completed_samples: list[Sample],
    config: EvalConfig,
    interrupted: bool = False,
    resume_from: str | None = None,
) -> None:
    """Write partial report for observability and interrupt recovery.

    This enables:
    1. Viewing progress before eval completes
    2. Uploading partial results if interrupted
    3. Resuming from where we left off

    Args:
        output_dir: Directory to write report to
        completed_samples: Samples completed so far
        config: Eval config for metadata
        interrupted: Whether this write is due to an interrupt
        resume_from: Previous run directory if this is a resume
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    summary_metrics = compute_summary_metrics(completed_samples) if completed_samples else {}

    # Sanitize endpoint config
    endpoint_config = sanitize_api_keys(asdict(config.endpoint))

    report = {
        "eval_name": config.eval_name,
        "dataset_path": config.eval_name,
        "total_samples": config.max_samples,
        "completed_samples": len(completed_samples),
        "partial": True,  # Flag indicating incomplete run
        "interrupted": interrupted,
        "summary_metrics": summary_metrics,
        "config": {
            "endpoint": endpoint_config,
            "max_samples": config.max_samples,
            "max_concurrent": config.max_concurrent,
        },
        "sample_ids": [s.id for s in completed_samples],
        "timestamp": datetime.now().isoformat(),
        "git_info": _get_git_info(),
        "config_path": config.config_path,
    }

    if config.metadata:
        report["metadata"] = config.metadata

    if resume_from:
        report["resume_from"] = resume_from

    if interrupted:
        report["interrupted_at"] = datetime.now().isoformat()

    report = sanitize_api_keys(report)
    report_file = output_dir / "report.json"
    report_file.write_text(json.dumps(report, indent=2))

    logger.debug(f"Wrote partial report: {len(completed_samples)} samples")


def _load_completed_sample_ids(resume_dir: Path) -> set[str]:
    """Load IDs of completed samples from a previous run for resume.

    Scans the samples/ directory and returns IDs of samples that completed
    successfully (status == "success" in metadata).

    Args:
        resume_dir: Directory of previous run to resume from

    Returns:
        Set of sample IDs that completed successfully
    """
    completed_ids: set[str] = set()
    samples_dir = resume_dir / "samples"

    if not samples_dir.exists():
        logger.warning(f"No samples directory found in {resume_dir}")
        return completed_ids

    for sample_file in samples_dir.glob("*.json"):
        try:
            sample_data = json.loads(sample_file.read_text())
            # Check metadata.status for success (this is where evaluate_sample stores it)
            status = sample_data.get("metadata", {}).get("status")
            if status == "success":
                completed_ids.add(sample_data.get("id", sample_file.stem))
        except Exception as e:
            logger.warning(f"Failed to load sample {sample_file}: {e}")

    return completed_ids


def _load_streamed_samples(output_dir: Path) -> list[Sample]:
    """Load any samples already streamed to disk.

    If the evaluation loop is interrupted (Ctrl+C / cancellation), some samples
    may have already been streamed to `output_dir/samples/` even if we didn't
    successfully return the in-memory results list. Loading these lets us write
    an accurate partial report for resume.
    """
    samples: list[Sample] = []
    samples_dir = output_dir / "samples"
    if not samples_dir.exists():
        return samples

    for sample_file in sorted(samples_dir.glob("*.json")):
        try:
            sample_data = json.loads(sample_file.read_text())
            samples.append(Sample.from_dict(sample_data))
        except Exception as e:
            logger.warning(f"Failed to load streamed sample {sample_file}: {e}")

    return samples


@dataclass
class _AgentRunResult:
    """Result of running agent with error handling."""

    states: list[AgentState]
    final_trajectory: Trajectory
    error_message: str | None = None
    is_provider_error: bool = False


async def _cleanup_environment(environment: Environment | None, sample_id: str) -> None:
    """Cleanup environment if it has a cleanup method."""
    if environment is None:
        return
    cleanup_fn = getattr(environment, "cleanup", None)
    if cleanup_fn is None:
        return
    try:
        await cleanup_fn()
    except Exception as e:
        logger.warning(f"Environment cleanup failed for {sample_id}: {e}")


def _stream_sample_to_file(sample: Sample, output_dir: Path) -> None:
    """Stream a completed sample to file immediately for live observability.

    Writes sample JSON and trajectory JSONL as soon as the sample completes,
    allowing observation of results before the full evaluation finishes.
    Creates directories if needed.
    """
    try:
        output_dir = Path(output_dir)

        # Write sample JSON
        samples_dir = output_dir / "samples"
        samples_dir.mkdir(parents=True, exist_ok=True)
        sample_dict = sample.to_dict()
        sample_dict = sanitize_api_keys(sample_dict)
        sample_file = samples_dir / f"{sample.id}.json"
        sample_file.write_text(json.dumps(sample_dict, indent=2, default=str))

        # Write trajectory JSONL
        if sample.trajectory:
            trajectories_dir = output_dir / "trajectories"
            trajectories_dir.mkdir(parents=True, exist_ok=True)
            traj_file = trajectories_dir / f"{sample.id}.jsonl"
            Trajectory.save_jsonl([sample.trajectory], str(traj_file))

        logger.debug(f"Streamed sample {sample.id} to {output_dir}")
    except Exception as e:
        logger.warning(f"Failed to stream sample {sample.id}: {e}")


async def _run_agent_with_error_handling(
    initial_state: AgentState,
    run_config: RunConfig,
    sample_id: str,
) -> _AgentRunResult:
    """Run agent and handle errors, returning structured result.

    Distinguishes provider errors (rate limits, timeouts) from actual failures.
    Provider errors are excluded from accuracy calculation.
    """
    from .providers.base import FatalEvalError, ProviderError

    try:
        states = await run_agent(initial_state, run_config)
        return _AgentRunResult(
            states=states,
            final_trajectory=states[-1].actor.trajectory,
        )

    except FatalEvalError:
        # Auth errors, no credits, etc. - crash loudly, don't continue with other samples
        raise

    except ProviderError as e:
        error_message = f"ProviderError[{e.provider}]: {str(e)}"
        logger.warning(
            f"Sample {sample_id} provider_error: {error_message} (attempts: {e.attempts})"
        )
        final_trajectory = replace(
            initial_state.actor.trajectory,
            metadata={
                **initial_state.actor.trajectory.metadata,
                "error": error_message,
                "error_type": "provider_error",
                "provider": e.provider,
                "attempts": e.attempts,
            },
        )
        return _AgentRunResult(
            states=[initial_state],
            final_trajectory=final_trajectory,
            error_message=error_message,
            is_provider_error=True,
        )

    except Exception as e:
        error_message = f"{type(e).__name__}: {str(e)}"
        logger.warning(f"Sample {sample_id} failed: {error_message}")
        final_trajectory = replace(
            initial_state.actor.trajectory,
            metadata={
                **initial_state.actor.trajectory.metadata,
                "error": error_message,
                "error_type": "failed",
            },
        )
        return _AgentRunResult(
            states=[initial_state],
            final_trajectory=final_trajectory,
            error_message=error_message,
            is_provider_error=False,
        )


async def evaluate_sample(
    sample_data: dict[str, Any],
    sample_id: str,
    runtime: EvalRuntime,
    environment: Environment | None = None,
) -> Sample:
    """Evaluate a single sample - analogous to run_agent_step.

    This is the atomic unit of evaluation that can be easily parallelized.
    Each call should receive a fresh environment instance to ensure state isolation.

    Args:
        sample_data: The raw sample data
        sample_id: Unique identifier for this sample
        runtime: Runtime context (config + instantiated limiters/progress)
        environment: Fresh Environment instance for this sample (None for tool-free eval)

    Returns:
        Sample with trajectory, score, and computed reward
    """
    # Unpack runtime for convenience
    config = runtime.config
    progress = runtime.progress

    # Prepare initial messages from sample
    initial_messages = config.prepare_messages(sample_data)

    # Inject sample_data into trajectory metadata for score function access
    initial_trajectory = Trajectory(
        messages=initial_messages,
        metadata={"sample_data": sample_data},  # Ground truth available to score_fn
    )

    actor = Actor(
        trajectory=initial_trajectory,
        endpoint=config.endpoint,
        tools=environment.get_tools() if environment else [],
    )

    initial_state = AgentState(actor=actor, environment=environment)

    # Build base run config with concurrency limiters
    base_run_config = _build_base_run_config(config, runtime.api_limiter, runtime.tool_limiter)

    # Wrap on_chunk to inject sample_id context for concurrent sample tracking
    base_on_chunk = base_run_config.on_chunk
    last_status: dict[str, str] = {}  # Track last status to avoid duplicate events
    current_turn: dict[str, int] = {}  # Track current turn per sample for wide events

    async def on_chunk_with_sample_id(event: object) -> None:
        nonlocal last_status, current_turn

        # Update MultiProgress on various events for granular status
        status = _get_progress_status_for_event(event)
        turn = _get_turn_from_event(event)

        if progress is not None:
            if status is not None or turn is not None:
                progress.update_task(
                    sample_id,
                    turn=turn if turn is not None else None,
                    status=status if status is not None else None,
                )

        # Emit to file for TUI - only on status changes to avoid flooding
        if isinstance(event, StreamChunk):
            if event.type == "turn_start":
                turn_num = event.data.get("turn", 0)
                current_turn[sample_id] = turn_num
                emit_event("turn", id=sample_id, turn=turn_num, status="waiting")
                last_status[sample_id] = "waiting"
            elif event.type == "modal_progress":
                emit_event("modal_progress", id=sample_id, phase=event.data.get("phase", ""))

        # Emit status changes for LLM events (streaming, thinking, tool calls)
        if status is not None and status != last_status.get(sample_id):
            emit_event("turn", id=sample_id, status=status)
            last_status[sample_id] = status

        # Wide events: emit detailed timing for performance analysis
        sample_turn = current_turn.get(sample_id, 0)
        if isinstance(event, LLMCallEnd):
            emit_event(
                "llm_call",
                id=sample_id,
                turn=sample_turn,
                duration_ms=round(event.duration_ms, 1),
                provider=event.provider,
                model=event.model,
                tokens_in=event.tokens_in,
                tokens_out=event.tokens_out,
                status=event.status,
                error=event.error,
            )
        elif isinstance(event, ToolExecutionEnd):
            emit_event(
                "tool_execution",
                id=sample_id,
                turn=sample_turn,
                tool_name=event.tool_name,
                duration_ms=round(event.duration_ms, 1),
                status=event.status,
                is_error=event.is_error,
                result_summary=event.result_summary,
            )
        elif isinstance(event, TextEnd):
            # Emit assistant message content for observability
            # Truncate long content to avoid bloating events file
            content = event.content
            truncated = len(content) > 2000
            if truncated:
                content = content[:2000] + "..."
            emit_event(
                "assistant_message",
                id=sample_id,
                turn=sample_turn,
                content=content,
                content_length=len(event.content),
                truncated=truncated,
            )

        # Wrap event with sample_id and forward to base handler
        wrapped_event = _wrap_event_with_sample_id(event, sample_id)
        await base_on_chunk(wrapped_event)

    run_config = replace(base_run_config, on_chunk=on_chunk_with_sample_id)

    # Run agent
    # Tiger Style: Catch operational errors (rate limits, network issues) at boundary
    # These are expected errors that should be reported, not crash the eval
    if config.verbose:
        logger.debug(f"Evaluating {sample_id}")

    # Track timing for structured logging
    start_time = time.time()

    # Emit sample_start event for frontend live streaming
    # Include initial_messages so streaming handlers can display them
    await run_config.on_chunk(
        StreamChunk(
            "sample_start",
            {
                "sample_id": sample_id,
                "sample_data": sample_data,
                "messages": [
                    {
                        "role": m.role,
                        "content": m.content if isinstance(m.content, str) else str(m.content),
                    }
                    for m in initial_messages
                ],
            },
        )
    )

    # Also emit to file for TUI (if emitter configured)
    # TODO: Retry logic can emit multiple sample_start events for the same sample_id
    # without a corresponding sample_end, causing progress display to show 100/100
    # while a sample is still running. Either emit sample_end before retry, or
    # don't emit sample_start on retries. See: chiraag/supabase-eval-traces PR #504
    sample_name = sample_data.get("name", sample_id)
    emit_event("sample_start", id=sample_id, name=sample_name)

    # Run agent with error handling
    result = await _run_agent_with_error_handling(initial_state, run_config, sample_id)
    states = result.states
    final_trajectory = result.final_trajectory
    error_message = result.error_message
    is_provider_error = result.is_provider_error

    # Serialize environment state for score function (agentic evals)
    env_state = None
    final_env = states[-1].environment
    if final_env is not None:
        try:
            env_state = await final_env.serialize()
        except Exception as e:
            logger.warning(f"Failed to serialize environment state: {e}")

    # Build Sample with trajectory for score function
    sample = Sample(
        id=sample_id,
        input=sample_data,
        ground_truth=sample_data.get("ground_truth") or sample_data.get("answer"),
        trajectory=final_trajectory,
        environment_state=env_state,
        metadata=sample_data.get("metadata", {}),
    )

    # Compute score
    score = await _compute_score(config.score_fn, sample)

    # Add execution metadata
    exec_metadata = {
        "turns_used": states[-1].turn_idx,
        "stop_reason": str(states[-1].stop) if states[-1].stop else None,
        "total_tokens": sum(len(m.content or "") for m in final_trajectory.messages),
    }

    # Include error if agent execution failed
    if error_message:
        exec_metadata["error"] = error_message
        exec_metadata["status"] = "provider_error" if is_provider_error else "failed"
    elif states[-1].stop == StopReason.ABORTED:
        exec_metadata["status"] = "aborted"
    else:
        exec_metadata["status"] = "success"

    # Compute duration and log completion
    duration_seconds = time.time() - start_time
    exec_metadata["duration_seconds"] = duration_seconds
    reward = score.reward if score else 0.0

    _log_sample_completion(
        sample_id, reward, exec_metadata, final_trajectory, score, config.verbose
    )

    # Cleanup environment
    await _cleanup_environment(environment, sample_id)

    # Update sample with score, reward, and status
    sample.score = score
    sample.reward = score.reward if score else 0.0
    sample.metadata = {**sample.metadata, **exec_metadata}

    # Set Sample.status field based on execution result
    # This enables resume to correctly identify completed samples
    if error_message:
        if is_provider_error:
            sample.status = Status.ABORTED  # Provider errors are transient, can retry
        else:
            sample.status = Status.COMPLETED  # Actual failures are "complete" (just with error)
    elif states[-1].stop == StopReason.ABORTED:
        sample.status = Status.ABORTED  # Interrupted by user, can retry on resume
    else:
        sample.status = Status.COMPLETED

    # Stream sample to file immediately for live observability
    # This allows viewing trajectories before the full eval completes
    if config.output_dir:
        _stream_sample_to_file(sample, config.output_dir)

    # Emit sample_end event for frontend live streaming
    await run_config.on_chunk(
        StreamChunk(
            "sample_end",
            {"sample_id": sample_id, "reward": reward, "metadata": exec_metadata},
        )
    )

    # Also emit to file for TUI (if emitter configured)
    emit_event("sample_end", id=sample_id, score=reward)

    return sample


async def evaluate(
    dataset: Iterator[dict[str, Any]],
    config: EvalConfig,
) -> EvalReport:
    """Run evaluation on a dataset - analogous to run_agent.

    This orchestrates evaluate_sample calls, potentially in parallel.
    Each sample gets a fresh environment instance to ensure state isolation.

    Supports interrupt/resume:
    - Set config.resume_dir to resume from a previous interrupted run
    - Partial report.json is written every config.report_batch_size samples
    - SIGINT/SIGTERM triggers graceful shutdown with final report write

    Args:
        dataset: Iterator of sample dictionaries
        config: Evaluation configuration (includes endpoint, template/prepare_messages,
                environment_factory, score_fn, and execution settings)

    Returns:
        EvalReport with results and summary metrics

    Example:
        >>> config = EvalConfig(
        ...     endpoint=Endpoint(provider="openai", model="gpt-4o-mini"),
        ...     score_fn=my_score_fn,
        ...     template=PromptTemplate(system="...", user_template="{question}"),
        ... )
        >>> report = await evaluate(dataset, config)

    Example with resume:
        >>> config = EvalConfig(
        ...     ...,
        ...     resume_dir=Path("results/my_eval_20260122-100000"),
        ... )
        >>> report = await evaluate(dataset, config)  # Skips completed samples
    """
    # Load completed sample IDs if resuming
    completed_ids: set[str] = set()
    resume_from: str | None = None
    if config.resume_dir:
        completed_ids = _load_completed_sample_ids(config.resume_dir)
        resume_from = str(config.resume_dir)
        if completed_ids:
            print(
                f"Resuming from {config.resume_dir}: {len(completed_ids)} completed samples to skip"
            )

    # Collect samples to evaluate (skipping completed ones on resume)
    samples_to_eval: list[tuple[str, dict[str, Any]]] = []
    samples_to_eval_dict: dict[str, dict[str, Any]] = {}  # For retry lookup
    skipped_count = 0
    for i, sample_data in enumerate(dataset):
        if config.max_samples and (len(samples_to_eval) + skipped_count) >= config.max_samples:
            break
        sample_id = f"sample_{i:04d}"

        # Skip if already completed in previous run
        if sample_id in completed_ids:
            skipped_count += 1
            continue

        samples_to_eval.append((sample_id, sample_data))
        samples_to_eval_dict[sample_id] = sample_data

    # Handle case where all samples already completed (nothing to do)
    if not samples_to_eval and skipped_count > 0:
        print(f"All {skipped_count} samples already completed in previous run. Nothing to do.")
        print(f"Results at: {config.resume_dir}")
        # Return empty report - caller can load results from resume_dir if needed
        return EvalReport(
            eval_name=config.eval_name,
            dataset_path=config.eval_name,
            total_samples=skipped_count,
            summary_metrics={},
            sample_results=[],
            config={"resumed_from": str(config.resume_dir)},
            metadata=config.metadata,
        )

    if config.verbose:
        logger.info(f"starting evaluation: {config.eval_name}")
        if skipped_count > 0:
            logger.info(f"skipped {skipped_count} completed samples (resume)")
        logger.info(f"samples to evaluate: {len(samples_to_eval)}")
        logger.info(f"max concurrent: {config.max_concurrent}")
        logger.debug("=" * 50)

    # Initialize event emitter for TUI progress (writes to events.jsonl)
    # This is separate from MultiProgress - events go to file for external TUI
    emitter: EventEmitter | None = None
    if config.output_dir:
        emitter = EventEmitter(output_dir=config.output_dir)
        emitter.as_context()  # Make available via get_emitter()
        emitter.emit("eval_start", name=config.eval_name, total=len(samples_to_eval))

    # Evaluate samples (with concurrency control)
    results: list[Sample] = []

    # Track state for interrupt handling
    interrupted = False
    last_report_count = 0  # Track when we last wrote a report

    # Create callback for incremental report writing
    def on_sample_complete(sample: Sample, all_results: list[Sample]) -> None:
        """Write partial report after batch_size samples complete."""
        nonlocal last_report_count
        if not config.output_dir:
            return

        # Write report every report_batch_size samples
        if len(all_results) - last_report_count >= config.report_batch_size:
            _write_partial_report(
                config.output_dir,
                all_results,
                config,
                interrupted=False,
                resume_from=resume_from,
            )
            last_report_count = len(all_results)

    # Initialize progress display for sample-level tracking
    # MultiProgress shows each concurrent sample with turn-by-turn updates
    progress: MultiProgress | None = None
    if config.show_progress:
        progress = MultiProgress(
            total=len(samples_to_eval),
            desc=config.eval_name,
            unit="sample",
            verbose=config.verbose,  # verbose=True shows INFO logs, False shows only WARNING+
        )
        progress.__enter__()

    # Create two-level concurrency limiters if configured
    api_limiter = (
        trio.CapacityLimiter(config.max_api_concurrent)
        if config.max_api_concurrent is not None
        else None
    )
    tool_limiter = (
        trio.CapacityLimiter(config.max_tool_concurrent)
        if config.max_tool_concurrent is not None
        else None
    )

    # Create runtime context (bundles config + instantiated handles)
    runtime = EvalRuntime(
        config=config,
        api_limiter=api_limiter,
        tool_limiter=tool_limiter,
        progress=progress,
    )

    # Run initial evaluation batch with incremental report callback
    try:
        results = await _evaluate_batch(samples_to_eval, runtime, on_sample_complete)
    except KeyboardInterrupt:
        # Handle Ctrl+C during evaluation
        interrupted = True
        logger.warning("Evaluation interrupted by user")
        if config.output_dir:
            results = _load_streamed_samples(config.output_dir)
    except trio.Cancelled:
        # Handle trio cancellation (from signal handler)
        interrupted = True
        logger.warning("Evaluation cancelled")
        if config.output_dir:
            results = _load_streamed_samples(config.output_dir)
    except BaseExceptionGroup as eg:
        # Trio wraps KeyboardInterrupt in ExceptionGroup - check if it's an interrupt
        if eg.subgroup(KeyboardInterrupt) is not None:
            interrupted = True
            logger.warning("Evaluation interrupted by user")
            if config.output_dir:
                results = _load_streamed_samples(config.output_dir)
        else:
            raise

    # Close progress display
    if progress:
        progress.__exit__(None, None, None)

    # Write final partial report and upload if interrupted
    if interrupted and config.output_dir:
        print(f"\nInterrupted - saving partial report ({len(results)} samples)...")
        _write_partial_report(
            config.output_dir,
            results,
            config,
            interrupted=True,
            resume_from=resume_from,
        )
        # Upload partial results to supabase if configured
        try:
            from .upload import upload_results_to_supabase

            print("Uploading partial results to Supabase...")
            upload_results_to_supabase(config.output_dir)
            print("Upload complete.")
        except Exception as e:
            print(f"Upload failed: {e}")
        # Close emitter and exit
        if emitter:
            emitter.emit("eval_end", name=config.eval_name, total=len(results), interrupted=True)
            emitter.close()
        # Exit cleanly - don't re-raise to avoid big traceback
        print(f"Partial results saved to {config.output_dir}")
        print("Resume with: --resume", config.output_dir)
        sys.exit(130)  # 130 = 128 + SIGINT(2), standard for Ctrl+C

    # Sample-level retry for provider errors (rate limits, connection errors)
    for retry_attempt in range(config.max_sample_retries):
        failed_samples = [
            (r.id, samples_to_eval_dict[r.id])
            for r in results
            if r.metadata.get("status") == "provider_error"
        ]

        if not failed_samples:
            break  # All samples succeeded

        # Wait before retry (exponential backoff: 30s, 60s, 120s)
        wait_seconds = min(30 * (2**retry_attempt), 120)
        retry_msg = (
            f"Retrying {len(failed_samples)} failed samples "
            f"(attempt {retry_attempt + 1}/{config.max_sample_retries}, waiting {wait_seconds}s)"
        )
        if progress:
            progress.log(retry_msg)
        else:
            logger.info(retry_msg)
        await trio.sleep(wait_seconds)

        # Remove failed samples and retry
        failed_ids = {sid for sid, _ in failed_samples}
        results = [r for r in results if r.id not in failed_ids]
        # Create runtime without progress for retries (no incremental reports during retry)
        retry_runtime = EvalRuntime(
            config=config,
            api_limiter=api_limiter,
            tool_limiter=tool_limiter,
            progress=None,
        )
        retry_results = await _evaluate_batch(failed_samples, retry_runtime)
        results.extend(retry_results)

        # Write incremental report after retry batch
        if config.output_dir:
            _write_partial_report(
                config.output_dir,
                results,
                config,
                interrupted=False,
                resume_from=resume_from,
            )
            last_report_count = len(results)

        # Log retry results
        still_failed = sum(1 for r in retry_results if r.metadata.get("status") == "provider_error")
        succeeded = len(retry_results) - still_failed
        retry_result_msg = (
            f"Retry {retry_attempt + 1}: {succeeded} succeeded, {still_failed} still failing"
        )
        if progress:
            progress.log(retry_result_msg)
        else:
            logger.info(retry_result_msg)

    # Compute summary metrics
    summary_metrics = compute_summary_metrics(results)

    # Create report
    # Sanitize endpoint config to exclude sensitive data
    endpoint_config = sanitize_api_keys(asdict(config.endpoint))

    report = EvalReport(
        eval_name=config.eval_name,
        dataset_path=config.eval_name,  # Use eval_name as dataset identifier
        total_samples=len(results),
        summary_metrics=summary_metrics,
        sample_results=results,
        config={
            "endpoint": endpoint_config,
            "max_samples": config.max_samples,
            "max_concurrent": config.max_concurrent,
            "evaluation_timestamp": datetime.now().isoformat(),
        },
        config_path=config.config_path,
        metadata=config.metadata,
    )

    # Save if output directory specified
    if config.output_dir:
        await report.save(config.output_dir)

    # Print summary
    if config.verbose:
        logger.info("")
        logger.debug("=" * 50)
        logger.info(f"Evaluation Summary: {config.eval_name}")
        logger.debug("=" * 50)
        logger.info(f"Samples evaluated: {len(results)}")
        for key, value in summary_metrics.items():
            # Handle both numeric and non-numeric values
            if isinstance(value, int | float):
                logger.info(f"{key}: {value:.3f}")
            else:
                logger.info(f"{key}: {value}")

    # Close event emitter
    if emitter:
        emitter.emit("eval_end", name=config.eval_name, total=len(results))
        emitter.close()

    return report


def compute_summary_metrics(results: list[Sample]) -> dict[str, float]:
    """Compute summary statistics from results using Score.

    Aggregates metrics from Score objects across all results.

    TODO: Separate provider_error from failed samples in accuracy calculation
    Article quote: "As these samples get scored as failure, the scores for the
    corresponding provider are affected substantially."

    Problem: Currently failed_samples includes both actual failures AND provider errors.
    This inflates the failure rate when providers have issues (rate limits, timeouts, etc.)

    Fix: Track provider_errors separately and exclude from success_rate calculation:
        provider_errors = [r for r in results if r.metadata.get("status") == "provider_error"]
        actual_failures = [r for r in results if r.metadata.get("status") == "failed"]
        success_rate = (total - len(actual_failures)) / (total - len(provider_errors))
    """
    if not results:
        return {}

    summary: dict[str, Any] = {}

    # Get all unique metric names from Score objects
    all_metric_names: set[str] = set()
    for r in results:
        if r.score:
            for m in r.score.metrics:
                all_metric_names.add(m.name)

    # Compute mean, median, min, max, std for each metric
    for metric_name in all_metric_names:
        values = []
        for r in results:
            if r.score:
                for m in r.score.metrics:
                    if m.name == metric_name:
                        values.append(m.value)
                        break
        if values:
            mean_val = sum(values) / len(values)
            sorted_values = sorted(values)
            n = len(sorted_values)
            if n % 2 == 0:
                median_val = (sorted_values[n // 2 - 1] + sorted_values[n // 2]) / 2
            else:
                median_val = sorted_values[n // 2]
            
            summary[f"mean_{metric_name}"] = mean_val
            summary[f"median_{metric_name}"] = median_val
            summary[f"min_{metric_name}"] = min(values)
            summary[f"max_{metric_name}"] = max(values)
            summary[f"std_{metric_name}"] = (
                sum((v - mean_val) ** 2 for v in values) / len(values)
            ) ** 0.5

    # Compute reward summary (the weighted score)
    rewards = [r.score.reward if r.score else 0.0 for r in results]
    if rewards:
        mean_reward = sum(rewards) / len(rewards)
        summary["mean_reward"] = mean_reward
        summary["min_reward"] = min(rewards)
        summary["max_reward"] = max(rewards)
        summary["std_reward"] = (sum((r - mean_reward) ** 2 for r in rewards) / len(rewards)) ** 0.5

    # Add metadata summaries
    summary["total_samples"] = len(results)
    summary["avg_turns"] = sum(r.metadata.get("turns_used", 0) for r in results) / len(results)
    summary["avg_tokens"] = sum(r.metadata.get("total_tokens", 0) for r in results) / len(results)

    # Separate provider errors from actual failures
    # Provider errors (rate limits, timeouts) are excluded from accuracy calculation
    provider_errors = [r for r in results if r.metadata.get("status") == "provider_error"]
    failed_samples = [r for r in results if r.metadata.get("status") == "failed"]
    successful_samples = [r for r in results if r.metadata.get("status") == "success"]

    summary["provider_errors"] = len(provider_errors)
    summary["failed_samples"] = len(failed_samples)
    summary["successful_samples"] = len(successful_samples)

    # Success rate excludes provider errors from denominator
    # (we can't count them as failures if the model never got to run)
    valid_samples = len(results) - len(provider_errors)
    summary["success_rate"] = len(successful_samples) / valid_samples if valid_samples > 0 else 0.0

    # Also provide raw completion rate (including provider errors as failures)
    summary["completion_rate"] = len(successful_samples) / len(results) if results else 0.0

    # Breakdown errors by type (for failed samples only, not provider errors)
    error_types: dict[str, int] = {}
    for r in failed_samples:
        error = r.metadata.get("error", "Unknown error")
        # Extract error type (e.g., "ValueError" from "ValueError: ...")
        error_type = error.split(":")[0] if ":" in error else error
        error_types[error_type] = error_types.get(error_type, 0) + 1

    if error_types:
        summary["error_breakdown"] = error_types

    # Breakdown provider errors by provider
    provider_breakdown: dict[str, int] = {}
    for r in provider_errors:
        # Extract provider from error message or metadata
        error = r.metadata.get("error", "")
        if "ProviderError[" in error:
            # Extract provider name from "ProviderError[anthropic]: ..."
            provider = error.split("[")[1].split("]")[0]
        else:
            provider = "unknown"
        provider_breakdown[provider] = provider_breakdown.get(provider, 0) + 1

    if provider_breakdown:
        summary["provider_error_breakdown"] = provider_breakdown

    return summary


# Dataset loaders
def load_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    """Load JSONL dataset."""
    with open(path) as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def load_csv(path: Path) -> Iterator[dict[str, Any]]:
    """Load CSV dataset."""
    import csv

    with open(path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield dict(row)


# Convenience function for simple evaluation
async def simple_evaluate(
    dataset_path: Path,
    config: EvalConfig,
) -> EvalReport:
    """Simple evaluation interface for common cases.

    Auto-detects dataset format (.jsonl or .csv) and runs evaluation.

    Args:
        dataset_path: Path to dataset file (.jsonl or .csv)
        config: Evaluation configuration (includes endpoint, template/prepare_messages,
                environment_factory, score_fn, etc.)

    Returns:
        EvalReport with results and summary metrics

    Example:
        >>> config = EvalConfig(
        ...     endpoint=Endpoint(...),
        ...     score_fn=my_score_fn,
        ...     template=PromptTemplate(system="...", user_template="{question}"),
        ... )
        >>> report = await simple_evaluate(Path("data.jsonl"), config)
    """
    # Auto-detect dataset format
    if dataset_path.suffix == ".jsonl":
        dataset = load_jsonl(dataset_path)
    elif dataset_path.suffix == ".csv":
        dataset = load_csv(dataset_path)
    else:
        raise ValueError(f"Unsupported format: {dataset_path.suffix}")

    return await evaluate(dataset, config)


# ── Analysis Helpers ──────────────────────────────────────────────────────────


def group_by(
    results: list[Sample],
    key: Callable[[Sample], str],
) -> dict[str, list[Sample]]:
    """Group evaluation results by a key function.

    Pure function for slicing results by metadata.

    Examples:
        >>> by_difficulty = group_by(results, key=lambda r: r.metadata["difficulty"])
        >>> by_category = group_by(results, key=lambda r: r.input.get("category", "unknown"))

    Args:
        results: List of evaluation samples
        key: Function to extract grouping key from each sample

    Returns:
        Dict mapping group keys to lists of samples
    """
    groups: dict[str, list[Sample]] = {}
    for result in results:
        k = key(result)
        if k not in groups:
            groups[k] = []
        groups[k].append(result)
    return groups


def summarize(results: list[Sample]) -> dict[str, float]:
    """Compute summary statistics for a list of evaluation results.

    Pure function for aggregating metrics.

    Examples:
        >>> stats = summarize(results)
        >>> print(f"Mean reward: {stats['mean']:.2%}, n={stats['n']}")

    Args:
        results: List of evaluation samples

    Returns:
        Dict with mean, std, min, max, n for the reward signal
    """
    if not results:
        return {"mean": 0.0, "std": 0.0, "min": 0.0, "max": 0.0, "n": 0}

    # Extract rewards - prefer Score.reward, fall back to metrics["reward"]
    rewards = []
    for r in results:
        if r.score is not None:
            rewards.append(r.score.reward)
        else:
            rewards.append(0.0)

    n = len(rewards)
    mean = sum(rewards) / n
    variance = sum((r - mean) ** 2 for r in rewards) / n
    std = variance**0.5

    return {
        "mean": mean,
        "std": std,
        "min": min(rewards),
        "max": max(rewards),
        "n": n,
    }


# ── Eval Runner Utilities ─────────────────────────────────────────────────────


def get_api_key(provider: str = "anthropic") -> str | None:
    """Get API key from environment variables.

    Checks provider-specific env vars in order of preference.

    Args:
        provider: LLM provider name (anthropic, openai, etc.)

    Returns:
        API key string or None if not found
    """
    import os

    provider_key_map = {
        "anthropic": ["WAFER_ANTHROPIC_API_KEY", "ANTHROPIC_API_KEY"],
        "openai": ["WAFER_OPENAI_API_KEY", "OPENAI_API_KEY"],
        "google": ["WAFER_GOOGLE_API_KEY", "GOOGLE_API_KEY"],
        "gemini": ["WAFER_GEMINI_API_KEY", "GEMINI_API_KEY"],
    }

    env_vars = provider_key_map.get(provider.lower(), [f"{provider.upper()}_API_KEY"])

    for env_var in env_vars:
        key = os.environ.get(env_var)
        if key:
            return key

    return None


def run_with_progress(
    eval_fn: Callable[[Any], Any],
    config: Any,
    output_dir: Path,
    quiet_config_fn: Callable[[Any], Any] | None = None,
    async_wrapper: Callable[[Callable, Any], Callable[[], Any]] | None = None,
) -> dict[str, Any]:
    """Run evaluation with progress display TUI.

    Wraps an async eval function with the progress_display context manager,
    which redirects stdout/stderr to output.log and renders a TUI.

    Args:
        eval_fn: Async evaluation function that takes config and returns results
        config: Configuration object
        output_dir: Directory for output files (events.jsonl, output.log)
        quiet_config_fn: Optional function to create a quiet version of config
                        (disables internal verbose/show_progress flags)
        async_wrapper: Optional wrapper for async runtime compatibility (e.g., trio_asyncio).
                      Takes (eval_fn, config) and returns an async callable for trio.run().

    Returns:
        Results dict from eval_fn

    Example:
        def my_quiet_config(config):
            return replace(config, run=replace(config.run, verbose=False, show_progress=False))

        result = run_with_progress(
            evaluate_my_task,
            config,
            config.output.output_dir,
            quiet_config_fn=my_quiet_config,
        )
    """
    from .progress_display import progress_display

    # Apply quiet config transformation if provided
    run_config = quiet_config_fn(config) if quiet_config_fn else config

    with progress_display(output_dir=output_dir):
        if async_wrapper:
            result = trio.run(async_wrapper(eval_fn, run_config))
        else:
            result = trio.run(eval_fn, run_config)
        assert result is not None, "Evaluation was cancelled"

    return result


def run_eval(
    eval_fn: Callable[[Any], Any],
    config: Any,
    output_dir: Path,
    show_progress: bool = False,
    quiet_config_fn: Callable[[Any], Any] | None = None,
    print_summary_fn: Callable[[dict[str, Any], Path], None] | None = None,
    async_wrapper: Callable[[Callable, Any], Callable[[], Any]] | None = None,
) -> dict[str, Any]:
    """Standard entry point for running evaluations.

    Handles the common pattern of optionally wrapping eval in progress display.

    Args:
        eval_fn: Async evaluation function that takes config and returns results
        config: Configuration object
        output_dir: Directory for output files
        show_progress: Whether to show progress TUI
        quiet_config_fn: Optional function to create quiet config for progress mode
        print_summary_fn: Optional function to print summary after completion
        async_wrapper: Optional wrapper for async runtime compatibility (e.g., trio_asyncio).
                      Takes (eval_fn, config) and returns an async callable for trio.run().
                      Use this when eval_fn depends on asyncio libraries (e.g., Modal SDK).

    Returns:
        Results dict from eval_fn

    Example:
        def run(config: MyEvalConfig) -> dict[str, Any]:
            return run_eval(
                eval_fn=evaluate_my_task,
                config=config,
                output_dir=config.output.output_dir,
                show_progress=config.run.show_progress,
                quiet_config_fn=lambda c: replace(c, run=replace(c.run, verbose=False, show_progress=False)),
                print_summary_fn=print_my_summary,
            )

    Example with trio_asyncio (for Modal/asyncio compatibility):
        import trio_asyncio

        def asyncio_compat_wrapper(eval_fn, config):
            async def wrapped():
                async with trio_asyncio.open_loop():
                    return await eval_fn(config)
            return wrapped

        result = run_eval(
            eval_fn=evaluate_kernelbench,
            config=config,
            ...,
            async_wrapper=asyncio_compat_wrapper,
        )
    """
    if show_progress:
        result = run_with_progress(eval_fn, config, output_dir, quiet_config_fn, async_wrapper)
    else:
        if async_wrapper:
            result = trio.run(async_wrapper(eval_fn, config))
        else:
            result = trio.run(eval_fn, config)
        assert result is not None, "Evaluation was cancelled"

    if print_summary_fn:
        print_summary_fn(result, output_dir)

    return result
