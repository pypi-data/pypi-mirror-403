"""Grep tool for searching file contents.

Pure function executor using ripgrep.
"""

import subprocess
from pathlib import Path

from wafer_core.rollouts.dtypes import (
    Tool,
    ToolCall,
    ToolFunction,
    ToolFunctionParameter,
    ToolResult,
)

# ── Constants ────────────────────────────────────────────────────────────────

DEFAULT_HEAD_LIMIT = 100
GREP_TIMEOUT = 30  # seconds


# ── Tool Definition ──────────────────────────────────────────────────────────

GREP_TOOL = Tool(
    type="function",
    function=ToolFunction(
        name="grep",
        description="Search file contents using ripgrep.",
        parameters=ToolFunctionParameter(
            type="object",
            properties={
                "pattern": {
                    "type": "string",
                    "description": "Regex pattern to search for",
                },
                "path": {
                    "type": "string",
                    "description": "File or directory to search in",
                },
                "glob": {
                    "type": "string",
                    "description": "Glob pattern to filter files (e.g. '*.csv')",
                },
                "output_mode": {
                    "type": "string",
                    "enum": ["content", "files_with_matches", "count"],
                    "description": "Output mode (default: files_with_matches)",
                },
            },
        ),
        required=["pattern"],
    ),
)


# ── Pure Function Executor ───────────────────────────────────────────────────


async def exec_grep(
    tool_call: ToolCall,
    working_dir: Path | None = None,
) -> ToolResult:
    """Search file contents using ripgrep.

    Args:
        tool_call: The tool call with pattern and optional path/glob args
        working_dir: Base working directory (defaults to cwd)

    Returns:
        ToolResult with search results
    """
    args = tool_call.args
    pattern = args.get("pattern", "")

    if not pattern:
        return ToolResult(
            tool_call_id=tool_call.id,
            is_error=True,
            content="",
            error="pattern is required",
        )

    base_dir = working_dir or Path.cwd()

    cmd = ["rg"]
    output_mode = args.get("output_mode", "files_with_matches")

    if output_mode == "files_with_matches":
        cmd.append("-l")
    elif output_mode == "count":
        cmd.append("-c")
    else:
        cmd.append("-n")

    if args.get("glob"):
        cmd.extend(["--glob", args["glob"]])

    cmd.append(pattern)

    search_path = base_dir
    if args.get("path"):
        search_path = base_dir / args["path"]
    cmd.append(str(search_path))

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=GREP_TIMEOUT,
            cwd=str(base_dir),
        )

        output = result.stdout
        if not output and result.returncode == 1:
            return ToolResult(
                tool_call_id=tool_call.id,
                is_error=False,
                content=f"No matches found for: {pattern}",
            )

        # Truncate if too many results
        lines = output.strip().split("\n")
        if len(lines) > DEFAULT_HEAD_LIMIT:
            lines = lines[:DEFAULT_HEAD_LIMIT]
            output = "\n".join(lines) + "\n... (truncated)"
        else:
            output = "\n".join(lines)

        return ToolResult(
            tool_call_id=tool_call.id,
            is_error=False,
            content=output,
        )

    except subprocess.TimeoutExpired:
        return ToolResult(
            tool_call_id=tool_call.id,
            is_error=True,
            content="",
            error=f"grep timed out after {GREP_TIMEOUT}s",
        )
    except FileNotFoundError:
        return ToolResult(
            tool_call_id=tool_call.id,
            is_error=True,
            content="",
            error="ripgrep (rg) not found. Install with: brew install ripgrep",
        )
    except Exception as e:
        return ToolResult(
            tool_call_id=tool_call.id,
            is_error=True,
            content="",
            error=f"grep error: {e}",
        )
