"""ROCprofiler-SDK analyze tool.

Pure function executor for analyzing rocprofv3 output files.
"""

from pathlib import Path

from wafer_core.lib.rocprofiler.sdk.analyzer import analyze_csv, analyze_file, analyze_json, analyze_rocpd
from wafer_core.rollouts.dtypes import (
    Tool,
    ToolCall,
    ToolFunction,
    ToolFunctionParameter,
    ToolResult,
)


# ── Tool Definition ──────────────────────────────────────────────────────────

ROCPROF_SDK_ANALYZE_TOOL = Tool(
    type="function",
    function=ToolFunction(
        name="rocprof_sdk_analyze",
        description="Analyze ROCprofiler-SDK output files (CSV, JSON, rocpd). Returns kernel metrics and summary statistics.",
        parameters=ToolFunctionParameter(
            type="object",
            properties={
                "file_path": {"type": "string", "description": "Path to rocprofiler output file (.csv, .json, .db, .rocpd)"},
                "format": {"type": "string", "description": "File format: csv, json, rocpd, or auto (default: auto-detect)"},
            }
        ),
        required=["file_path"]
    )
)


# ── Pure Function Executor ───────────────────────────────────────────────────

async def exec_rocprof_sdk_analyze(
    tool_call: ToolCall,
    working_dir: Path,
) -> ToolResult:
    """Execute rocprof-sdk analysis (pure function)."""
    # Validate required args
    if "file_path" not in tool_call.args:
        return ToolResult(
            tool_call_id=tool_call.id,
            is_error=True,
            content="",
            error="Missing required argument: 'file_path'"
        )

    file_path_str = tool_call.args["file_path"]
    format_hint = tool_call.args.get("format", "auto")

    # Parse file path
    file_path = Path(file_path_str)
    if not file_path.is_absolute():
        file_path = working_dir / file_path

    if not file_path.exists():
        return ToolResult(
            tool_call_id=tool_call.id,
            is_error=True,
            content="",
            error=f"File not found: {file_path_str}"
        )

    # Call appropriate analyzer
    if format_hint == "auto":
        result = analyze_file(file_path)
    elif format_hint == "csv":
        result = analyze_csv(file_path)
    elif format_hint == "json":
        result = analyze_json(file_path)
    elif format_hint == "rocpd":
        result = analyze_rocpd(file_path)
    else:
        return ToolResult(
            tool_call_id=tool_call.id,
            is_error=True,
            content="",
            error=f"Unsupported format: {format_hint}. Use: csv, json, rocpd, or auto"
        )

    # Convert AnalysisResult to ToolResult
    if result.success:
        content_lines = [
            f"Analysis completed successfully.",
            f"File format: {result.file_format}",
        ]
        if result.summary:
            summary = result.summary
            content_lines.append(f"\nSummary:")
            content_lines.append(f"  Total kernels: {summary.get('total_kernels', 0)}")
            if "total_duration_ms" in summary:
                content_lines.append(f"  Total duration: {summary['total_duration_ms']:.2f} ms")
            if "avg_duration_ms" in summary:
                content_lines.append(f"  Average duration: {summary['avg_duration_ms']:.2f} ms")
        if result.kernels:
            content_lines.append(f"\nKernels ({len(result.kernels)}):")
            for kernel in result.kernels[:10]:  # Limit to first 10
                kernel_info = f"  - {kernel.name}"
                if kernel.duration_ns:
                    kernel_info += f" ({kernel.duration_ns / 1_000_000:.2f} ms)"
                content_lines.append(kernel_info)
            if len(result.kernels) > 10:
                content_lines.append(f"  ... and {len(result.kernels) - 10} more")

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
            error=result.error or "Analysis failed"
        )
