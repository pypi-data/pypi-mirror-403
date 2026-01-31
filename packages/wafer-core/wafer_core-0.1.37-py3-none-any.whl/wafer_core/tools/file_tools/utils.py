"""Shared utilities for file operation tools."""

from pathlib import Path

# Constants
MAX_LINES = 2000
MAX_LINE_LENGTH = 2000


def expand_path(file_path: str, working_dir: Path | None = None) -> Path:
    """Expand ~ to home directory and resolve path.

    Args:
        file_path: Path string (absolute or relative)
        working_dir: Base directory for relative paths. If None, uses process cwd.
    """
    if file_path == "~":
        return Path.home()
    if file_path.startswith("~/"):
        return Path.home() / file_path[2:]

    path = Path(file_path)
    if path.is_absolute():
        return path.resolve()

    # Resolve relative paths against working_dir
    if working_dir is not None:
        return (working_dir / path).resolve()
    return path.resolve()


def generate_diff(old_content: str, new_content: str, context_lines: int = 3) -> str:
    """Generate unified diff string with line numbers in gutter."""
    old_lines = old_content.split("\n")
    new_lines = new_content.split("\n")

    output = []
    max_line_num = max(len(old_lines), len(new_lines))
    line_num_width = len(str(max_line_num))

    # Find common prefix
    i = 0
    while i < len(old_lines) and i < len(new_lines) and old_lines[i] == new_lines[i]:
        i += 1

    # Find common suffix
    j_old = len(old_lines) - 1
    j_new = len(new_lines) - 1
    while j_old >= i and j_new >= i and old_lines[j_old] == new_lines[j_new]:
        j_old -= 1
        j_new -= 1

    # Show context before changes
    context_start = max(0, i - context_lines)
    if context_start > 0:
        output.append("     ...")

    for line_idx in range(context_start, i):
        line_num = str(line_idx + 1).rjust(line_num_width)
        output.append(f"{line_num}   {old_lines[line_idx]}")

    # Show removed lines
    for line_idx in range(i, j_old + 1):
        line_num = str(line_idx + 1).rjust(line_num_width)
        output.append(f"{line_num} - {old_lines[line_idx]}")

    # Show added lines
    new_line_start = i
    for idx, line_idx in enumerate(range(i, j_new + 1)):
        line_num = str(new_line_start + idx + 1).rjust(line_num_width)
        output.append(f"{line_num} + {new_lines[line_idx]}")

    # Show context after changes
    context_end = min(len(new_lines), j_new + 2 + context_lines)
    for line_idx in range(j_new + 1, context_end):
        line_num = str(line_idx + 1).rjust(line_num_width)
        output.append(f"{line_num}   {new_lines[line_idx]}")

    if context_end < len(new_lines):
        output.append("     ...")

    return "\n".join(output)
