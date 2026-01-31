"""ROCprofiler-Systems instrument tool.

Pure function executor for rocprof-sys-instrument binary instrumentation.
"""

import shlex
from pathlib import Path

from wafer_core.lib.rocprofiler.systems.instrument.profiler import run_instrumentation
from wafer_core.rollouts.dtypes import (
    Tool,
    ToolCall,
    ToolFunction,
    ToolFunctionParameter,
    ToolResult,
)


# ── Tool Definition ──────────────────────────────────────────────────────────

ROCPROF_SYSTEMS_INSTRUMENT_TOOL = Tool(
    type="function",
    function=ToolFunction(
        name="rocprof_systems_instrument",
        description="Run binary instrumentation with ROCprofiler-Systems (rocprof-sys-instrument). Instruments a binary using Dyninst to collect function call information, coverage data, and other runtime metrics.",
        parameters=ToolFunctionParameter(
            type="object",
            properties={
                "command": {"type": "string", "description": "Command to instrument and run (e.g., './my_app arg1')"},
                "output": {"type": "string", "description": "Output directory for instrumentation results"},
                "function_include": {"type": "string", "description": "Comma-separated function patterns to instrument (regex/glob)"},
                "function_exclude": {"type": "string", "description": "Comma-separated function patterns to exclude"},
                "module_include": {"type": "string", "description": "Comma-separated module patterns to instrument"},
                "module_exclude": {"type": "string", "description": "Comma-separated module patterns to exclude"},
                "instrument_loops": {"type": "boolean", "description": "Enable loop instrumentation"},
                "coverage": {"type": "boolean", "description": "Enable code coverage mode"},
                "simulate": {"type": "boolean", "description": "Simulate instrumentation (dry run, outputs diagnostics)"},
                "verbose": {"type": "boolean", "description": "Enable verbose output"},
            }
        ),
        required=["command"]
    )
)


# ── Pure Function Executor ───────────────────────────────────────────────────

async def exec_rocprof_systems_instrument(
    tool_call: ToolCall,
    working_dir: Path,
) -> ToolResult:
    """Execute rocprof-systems instrumentation (pure function)."""
    # Validate required args
    if "command" not in tool_call.args:
        return ToolResult(
            tool_call_id=tool_call.id,
            is_error=True,
            content="",
            error="Missing required argument: 'command'"
        )

    command_str = tool_call.args["command"]
    output_str = tool_call.args.get("output")
    function_include_str = tool_call.args.get("function_include")
    function_exclude_str = tool_call.args.get("function_exclude")
    module_include_str = tool_call.args.get("module_include")
    module_exclude_str = tool_call.args.get("module_exclude")
    instrument_loops = tool_call.args.get("instrument_loops", False)
    coverage = tool_call.args.get("coverage", False)
    simulate = tool_call.args.get("simulate", False)
    verbose = tool_call.args.get("verbose", False)

    # Parse command string into list
    cmd_list = shlex.split(command_str)

    # Parse filter lists
    function_include = None
    if function_include_str:
        function_include = [f.strip() for f in function_include_str.split(",") if f.strip()]

    function_exclude = None
    if function_exclude_str:
        function_exclude = [f.strip() for f in function_exclude_str.split(",") if f.strip()]

    module_include = None
    if module_include_str:
        module_include = [m.strip() for m in module_include_str.split(",") if m.strip()]

    module_exclude = None
    if module_exclude_str:
        module_exclude = [m.strip() for m in module_exclude_str.split(",") if m.strip()]

    # Parse output directory
    output = None
    if output_str:
        output = Path(output_str)
        if not output.is_absolute():
            output = working_dir / output

    # Call lib function
    result = run_instrumentation(
        command=cmd_list,
        output=output,
        function_include=function_include,
        function_exclude=function_exclude,
        module_include=module_include,
        module_exclude=module_exclude,
        instrument_loops=instrument_loops,
        coverage=coverage,
        simulate=simulate,
        verbose=verbose,
    )

    # Convert ProfileResult to ToolResult
    if result.success:
        content_lines = [
            f"Binary instrumentation completed successfully.",
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
            error=result.error or "Instrumentation failed"
        )
