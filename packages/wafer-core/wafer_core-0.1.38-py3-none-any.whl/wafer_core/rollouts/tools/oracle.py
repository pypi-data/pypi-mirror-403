"""
Oracle tool - consult a senior engineer for planning, review, and debugging.

The oracle is a subagent that uses a (potentially stronger) model to provide
expert guidance on complex tasks. It runs in zero-shot mode and returns
concise, actionable recommendations.

Usage:
    # As a standalone function
    result = await oracle_impl(
        task="Review this auth implementation for security issues",
        files=[FileRange(path="auth.py", start=50, end=120)],
        endpoint=oracle_endpoint,
        filesystem=fs,
    )

    # As a tool in an environment (via decorator)
    tools = [oracle_tool.definition]
"""

from dataclasses import dataclass, replace
from typing import Annotated

from ..agents import run_agent
from ..dtypes import (
    Actor,
    AgentState,
    Endpoint,
    Message,
    RunConfig,
    StopReason,
    StreamEvent,
    Trajectory,
)
from .decorator import Depends, Tool, tool


async def _noop_on_chunk(event: StreamEvent) -> None:
    """Silent chunk handler for oracle (doesn't stream to user)."""
    pass


# ── Types ─────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class FileRange:
    """A file path with optional line range."""

    path: str
    start: int | None = None  # None = from beginning
    end: int | None = None  # None = to end


# ── Configuration ─────────────────────────────────────────────────────────────

# Default oracle model - GPT-5.2 with high reasoning effort
# Can be overridden via Depends
DEFAULT_ORACLE_PROVIDER = "openai"
DEFAULT_ORACLE_MODEL = "gpt-5.2"
DEFAULT_REASONING_EFFORT = "high"  # low, medium, high

ORACLE_SYSTEM_PROMPT = """You are the Oracle - an expert AI advisor with advanced reasoning capabilities.

Your role is to provide high-quality technical guidance, code reviews, architectural advice, and strategic planning for software engineering tasks.

You are a subagent inside an AI coding system, called when the main agent needs deeper analysis. You are invoked in a zero-shot manner - no follow-up questions or answers.

Key responsibilities:
- Analyze code and architecture patterns
- Provide specific, actionable technical recommendations
- Plan implementations and refactoring strategies
- Debug complex issues with clear reasoning
- Identify potential issues and propose solutions

Operating principles (simplicity-first):
- Default to the simplest viable solution that meets requirements
- Prefer minimal, incremental changes that reuse existing code and patterns
- Optimize for maintainability and developer time over theoretical scalability
- Apply YAGNI and KISS; avoid premature optimization
- Provide one primary recommendation with at most one alternative if materially different
- Calibrate depth to scope: brief for small tasks, deep only when truly required
- Include rough effort signal (S <1h, M 1-3h, L 1-2d, XL >2d) when proposing changes

Response format (concise and action-oriented):
1) TL;DR: 1-3 sentences with recommended simple approach
2) Recommended approach: numbered steps or short checklist with minimal code snippets
3) Rationale: brief justification; why alternatives are unnecessary now
4) Risks and guardrails: key caveats and mitigations
5) When to reconsider: concrete triggers that would justify more complexity

IMPORTANT: Be comprehensive yet focused. Give clear, simple recommendations the user can act on immediately."""


# ── Dependency Providers ──────────────────────────────────────────────────────


def get_default_oracle_endpoint() -> Endpoint:
    """Default oracle endpoint provider. Override via Depends for custom model.

    Uses GPT-5.2 with high reasoning effort by default.
    API key is loaded from OPENAI_API_KEY env var.
    """
    import os

    return Endpoint(
        provider=DEFAULT_ORACLE_PROVIDER,
        model=DEFAULT_ORACLE_MODEL,
        api_base="https://api.openai.com/v1",
        api_key=os.environ.get("OPENAI_API_KEY", ""),
        reasoning_effort=DEFAULT_REASONING_EFFORT,
        max_completion_tokens=16384,  # GPT-5 uses max_completion_tokens, not max_tokens
    )


# ── Core Implementation ───────────────────────────────────────────────────────


async def read_file_range(
    path: str,
    start: int | None,
    end: int | None,
    read_fn,
) -> str:
    """Read a file with optional line range."""
    content = await read_fn(path)
    if content is None:
        return f"# {path}\n<file not found>"

    lines = content.splitlines()

    # Convert to 0-indexed
    start_idx = (start - 1) if start else 0
    end_idx = end if end else len(lines)

    # Clamp to valid range
    start_idx = max(0, start_idx)
    end_idx = min(len(lines), end_idx)

    selected = lines[start_idx:end_idx]

    # Format with line numbers
    range_str = f"{start_idx + 1}-{end_idx}" if start or end else "full"
    header = f"# {path}:{range_str}"

    numbered_lines = [f"{start_idx + i + 1:4d} | {line}" for i, line in enumerate(selected)]
    return header + "\n" + "\n".join(numbered_lines)


async def oracle_impl(
    task: str,
    context: str | None,
    files: list[FileRange] | None,
    endpoint: Endpoint,
    read_fn,
    max_turns: int = 1,
) -> str:
    """
    Core oracle implementation.

    Args:
        task: The task or question for the oracle
        context: Optional background context
        files: Optional file ranges to examine
        endpoint: The endpoint to use for the oracle
        read_fn: Async function to read files: (path) -> str | None
        max_turns: Max turns for the oracle (default 1 = zero-shot)

    Returns:
        The oracle's response text
    """
    # Build user message
    parts = []

    if context:
        parts.append(f"Context:\n{context}")

    parts.append(f"Task:\n{task}")

    # Read and attach files
    if files:
        file_contents = []
        for f in files:
            content = await read_file_range(f.path, f.start, f.end, read_fn)
            file_contents.append(content)

        if file_contents:
            parts.append("Relevant files:\n\n" + "\n\n".join(file_contents))

    user_message = "\n\n".join(parts)

    # Build trajectory
    trajectory = Trajectory(
        messages=[
            Message(role="system", content=ORACLE_SYSTEM_PROMPT),
            Message(role="user", content=user_message),
        ]
    )

    # Create minimal state
    state = AgentState(
        actor=Actor(
            trajectory=trajectory,
            endpoint=endpoint,
            tools=[],  # Oracle has no tools - pure reasoning
        ),
        environment=None,
    )

    # Simple stop handler
    def handle_stop(s: AgentState) -> AgentState:
        if s.turn_idx >= max_turns:
            return replace(s, stop=StopReason.MAX_TURNS)
        return s

    # Run the oracle
    config = RunConfig(
        on_chunk=_noop_on_chunk,
        handle_stop=handle_stop,
        session_store=None,  # Ephemeral - don't persist
    )

    states = await run_agent(state, config)

    # Extract final assistant message
    final_state = states[-1]
    for msg in reversed(final_state.actor.trajectory.messages):
        if msg.role == "assistant" and msg.content:
            if isinstance(msg.content, str):
                return msg.content
            # Handle content blocks
            text_parts = []
            for block in msg.content:
                if hasattr(block, "text"):
                    text_parts.append(block.text)
                elif isinstance(block, dict) and block.get("type") == "text":
                    text_parts.append(block.get("text", ""))
            if text_parts:
                return "\n".join(text_parts)

    return "<oracle returned no response>"


# ── Tool Definition ───────────────────────────────────────────────────────────

# TODO: Implement handoff tool for transferring work to a new thread when context
# is degraded. See amp's handoff implementation which:
# 1. Calls create_handoff_context to extract (relevant_info, relevant_files)
# 2. Creates a child session with summarized context
# 3. Starts a new agent on that session
# The primitives needed are: summarize_trajectory() and session_store.fork()


@tool(
    "Consult the Oracle - an expert advisor for planning, code review, debugging, and architecture analysis"
)
async def oracle(
    task: str,
    context: str | None = None,
    files: list[FileRange] | None = None,
    # Injected dependencies (hidden from LLM schema)
    endpoint: Annotated[Endpoint, Depends(get_default_oracle_endpoint)] = None,  # type: ignore
    read_fn: Annotated[object, Depends(lambda: None)] = None,  # type: ignore  # Must be overridden
) -> str:
    """
    Consult the Oracle for expert guidance on complex tasks.

    Use this tool when you need:
    - Code review and architecture feedback
    - Help debugging issues across multiple files
    - Planning complex implementations or refactoring
    - Deeper analysis that requires careful reasoning

    Do NOT use for:
    - Simple file reading (use read tool directly)
    - Basic code modifications (do it yourself)
    - Codebase searches (use grep/glob)

    Args:
        task: The task or question you want help with. Be specific about what
            kind of guidance, review, or planning you need.
        context: Optional background context about the situation, what you've
            tried, or constraints that would help provide better guidance.
        files: Optional list of file ranges to examine. Each has path (required),
            start line (optional), and end line (optional). Prefer specific
            ranges over full files to focus the analysis.

    Returns:
        Expert guidance with TL;DR, recommended approach, rationale, and caveats.
    """
    assert endpoint is not None, "endpoint must be injected via Depends"
    assert read_fn is not None, "read_fn must be injected via Depends"

    return await oracle_impl(
        task=task,
        context=context,
        files=files,
        endpoint=endpoint,
        read_fn=read_fn,
    )


# Convenience export
oracle_tool: Tool = oracle
