"""TraceLens report generation tool.

Pure function executor for generating performance reports from traces.
"""

from pathlib import Path

from wafer_core.lib.tracelens import generate_perf_report
from wafer_core.lib.tracelens.types import TraceFormat
from wafer_core.rollouts.dtypes import (
    Tool,
    ToolCall,
    ToolFunction,
    ToolFunctionParameter,
    ToolResult,
)


# Tool schema definition
TRACELENS_REPORT_TOOL = Tool(
    type="function",
    function=ToolFunction(
        name="tracelens_report",
        description=(
            "Generate performance analysis report from GPU trace files (PyTorch, rocprofv3, JAX). "
            "Outputs Excel file with hierarchical breakdowns, kernel statistics, and efficiency metrics. "
            "Supports compressed traces (.zip, .gz)."
        ),
        parameters=ToolFunctionParameter(
            type="object",
            properties={
                "trace_path": {
                    "type": "string",
                    "description": "Path to trace file (.json, .zip, .gz, .pb)"
                },
                "output_path": {
                    "type": "string",
                    "description": "Output path for Excel report (optional, default: <trace>_perf_report.xlsx)"
                },
                "format": {
                    "type": "string",
                    "enum": ["auto", "pytorch", "rocprof", "jax"],
                    "description": "Trace format (default: auto-detect from file)"
                },
                "short_kernel_study": {
                    "type": "boolean",
                    "description": "Include analysis of short-duration kernels"
                },
                "kernel_details": {
                    "type": "boolean",
                    "description": "Include detailed per-kernel breakdown"
                },
            }
        ),
        required=["trace_path"]
    )
)


# Format string to enum mapping
_FORMAT_MAP = {
    "auto": TraceFormat.AUTO,
    "pytorch": TraceFormat.PYTORCH,
    "rocprof": TraceFormat.ROCPROF,
    "jax": TraceFormat.JAX,
}


async def exec_tracelens_report(
    tool_call: ToolCall,
    working_dir: Path,
) -> ToolResult:
    """Execute TraceLens report generation.
    
    Logic:
    1. Validate trace_path argument exists
    2. Resolve relative paths against working_dir
    3. Map format string to TraceFormat enum
    4. Call generate_perf_report() from lib
    5. Convert ReportResult to ToolResult
    
    Args:
        tool_call: Tool call with arguments
        working_dir: Working directory for relative paths
        
    Returns:
        ToolResult with success/error status
    """
    # Validate required args
    if "trace_path" not in tool_call.args:
        return ToolResult(
            tool_call_id=tool_call.id,
            is_error=True,
            content="",
            error="Missing required argument: 'trace_path'"
        )
    
    trace_path_str = tool_call.args["trace_path"]
    trace_path = Path(trace_path_str)
    
    # Resolve relative paths
    if not trace_path.is_absolute():
        trace_path = working_dir / trace_path
    
    # Parse optional args
    output_path = tool_call.args.get("output_path")
    
    # Resolve output_path relative to working_dir
    if output_path is not None:
        output_path_obj = Path(output_path)
        if not output_path_obj.is_absolute():
            output_path = str(working_dir / output_path_obj)
    format_str = tool_call.args.get("format", "auto")
    short_kernel = tool_call.args.get("short_kernel_study", False)
    kernel_details = tool_call.args.get("kernel_details", False)
    
    # Map format string to enum
    trace_format = _FORMAT_MAP.get(format_str, TraceFormat.AUTO)
    
    # Call core library function
    result = generate_perf_report(
        trace_path=str(trace_path),
        output_path=output_path,
        trace_format=trace_format,
        short_kernel_study=short_kernel,
        kernel_details=kernel_details,
    )
    
    # Convert to ToolResult
    if result.success:
        content_lines = [
            "✓ Performance report generated successfully",
            f"  Output: {result.output_path}",
            f"  Format: {result.trace_format}",
        ]
        if result.summary:
            content_lines.append(f"  Summary: {result.summary}")
        
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
            error=result.error or "Report generation failed"
        )
