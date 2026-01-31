"""Read file tool.

Pure function executor for reading file contents.
"""

from pathlib import Path

from wafer_core.rollouts.dtypes import (
    Tool,
    ToolCall,
    ToolFunction,
    ToolFunctionParameter,
    ToolResult,
)
from wafer_core.tools.file_tools.utils import MAX_LINE_LENGTH, MAX_LINES, expand_path

# ── Tool Definition ──────────────────────────────────────────────────────────

READ_TOOL = Tool(
    type="function",
    function=ToolFunction(
        name="read",
        description="Read the contents of a file. Defaults to first 2000 lines. Use offset/limit for large files.",
        parameters=ToolFunctionParameter(
            type="object",
            properties={
                "path": {
                    "type": "string",
                    "description": "Path to the file to read (relative or absolute)",
                },
                "offset": {
                    "type": "integer",
                    "description": "Line number to start reading from (1-indexed)",
                },
                "limit": {"type": "integer", "description": "Maximum number of lines to read"},
            },
        ),
        required=["path"],
    ),
)


# ── Pure Function Executor ───────────────────────────────────────────────────


async def exec_read(tool_call: ToolCall, working_dir: Path | None = None) -> ToolResult:
    """Read file contents.

    Args:
        tool_call: The tool call with path and optional offset/limit args.
        working_dir: Base directory for relative paths. If None, uses process cwd.
    """
    path_str = tool_call.args["path"]
    offset = tool_call.args.get("offset")
    limit = tool_call.args.get("limit")

    abs_path = expand_path(path_str, working_dir)

    if not abs_path.exists():
        return ToolResult(
            tool_call_id=tool_call.id,
            is_error=True,
            content="",
            error=f"File not found: {path_str}",
        )

    if not abs_path.is_file():
        return ToolResult(
            tool_call_id=tool_call.id, is_error=True, content="", error=f"Not a file: {path_str}"
        )

    try:
        content = abs_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return ToolResult(
            tool_call_id=tool_call.id,
            is_error=True,
            content="",
            error=f"Cannot read binary file: {path_str}",
        )

    lines = content.split("\n")

    # Apply offset and limit
    start_line = (offset - 1) if offset else 0  # 1-indexed to 0-indexed
    max_lines = limit or MAX_LINES
    end_line = min(start_line + max_lines, len(lines))

    if start_line >= len(lines):
        return ToolResult(
            tool_call_id=tool_call.id,
            is_error=True,
            content="",
            error=f"Offset {offset} is beyond end of file ({len(lines)} lines total)",
        )

    selected_lines = lines[start_line:end_line]

    # Truncate long lines
    had_truncated = False
    formatted_lines = []
    for line in selected_lines:
        if len(line) > MAX_LINE_LENGTH:
            had_truncated = True
            formatted_lines.append(line[:MAX_LINE_LENGTH])
        else:
            formatted_lines.append(line)

    output_text = "\n".join(formatted_lines)

    # Add notices
    notices = []
    if had_truncated:
        notices.append(f"Some lines were truncated to {MAX_LINE_LENGTH} characters")
    if end_line < len(lines):
        remaining = len(lines) - end_line
        notices.append(f"{remaining} more lines not shown. Use offset={end_line + 1} to continue")

    if notices:
        output_text += f"\n\n... ({'. '.join(notices)})"

    return ToolResult(tool_call_id=tool_call.id, is_error=False, content=output_text)
