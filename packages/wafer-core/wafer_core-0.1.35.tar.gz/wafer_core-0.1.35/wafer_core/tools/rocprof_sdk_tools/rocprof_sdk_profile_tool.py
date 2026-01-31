"""ROCprofiler-SDK profile tool.

Pure function executor for rocprofv3 profiling.
"""

import shlex
from pathlib import Path

from wafer_core.lib.rocprofiler.sdk.profiler import run_profile
from wafer_core.rollouts.dtypes import (
    Tool,
    ToolCall,
    ToolFunction,
    ToolFunctionParameter,
    ToolResult,
)


# ── Tool Definition ──────────────────────────────────────────────────────────

ROCPROF_SDK_PROFILE_TOOL = Tool(
    type="function",
    function=ToolFunction(
        name="rocprof_sdk_profile",
        description="Profile a command with ROCprofiler-SDK (rocprofv3). Returns profiling results including kernel metrics, traces, and hardware counters.",
        parameters=ToolFunctionParameter(
            type="object",
            properties={
                "command": {"type": "string", "description": "Command to profile (e.g., './my_kernel arg1')"},
                "output_dir": {"type": "string", "description": "Output directory for results"},
                "output_format": {"type": "string", "description": "Output format: csv, json, rocpd, pftrace, otf2 (default: csv)"},
                "counters": {"type": "string", "description": "Comma-separated hardware counters (e.g., 'SQ_WAVES,L2_CACHE_HITS')"},
                "kernel_include": {"type": "string", "description": "Include only kernels matching this regex"},
                "kernel_exclude": {"type": "string", "description": "Exclude kernels matching this regex"},
                "trace_hip_runtime": {"type": "boolean", "description": "Enable HIP runtime API tracing"},
                "trace_hip_compiler": {"type": "boolean", "description": "Enable HIP compiler code tracing"},
                "trace_hsa": {"type": "boolean", "description": "Enable HSA API tracing"},
                "trace_marker": {"type": "boolean", "description": "Enable ROCTx marker tracing"},
                "trace_memory_copy": {"type": "boolean", "description": "Enable memory copy operation tracing"},
            }
        ),
        required=["command"]
    )
)


# ── Pure Function Executor ───────────────────────────────────────────────────

async def exec_rocprof_sdk_profile(
    tool_call: ToolCall,
    working_dir: Path,
) -> ToolResult:
    """Execute rocprof-sdk profiling (pure function)."""
    # Validate required args
    if "command" not in tool_call.args:
        return ToolResult(
            tool_call_id=tool_call.id,
            is_error=True,
            content="",
            error="Missing required argument: 'command'"
        )

    command_str = tool_call.args["command"]
    output_dir_str = tool_call.args.get("output_dir")
    output_format = tool_call.args.get("output_format", "csv")
    counters_str = tool_call.args.get("counters")
    kernel_include = tool_call.args.get("kernel_include")
    kernel_exclude = tool_call.args.get("kernel_exclude")
    trace_hip_runtime = tool_call.args.get("trace_hip_runtime", False)
    trace_hip_compiler = tool_call.args.get("trace_hip_compiler", False)
    trace_hsa = tool_call.args.get("trace_hsa", False)
    trace_marker = tool_call.args.get("trace_marker", False)
    trace_memory_copy = tool_call.args.get("trace_memory_copy", False)

    # Parse command string into list
    cmd_list = shlex.split(command_str)

    # Parse counters if provided
    counters_list = None
    if counters_str:
        counters_list = [c.strip() for c in counters_str.split(",") if c.strip()]

    # Parse output directory
    output_dir = None
    if output_dir_str:
        output_dir = Path(output_dir_str)
        if not output_dir.is_absolute():
            output_dir = working_dir / output_dir

    # Call lib function
    result = run_profile(
        command=cmd_list,
        output_dir=output_dir,
        output_format=output_format,
        counters=counters_list,
        kernel_include_regex=kernel_include,
        kernel_exclude_regex=kernel_exclude,
        trace_hip_runtime=trace_hip_runtime,
        trace_hip_compiler=trace_hip_compiler,
        trace_hsa=trace_hsa,
        trace_marker=trace_marker,
        trace_memory_copy=trace_memory_copy,
    )

    # Convert ProfileResult to ToolResult
    if result.success:
        content_lines = [
            f"Profiling completed successfully.",
            f"Output format: {output_format}",
        ]
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
