"""ROCprofiler-Compute profile tool.

Pure function executor for rocprof-compute profiling.
"""

import shlex
from pathlib import Path

from wafer_core.lib.rocprofiler.compute.profiler import run_profile
from wafer_core.rollouts.dtypes import (
    Tool,
    ToolCall,
    ToolFunction,
    ToolFunctionParameter,
    ToolResult,
)


# ── Tool Definition ──────────────────────────────────────────────────────────

ROCPROF_COMPUTE_PROFILE_TOOL = Tool(
    type="function",
    function=ToolFunction(
        name="rocprof_compute_profile",
        description="Profile a command with ROCprofiler-Compute (rocprof-compute). Returns profiling results including roofline data, memory analysis, and kernel statistics.",
        parameters=ToolFunctionParameter(
            type="object",
            properties={
                "command": {"type": "string", "description": "Command to profile (e.g., './my_kernel arg1')"},
                "workload_name": {"type": "string", "description": "Name for the workload (used in output path, required)"},
                "workload_path": {"type": "string", "description": "Base path for workload directory (default: ./workloads/<name>)"},
                "kernel_filter": {"type": "string", "description": "Comma-separated kernel names to filter"},
                "dispatch_filter": {"type": "string", "description": "Comma-separated dispatch IDs to filter"},
                "block_filter": {"type": "string", "description": "Comma-separated hardware blocks or metric IDs to filter"},
                "no_roof": {"type": "boolean", "description": "Skip roofline data collection (faster profiling)"},
                "roof_only": {"type": "boolean", "description": "Profile roofline data only (fastest, no detailed metrics)"},
                "hip_trace": {"type": "boolean", "description": "Enable HIP trace collection"},
                "verbose": {"type": "integer", "description": "Verbosity level 0-3 (default: 0)"},
            }
        ),
        required=["command", "workload_name"]
    )
)


# ── Pure Function Executor ───────────────────────────────────────────────────

async def exec_rocprof_compute_profile(
    tool_call: ToolCall,
    working_dir: Path,
) -> ToolResult:
    """Execute rocprof-compute profiling (pure function)."""
    # Validate required args
    if "command" not in tool_call.args:
        return ToolResult(
            tool_call_id=tool_call.id,
            is_error=True,
            content="",
            error="Missing required argument: 'command'"
        )
    if "workload_name" not in tool_call.args:
        return ToolResult(
            tool_call_id=tool_call.id,
            is_error=True,
            content="",
            error="Missing required argument: 'workload_name'"
        )

    command_str = tool_call.args["command"]
    workload_name = tool_call.args["workload_name"]
    workload_path_str = tool_call.args.get("workload_path")
    kernel_filter_str = tool_call.args.get("kernel_filter")
    dispatch_filter_str = tool_call.args.get("dispatch_filter")
    block_filter_str = tool_call.args.get("block_filter")
    no_roof = tool_call.args.get("no_roof", False)
    roof_only = tool_call.args.get("roof_only", False)
    hip_trace = tool_call.args.get("hip_trace", False)
    verbose = tool_call.args.get("verbose", 0)

    # Parse command string into list
    cmd_list = shlex.split(command_str)

    # Parse filters
    kernel_filter = None
    if kernel_filter_str:
        kernel_filter = [k.strip() for k in kernel_filter_str.split(",") if k.strip()]

    dispatch_filter = None
    if dispatch_filter_str:
        dispatch_filter = [int(d.strip()) for d in dispatch_filter_str.split(",") if d.strip()]

    block_filter = None
    if block_filter_str:
        block_filter = [b.strip() for b in block_filter_str.split(",") if b.strip()]

    # Parse workload path
    workload_path = None
    if workload_path_str:
        workload_path = Path(workload_path_str)
        if not workload_path.is_absolute():
            workload_path = working_dir / workload_path

    # Call lib function
    result = run_profile(
        target_command=cmd_list,
        workload_name=workload_name,
        workload_path=workload_path,
        kernel_filter=kernel_filter,
        dispatch_filter=dispatch_filter,
        block_filter=block_filter,
        no_roof=no_roof,
        roof_only=roof_only,
        hip_trace=hip_trace,
        verbose=verbose,
    )

    # Convert ProfileResult to ToolResult
    if result.success:
        content_lines = [
            f"Profiling completed successfully.",
            f"Workload name: {workload_name}",
        ]
        if result.workload_path:
            content_lines.append(f"Workload path: {result.workload_path}")
        if result.output_files:
            content_lines.append(f"\nGenerated {len(result.output_files)} output file(s):")
            for f in result.output_files[:10]:  # Limit to first 10
                content_lines.append(f"  - {f}")
            if len(result.output_files) > 10:
                content_lines.append(f"  ... and {len(result.output_files) - 10} more")
        if result.stdout:
            content_lines.append(f"\nOutput:\n{result.stdout[:500]}")  # Limit stdout preview

        return ToolResult(
            tool_call_id=tool_call.id,
            is_error=False,
            content="\n".join(content_lines)
        )
    else:
        return ToolResult(
            tool_call_id=tool_call.id,
            is_error=True,
            content="",
            error=result.error or "Profiling failed"
        )
