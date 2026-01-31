"""ROCprofiler-Systems profile tool.

Pure function executor for rocprof-sys-run system profiling.
"""

import shlex
from pathlib import Path

from wafer_core.lib.rocprofiler.systems.run.profiler import run_systems_profile
from wafer_core.rollouts.dtypes import (
    Tool,
    ToolCall,
    ToolFunction,
    ToolFunctionParameter,
    ToolResult,
)


# ── Tool Definition ──────────────────────────────────────────────────────────

ROCPROF_SYSTEMS_PROFILE_TOOL = Tool(
    type="function",
    function=ToolFunction(
        name="rocprof_systems_profile",
        description="Profile a command with ROCprofiler-Systems (rocprof-sys-run). Returns system-level profiling results including traces, profiles, and metrics.",
        parameters=ToolFunctionParameter(
            type="object",
            properties={
                "command": {"type": "string", "description": "Command to profile (e.g., './my_app arg1')"},
                "output_dir": {"type": "string", "description": "Output directory for results"},
                "trace": {"type": "boolean", "description": "Generate detailed trace (Perfetto output, default: true)"},
                "profile": {"type": "boolean", "description": "Generate call-stack-based profile"},
                "flat_profile": {"type": "boolean", "description": "Generate flat profile (conflicts with profile)"},
                "sample": {"type": "boolean", "description": "Enable sampling profiling"},
                "host": {"type": "boolean", "description": "Enable sampling host-based metrics (CPU freq, memory, etc.)"},
                "device": {"type": "boolean", "description": "Enable sampling device-based metrics (GPU temp, memory, etc.)"},
                "wait": {"type": "number", "description": "Wait time before collecting data (seconds)"},
                "duration": {"type": "number", "description": "Duration of data collection (seconds)"},
                "use_rocm": {"type": "boolean", "description": "Enable ROCm backend (default: true)"},
                "use_sampling": {"type": "boolean", "description": "Enable sampling backend"},
                "use_kokkosp": {"type": "boolean", "description": "Enable Kokkos profiling backend"},
                "use_mpip": {"type": "boolean", "description": "Enable MPI profiling backend"},
                "use_rocpd": {"type": "boolean", "description": "Enable rocpd database output (SQLite)"},
                "backends": {"type": "string", "description": "Comma-separated list of backends (e.g., 'rocm,kokkosp,mpip')"},
            }
        ),
        required=["command"]
    )
)


# ── Pure Function Executor ───────────────────────────────────────────────────

async def exec_rocprof_systems_profile(
    tool_call: ToolCall,
    working_dir: Path,
) -> ToolResult:
    """Execute rocprof-systems profiling (pure function)."""
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
    trace = tool_call.args.get("trace", True)
    profile = tool_call.args.get("profile", False)
    flat_profile = tool_call.args.get("flat_profile", False)
    sample = tool_call.args.get("sample", False)
    host = tool_call.args.get("host", False)
    device = tool_call.args.get("device", False)
    wait = tool_call.args.get("wait")
    duration = tool_call.args.get("duration")
    use_rocm = tool_call.args.get("use_rocm", True)
    use_sampling = tool_call.args.get("use_sampling", False)
    use_kokkosp = tool_call.args.get("use_kokkosp", False)
    use_mpip = tool_call.args.get("use_mpip", False)
    use_rocpd = tool_call.args.get("use_rocpd", False)
    backends_str = tool_call.args.get("backends")

    # Parse command string into list
    cmd_list = shlex.split(command_str)

    # Parse backends if provided
    backends_list = None
    if backends_str:
        backends_list = [b.strip() for b in backends_str.split(",") if b.strip()]

    # Parse output directory
    output_dir = None
    if output_dir_str:
        output_dir = Path(output_dir_str)
        if not output_dir.is_absolute():
            output_dir = working_dir / output_dir

    # Call lib function
    result = run_systems_profile(
        command=cmd_list,
        output_dir=output_dir,
        trace=trace,
        profile=profile,
        flat_profile=flat_profile,
        sample=sample,
        host=host,
        device=device,
        wait=wait,
        duration=duration,
        use_rocm=use_rocm,
        use_sampling=use_sampling,
        use_kokkosp=use_kokkosp,
        use_mpip=use_mpip,
        use_rocpd=use_rocpd,
        backends=backends_list,
    )

    # Convert ProfileResult to ToolResult
    if result.success:
        content_lines = [
            f"System profiling completed successfully.",
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
