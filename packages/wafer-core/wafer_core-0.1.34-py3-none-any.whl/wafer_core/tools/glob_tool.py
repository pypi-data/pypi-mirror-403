"""Glob tool for finding files by pattern.

Pure function executor for file pattern matching.
"""

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


# ── Tool Definition ──────────────────────────────────────────────────────────

GLOB_TOOL = Tool(
    type="function",
    function=ToolFunction(
        name="glob",
        description="Find files matching a glob pattern.",
        parameters=ToolFunctionParameter(
            type="object",
            properties={
                "pattern": {
                    "type": "string",
                    "description": "Glob pattern (e.g. '**/*.csv', '*.json')",
                },
                "path": {
                    "type": "string",
                    "description": "Directory to search in (default: working directory)",
                },
            },
        ),
        required=["pattern"],
    ),
)


# ── Pure Function Executor ───────────────────────────────────────────────────


async def exec_glob(
    tool_call: ToolCall,
    working_dir: Path | None = None,
) -> ToolResult:
    """Find files matching a glob pattern.

    Args:
        tool_call: The tool call with pattern and optional path args
        working_dir: Base working directory (defaults to cwd)

    Returns:
        ToolResult with list of matching file paths
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
    search_path = base_dir
    if args.get("path"):
        search_path = base_dir / args["path"]

    if not search_path.exists():
        return ToolResult(
            tool_call_id=tool_call.id,
            is_error=True,
            content="",
            error=f"Directory not found: {args.get('path', search_path)}",
        )

    try:
        matches = list(search_path.glob(pattern))
        rel_paths = []
        for m in matches:
            if m.is_file():
                try:
                    rel_path = m.relative_to(base_dir)
                    rel_paths.append(str(rel_path))
                except ValueError:
                    rel_paths.append(str(m))

        rel_paths.sort()

        if len(rel_paths) > DEFAULT_HEAD_LIMIT:
            rel_paths = rel_paths[:DEFAULT_HEAD_LIMIT]
            output = "\n".join(rel_paths) + f"\n... (truncated to {DEFAULT_HEAD_LIMIT})"
        else:
            output = "\n".join(rel_paths) if rel_paths else "No files found"

        return ToolResult(
            tool_call_id=tool_call.id,
            is_error=False,
            content=f"Found {len(rel_paths)} files:\n{output}",
        )

    except Exception as e:
        return ToolResult(
            tool_call_id=tool_call.id,
            is_error=True,
            content="",
            error=f"glob error: {e}",
        )
