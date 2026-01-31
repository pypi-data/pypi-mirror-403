"""ROCprofiler-Compute analyze tool.

Pure function executor for analyzing rocprof-compute workload data.
"""

from pathlib import Path

from wafer_core.lib.rocprofiler.compute.profiler import run_analysis
from wafer_core.rollouts.dtypes import (
    Tool,
    ToolCall,
    ToolFunction,
    ToolFunctionParameter,
    ToolResult,
)


# ── Tool Definition ──────────────────────────────────────────────────────────

ROCPROF_COMPUTE_ANALYZE_TOOL = Tool(
    type="function",
    function=ToolFunction(
        name="rocprof_compute_analyze",
        description="Analyze existing ROCprofiler-Compute workload data. Useful for re-analyzing data with different filters without re-profiling.",
        parameters=ToolFunctionParameter(
            type="object",
            properties={
                "workload_path": {"type": "string", "description": "Path to workload directory containing profiling results"},
                "kernel_filter": {"type": "string", "description": "Comma-separated kernel IDs to filter"},
                "dispatch_filter": {"type": "string", "description": "Comma-separated dispatch IDs to filter"},
                "block_filter": {"type": "string", "description": "Comma-separated metric IDs to filter"},
                "output_file": {"type": "string", "description": "Path to save analysis results"},
                "list_stats": {"type": "boolean", "description": "List all detected kernels and dispatches"},
                "list_metrics": {"type": "string", "description": "List available metrics for architecture (e.g., 'gfx90a')"},
                "verbose": {"type": "integer", "description": "Verbosity level 0-3 (default: 0)"},
            }
        ),
        required=["workload_path"]
    )
)


# ── Pure Function Executor ───────────────────────────────────────────────────

async def exec_rocprof_compute_analyze(
    tool_call: ToolCall,
    working_dir: Path,
) -> ToolResult:
    """Execute rocprof-compute analysis (pure function)."""
    # Validate required args
    if "workload_path" not in tool_call.args:
        return ToolResult(
            tool_call_id=tool_call.id,
            is_error=True,
            content="",
            error="Missing required argument: 'workload_path'"
        )

    workload_path_str = tool_call.args["workload_path"]
    kernel_filter_str = tool_call.args.get("kernel_filter")
    dispatch_filter_str = tool_call.args.get("dispatch_filter")
    block_filter_str = tool_call.args.get("block_filter")
    output_file_str = tool_call.args.get("output_file")
    list_stats = tool_call.args.get("list_stats", False)
    list_metrics = tool_call.args.get("list_metrics")
    verbose = tool_call.args.get("verbose", 0)

    # Parse workload path
    workload_path = Path(workload_path_str)
    if not workload_path.is_absolute():
        workload_path = working_dir / workload_path

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

    # Call lib function
    result = run_analysis(
        workload_path=str(workload_path),
        kernel_filter=kernel_filter,
        dispatch_filter=dispatch_filter,
        block_filter=block_filter,
        output_file=output_file_str,
        list_stats=list_stats,
        list_metrics=list_metrics,
        verbose=verbose,
    )

    # Convert ProfileResult to ToolResult
    if result.success:
        content_lines = [
            f"Analysis completed successfully.",
            f"Workload path: {workload_path_str}",
        ]
        if result.output_files:
            content_lines.append(f"\nGenerated {len(result.output_files)} output file(s):")
            for f in result.output_files:
                content_lines.append(f"  - {f}")
        if result.stdout:
            content_lines.append(f"\nOutput:\n{result.stdout[:1000]}")  # Limit stdout preview

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
