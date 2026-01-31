"""Write file tool.

Pure function executor for writing file contents.
"""

from pathlib import Path

from wafer_core.rollouts.dtypes import (
    Tool,
    ToolCall,
    ToolFunction,
    ToolFunctionParameter,
    ToolResult,
)
from wafer_core.tools.file_tools.utils import expand_path

# ── Tool Definition ──────────────────────────────────────────────────────────

WRITE_TOOL = Tool(
    type="function",
    function=ToolFunction(
        name="write",
        description="Write content to a file. Creates the file if it doesn't exist, overwrites if it does. Automatically creates parent directories.",
        parameters=ToolFunctionParameter(
            type="object",
            properties={
                "path": {
                    "type": "string",
                    "description": "Path to the file to write (relative or absolute)",
                },
                "content": {"type": "string", "description": "Content to write to the file"},
            },
        ),
        required=["path", "content"],
    ),
)


# ── Pure Function Executor ───────────────────────────────────────────────────


async def exec_write(tool_call: ToolCall, working_dir: Path | None = None) -> ToolResult:
    """Write content to file.

    Args:
        tool_call: The tool call with path and content args.
        working_dir: Base directory for relative paths. If None, uses process cwd.
    """
    path_str = tool_call.args["path"]
    content = tool_call.args["content"]

    abs_path = expand_path(path_str, working_dir)

    # Create parent directories
    abs_path.parent.mkdir(parents=True, exist_ok=True)

    # Write file
    abs_path.write_text(content, encoding="utf-8")

    return ToolResult(
        tool_call_id=tool_call.id,
        is_error=False,
        content=f"Successfully wrote {len(content)} bytes to {path_str}",
    )
