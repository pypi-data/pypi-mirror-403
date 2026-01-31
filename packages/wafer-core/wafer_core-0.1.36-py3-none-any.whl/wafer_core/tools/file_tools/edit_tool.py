"""Edit file tool.

Pure function executor for editing file contents by replacing exact text.
"""

from pathlib import Path

from wafer_core.rollouts.dtypes import (
    Tool,
    ToolCall,
    ToolFunction,
    ToolFunctionParameter,
    ToolResult,
)
from wafer_core.tools.file_tools.utils import expand_path, generate_diff

# ── Tool Definition ──────────────────────────────────────────────────────────

EDIT_TOOL = Tool(
    type="function",
    function=ToolFunction(
        name="edit",
        description="Edit a file by replacing exact text. The old_text must match exactly (including whitespace). Use this for precise, surgical edits.",
        parameters=ToolFunctionParameter(
            type="object",
            properties={
                "path": {
                    "type": "string",
                    "description": "Path to the file to edit (relative or absolute)",
                },
                "old_text": {
                    "type": "string",
                    "description": "Exact text to find and replace (must match exactly)",
                },
                "new_text": {
                    "type": "string",
                    "description": "New text to replace the old text with",
                },
            },
        ),
        required=["path", "old_text", "new_text"],
    ),
)


# ── Pure Function Executor ───────────────────────────────────────────────────


async def exec_edit(tool_call: ToolCall, working_dir: Path | None = None) -> ToolResult:
    """Edit file by replacing exact text.

    Args:
        tool_call: The tool call with path, old_text, and new_text args.
        working_dir: Base directory for relative paths. If None, uses process cwd.
    """
    path_str = tool_call.args["path"]
    old_text = tool_call.args["old_text"]
    new_text = tool_call.args["new_text"]

    abs_path = expand_path(path_str, working_dir)

    if not abs_path.exists():
        return ToolResult(
            tool_call_id=tool_call.id,
            is_error=True,
            content="",
            error=f"File not found: {path_str}",
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

    # Check if old text exists
    if old_text not in content:
        return ToolResult(
            tool_call_id=tool_call.id,
            is_error=True,
            content="",
            error=f"Could not find the exact text in {path_str}. The old text must match exactly including all whitespace and newlines.",
        )

    # Count occurrences
    occurrences = content.count(old_text)
    if occurrences > 1:
        return ToolResult(
            tool_call_id=tool_call.id,
            is_error=True,
            content="",
            error=f"Found {occurrences} occurrences of the text in {path_str}. The text must be unique. Please provide more context to make it unique.",
        )

    # Perform replacement
    index = content.find(old_text)
    new_content = content[:index] + new_text + content[index + len(old_text) :]

    if content == new_content:
        return ToolResult(
            tool_call_id=tool_call.id,
            is_error=True,
            content="",
            error=f"No changes made to {path_str}. The replacement produced identical content.",
        )

    abs_path.write_text(new_content, encoding="utf-8")

    # Generate diff for UI display
    diff_str = generate_diff(content, new_content)

    return ToolResult(
        tool_call_id=tool_call.id,
        is_error=False,
        content=f"Successfully replaced text in {path_str}. Changed {len(old_text)} characters to {len(new_text)} characters.",
        details={"diff": diff_str},
    )
