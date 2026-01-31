"""Glob tool for finding files by pattern."""

from pathlib import Path

from wafer_core.rollouts.dtypes import (
    Tool,
    ToolCall,
    ToolFunction,
    ToolFunctionParameter,
    ToolResult,
)

GLOB_TOOL = Tool(
    type="function",
    function=ToolFunction(
        name="glob",
        description=(
            "Find files matching a glob pattern. "
            "Returns list of file paths sorted by modification time (most recent first). "
            "Use this to find files by name, extension, or directory structure."
        ),
        parameters=ToolFunctionParameter(
            type="object",
            properties={
                "pattern": {
                    "type": "string",
                    "description": (
                        "Glob pattern to match files. "
                        "Examples: '**/*.py', 'src/**/*.ts', '**/test_*.py'"
                    ),
                },
                "path": {
                    "type": "string",
                    "description": "Directory to search in (defaults to current directory)",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of files to return (default: 100)",
                },
            },
        ),
        required=["pattern"],
    ),
)


async def exec_glob(tool_call: ToolCall, working_dir: Path) -> ToolResult:
    """Execute glob to find files."""
    args = tool_call.args
    pattern = args.get("pattern")
    search_path = args.get("path", ".")
    max_results = args.get("max_results", 100)

    if not pattern:
        return ToolResult(
            tool_call_id=tool_call.id,
            is_error=True,
            content="",
            error="'pattern' is required",
        )

    # Resolve search path
    full_path = working_dir / search_path
    if not full_path.exists():
        return ToolResult(
            tool_call_id=tool_call.id,
            is_error=True,
            content="",
            error=f"Path does not exist: {search_path}",
        )

    if not full_path.is_dir():
        return ToolResult(
            tool_call_id=tool_call.id,
            is_error=True,
            content="",
            error=f"Path is not a directory: {search_path}",
        )

    # Find matching files
    try:
        matches = list(full_path.glob(pattern))
        matches = [f for f in matches if f.is_file()]
    except Exception as e:
        return ToolResult(
            tool_call_id=tool_call.id,
            is_error=True,
            content="",
            error=f"Invalid glob pattern: {e}",
        )

    if not matches:
        return ToolResult(
            tool_call_id=tool_call.id,
            is_error=False,
            content=f"No files found matching pattern: {pattern}",
        )

    # Sort by modification time (most recent first)
    matches.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    matches = matches[:max_results]

    # Format results as relative paths
    rel_paths = []
    for f in matches:
        try:
            rel_paths.append(str(f.relative_to(working_dir)))
        except ValueError:
            rel_paths.append(str(f))

    result_lines = [f"Found {len(rel_paths)} files:"]
    result_lines.extend(f"  {p}" for p in rel_paths)

    return ToolResult(
        tool_call_id=tool_call.id,
        is_error=False,
        content="\n".join(result_lines),
    )
