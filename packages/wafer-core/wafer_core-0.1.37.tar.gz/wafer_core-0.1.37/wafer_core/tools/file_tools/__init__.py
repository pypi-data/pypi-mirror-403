"""File operation tools.

Grouped file operations: read, write, edit, glob, grep.
"""

from wafer_core.tools.file_tools.edit_tool import EDIT_TOOL, exec_edit
from wafer_core.tools.file_tools.glob_tool import GLOB_TOOL, exec_glob
from wafer_core.tools.file_tools.grep_tool import GREP_TOOL, exec_grep
from wafer_core.tools.file_tools.read_tool import READ_TOOL, exec_read
from wafer_core.tools.file_tools.write_tool import WRITE_TOOL, exec_write

__all__ = [
    "READ_TOOL",
    "WRITE_TOOL",
    "EDIT_TOOL",
    "GLOB_TOOL",
    "GREP_TOOL",
    "exec_read",
    "exec_write",
    "exec_edit",
    "exec_glob",
    "exec_grep",
]
