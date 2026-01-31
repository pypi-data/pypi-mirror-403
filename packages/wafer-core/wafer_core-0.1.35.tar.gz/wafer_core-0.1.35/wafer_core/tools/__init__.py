"""Tool executors.

Each file contains both a Tool schema definition and an exec_* function that returns ToolResult.
"""

from wafer_core.tools.bash_tool import (
    BASH_TOOL,
    ApprovalCallback,
    BashPermission,
    BashPermissionResult,
    check_bash_permissions,
    exec_bash,
)
from wafer_core.tools.capture_tool import (
    CAPTURE_TOOL,
    exec_capture,
)
from wafer_core.tools.file_tools import (
    EDIT_TOOL,
    GLOB_TOOL,
    GREP_TOOL,
    READ_TOOL,
    WRITE_TOOL,
    exec_edit,
    exec_glob,
    exec_grep,
    exec_read,
    exec_write,
)
from wafer_core.tools.rocprof_compute_tools import (
    ROCPROF_COMPUTE_ANALYZE_TOOL,
    ROCPROF_COMPUTE_PROFILE_TOOL,
    exec_rocprof_compute_analyze,
    exec_rocprof_compute_profile,
)
from wafer_core.tools.rocprof_sdk_tools import (
    ROCPROF_SDK_ANALYZE_TOOL,
    ROCPROF_SDK_PROFILE_TOOL,
    exec_rocprof_sdk_analyze,
    exec_rocprof_sdk_profile,
)
from wafer_core.tools.rocprof_systems_tools import (
    ROCPROF_SYSTEMS_INSTRUMENT_TOOL,
    ROCPROF_SYSTEMS_PROFILE_TOOL,
    ROCPROF_SYSTEMS_QUERY_TOOL,
    ROCPROF_SYSTEMS_SAMPLE_TOOL,
    exec_rocprof_systems_instrument,
    exec_rocprof_systems_profile,
    exec_rocprof_systems_query,
    exec_rocprof_systems_sample,
)
from wafer_core.tools.skill_tool import (
    SKILL_TOOL,
    exec_skill,
)
from wafer_core.tools.tracelens_tools import (
    TRACELENS_COLLECTIVE_TOOL,
    TRACELENS_COMPARE_TOOL,
    TRACELENS_REPORT_TOOL,
    exec_tracelens_collective,
    exec_tracelens_compare,
    exec_tracelens_report,
)
from wafer_core.tools.wafer_tool import (
    BLOCKED_WAFER_SUBCOMMANDS,
    WAFER_SUBCOMMANDS,
    WAFER_TOOL,
    exec_wafer,
)
from wafer_core.tools.write_kernel_tool import (
    WRITE_KERNEL_TOOL,
    KernelSubmission,
    exec_write_kernel,
)

__all__ = [
    # File tools
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
    # Bash tool
    "BASH_TOOL",
    "ApprovalCallback",
    "BashPermission",
    "BashPermissionResult",
    "check_bash_permissions",
    "exec_bash",
    # Skill tool
    "SKILL_TOOL",
    "exec_skill",
    # Wafer tool
    "WAFER_TOOL",
    "WAFER_SUBCOMMANDS",
    "BLOCKED_WAFER_SUBCOMMANDS",
    "exec_wafer",
    # Write kernel tool
    "WRITE_KERNEL_TOOL",
    "KernelSubmission",
    "exec_write_kernel",
    # ROCprofiler-SDK tools
    "ROCPROF_SDK_PROFILE_TOOL",
    "ROCPROF_SDK_ANALYZE_TOOL",
    "exec_rocprof_sdk_profile",
    "exec_rocprof_sdk_analyze",
    # ROCprofiler-Compute tools
    "ROCPROF_COMPUTE_PROFILE_TOOL",
    "ROCPROF_COMPUTE_ANALYZE_TOOL",
    "exec_rocprof_compute_profile",
    "exec_rocprof_compute_analyze",
    # ROCprofiler-Systems tools
    "ROCPROF_SYSTEMS_PROFILE_TOOL",
    "ROCPROF_SYSTEMS_SAMPLE_TOOL",
    "ROCPROF_SYSTEMS_INSTRUMENT_TOOL",
    "ROCPROF_SYSTEMS_QUERY_TOOL",
    "exec_rocprof_systems_profile",
    "exec_rocprof_systems_sample",
    "exec_rocprof_systems_instrument",
    "exec_rocprof_systems_query",
    # Capture tool
    "CAPTURE_TOOL",
    "exec_capture",
    # TraceLens tools
    "TRACELENS_REPORT_TOOL",
    "TRACELENS_COMPARE_TOOL",
    "TRACELENS_COLLECTIVE_TOOL",
    "exec_tracelens_report",
    "exec_tracelens_compare",
    "exec_tracelens_collective",
]
