"""ROCprofiler-Systems sample tool.

Pure function executor for rocprof-sys-sample sampling profiling.
"""

import shlex
from pathlib import Path

from wafer_core.lib.rocprofiler.systems.sample.profiler import run_sampling
from wafer_core.rollouts.dtypes import (
    Tool,
    ToolCall,
    ToolFunction,
    ToolFunctionParameter,
    ToolResult,
)


# ── Tool Definition ──────────────────────────────────────────────────────────

ROCPROF_SYSTEMS_SAMPLE_TOOL = Tool(
    type="function",
    function=ToolFunction(
        name="rocprof_systems_sample",
        description="Run sampling-based profiling with ROCprofiler-Systems (rocprof-sys-sample). Can be used standalone (attach to running processes) or with a command.",
        parameters=ToolFunctionParameter(
            type="object",
            properties={
                "command": {"type": "string", "description": "Command to profile (optional - can attach to running process)"},
                "output_dir": {"type": "string", "description": "Output directory for results"},
                "trace": {"type": "boolean", "description": "Generate detailed trace (Perfetto output)"},
                "profile": {"type": "boolean", "description": "Generate call-stack-based profile"},
                "flat_profile": {"type": "boolean", "description": "Generate flat profile (conflicts with profile)"},
                "host": {"type": "boolean", "description": "Enable sampling host-based metrics"},
                "device": {"type": "boolean", "description": "Enable sampling device-based metrics"},
                "freq": {"type": "integer", "description": "Sampling frequency in Hz"},
                "wait": {"type": "number", "description": "Wait time before collecting data (seconds)"},
                "duration": {"type": "number", "description": "Duration of data collection (seconds)"},
                "cpus": {"type": "string", "description": "Comma-separated CPU IDs to sample (e.g., '0,1,2')"},
                "gpus": {"type": "string", "description": "Comma-separated GPU IDs to sample"},
                "cputime": {"type": "boolean", "description": "Sample based on CPU time"},
                "realtime": {"type": "boolean", "description": "Sample based on real (wall) time"},
            }
        ),
        required=[]
    )
)


# ── Pure Function Executor ───────────────────────────────────────────────────

async def exec_rocprof_systems_sample(
    tool_call: ToolCall,
    working_dir: Path,
) -> ToolResult:
    """Execute rocprof-systems sampling (pure function)."""
    command_str = tool_call.args.get("command")
    output_dir_str = tool_call.args.get("output_dir")
    trace = tool_call.args.get("trace", False)
    profile = tool_call.args.get("profile", False)
    flat_profile = tool_call.args.get("flat_profile", False)
    host = tool_call.args.get("host", False)
    device = tool_call.args.get("device", False)
    freq = tool_call.args.get("freq")
    wait = tool_call.args.get("wait")
    duration = tool_call.args.get("duration")
    cpus_str = tool_call.args.get("cpus")
    gpus_str = tool_call.args.get("gpus")
    cputime = tool_call.args.get("cputime", False)
    realtime = tool_call.args.get("realtime", False)

    # Parse command string into list if provided
    cmd_list = None
    if command_str:
        cmd_list = shlex.split(command_str)

    # Parse CPU/GPU lists
    cpus_list = None
    if cpus_str:
        cpus_list = [int(c.strip()) for c in cpus_str.split(",") if c.strip()]

    gpus_list = None
    if gpus_str:
        gpus_list = [int(g.strip()) for g in gpus_str.split(",") if g.strip()]

    # Parse output directory
    output_dir = None
    if output_dir_str:
        output_dir = Path(output_dir_str)
        if not output_dir.is_absolute():
            output_dir = working_dir / output_dir

    # Call lib function
    result = run_sampling(
        command=cmd_list,
        output_dir=output_dir,
        trace=trace,
        profile=profile,
        flat_profile=flat_profile,
        host=host,
        device=device,
        freq=freq,
        wait=wait,
        duration=duration,
        cpus=cpus_list,
        gpus=gpus_list,
        cputime=cputime,
        realtime=realtime,
    )

    # Convert ProfileResult to ToolResult
    if result.success:
        content_lines = [
            f"Sampling profiling completed successfully.",
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
            error=result.error or "Sampling failed"
        )
