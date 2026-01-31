"""Wafer CLI command execution tool.

Pure function executor for wafer subcommands that accepts ToolCall and returns ToolResult.
"""

import shlex
import subprocess
from pathlib import Path

import trio

from wafer_core.rollouts.dtypes import (
    Tool,
    ToolCall,
    ToolFunction,
    ToolFunctionParameter,
    ToolResult,
)

# Constants
MAX_OUTPUT_SIZE = 10 * 1024 * 1024  # 10MB

# All wafer subcommands (used for --tools filtering)
# These can be passed to --tools like: --tools read,write,ncu-analyze
WAFER_SUBCOMMANDS = {
    "ncu-analyze",
    "remote-run",
    "push",
    "evaluate",
    "targets",
    "rocprof-sdk",
    "rocprof-compute",
    "rocprof-systems",
}

# Blocked subcommands (require --allow-spawn)
BLOCKED_WAFER_SUBCOMMANDS = {
    "wevin",
}


# ── Helper Functions ──────────────────────────────────────────────────────────

def get_enabled_subcommands(enabled_tools: list[str] | None) -> set[str]:
    """Get the set of enabled wafer subcommands (pure function)."""
    if enabled_tools is None:
        # All subcommands enabled by default
        return WAFER_SUBCOMMANDS.copy()

    # Filter to only wafer subcommands that are in enabled_tools
    return {t for t in enabled_tools if t in WAFER_SUBCOMMANDS}


# ── Tool Definition ──────────────────────────────────────────────────────────

WAFER_TOOL = Tool(
    type="function",
    function=ToolFunction(
        name="wafer",
        description="Execute a wafer CLI command. Available subcommands: ncu-analyze (analyze NCU profiles), remote-run (run on remote GPU), push (push files to remote), evaluate (run kernel evaluation), targets (list available targets), rocprof-sdk (profile with ROCprofiler-SDK/rocprofv3), rocprof-compute (profile with ROCprofiler-Compute and roofline analysis), rocprof-systems (system-level profiling with rocprof-sys).",
        parameters=ToolFunctionParameter(
            type="object",
            properties={
                "subcommand": {"type": "string", "description": "Wafer subcommand to run (e.g., 'ncu-analyze', 'rocprof-sdk', 'rocprof-compute', 'rocprof-systems')"},
                "args": {"type": "string", "description": "Arguments to pass to the subcommand"},
                "timeout": {"type": "integer", "description": "Timeout in seconds (default: 300)"},
            }
        ),
        required=["subcommand"]
    )
)


# ── Pure Function Executor ────────────────────────────────────────────────────

async def exec_wafer(
    tool_call: ToolCall,
    working_dir: Path,
    enabled_tools: list[str] | None,
    allow_spawn: bool,
    cancel_scope: trio.CancelScope | None = None,
) -> ToolResult:
    """Execute wafer subcommand (pure function - takes config as parameters)."""
    subcommand = tool_call.args["subcommand"]
    args = tool_call.args.get("args", "")
    timeout = tool_call.args.get("timeout", 300)

    # Check for blocked subcommands (wevin requires --allow-spawn)
    if subcommand in BLOCKED_WAFER_SUBCOMMANDS and not allow_spawn:
        return ToolResult(
            tool_call_id=tool_call.id,
            is_error=True,
            content="",
            error=f"Subcommand '{subcommand}' is blocked. Use --allow-spawn to enable spawning sub-agents."
        )

    # Get enabled subcommands based on --tools flag
    enabled_subcommands = get_enabled_subcommands(enabled_tools)

    # Check if subcommand is enabled
    if subcommand not in enabled_subcommands and subcommand not in BLOCKED_WAFER_SUBCOMMANDS:
        if subcommand in WAFER_SUBCOMMANDS:
            # Valid subcommand but not enabled
            return ToolResult(
                tool_call_id=tool_call.id,
                is_error=True,
                content="",
                error=f"Subcommand '{subcommand}' is not enabled. Enabled: {', '.join(sorted(enabled_subcommands))}"
            )
        else:
            # Unknown subcommand
            return ToolResult(
                tool_call_id=tool_call.id,
                is_error=True,
                content="",
                error=f"Unknown wafer subcommand: '{subcommand}'. Available: {', '.join(sorted(WAFER_SUBCOMMANDS))}"
            )

    # Build command - handle args based on subcommand
    cmd_parts = ["wafer", subcommand]
    if args:
        # Use shlex.split for commands with multiple args
        try:
            cmd_parts.extend(shlex.split(args))
        except ValueError:
            # If shlex.split fails, treat as single argument
            cmd_parts.append(args)

    try:
        result = await trio.to_thread.run_sync(
            lambda: subprocess.run(
                cmd_parts,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(working_dir),
            ),
        )

        output = ""
        if result.stdout:
            output += result.stdout
        if result.stderr:
            if output:
                output += "\n"
            output += result.stderr

        # Truncate if too large
        if len(output) > MAX_OUTPUT_SIZE:
            output = output[:MAX_OUTPUT_SIZE] + "\n\n... (output truncated)"

        if result.returncode != 0:
            return ToolResult(
                tool_call_id=tool_call.id,
                is_error=True,
                content=output or "(no output)",
                error=f"wafer {subcommand} exited with code {result.returncode}"
            )

        return ToolResult(
            tool_call_id=tool_call.id,
            is_error=False,
            content=output or "(no output)"
        )

    except subprocess.TimeoutExpired:
        return ToolResult(
            tool_call_id=tool_call.id,
            is_error=True,
            content="",
            error=f"wafer {subcommand} timed out after {timeout} seconds"
        )
    except trio.Cancelled:
        return ToolResult(
            tool_call_id=tool_call.id,
            is_error=True,
            content="",
            error="Command aborted"
        )
