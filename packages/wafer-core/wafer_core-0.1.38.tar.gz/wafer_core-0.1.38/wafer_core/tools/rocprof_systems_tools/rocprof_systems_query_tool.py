"""ROCprofiler-Systems query tool.

Pure function executor for querying available metrics and components.
"""

from pathlib import Path

from wafer_core.lib.rocprofiler.systems.avail.query import (
    query_available_metrics,
    query_components,
    query_hw_counters,
)
from wafer_core.rollouts.dtypes import (
    Tool,
    ToolCall,
    ToolFunction,
    ToolFunctionParameter,
    ToolResult,
)


# ── Tool Definition ──────────────────────────────────────────────────────────

ROCPROF_SYSTEMS_QUERY_TOOL = Tool(
    type="function",
    function=ToolFunction(
        name="rocprof_systems_query",
        description="Query available metrics and components using ROCprofiler-Systems (rocprof-sys-avail). Returns information about available hardware counters, components, and metrics.",
        parameters=ToolFunctionParameter(
            type="object",
            properties={
                "query_type": {"type": "string", "description": "Type of query: 'metrics', 'components', 'hw_counters', or 'all' (default: 'metrics')"},
                "components": {"type": "boolean", "description": "List available components"},
                "hw_counters": {"type": "boolean", "description": "List available hardware counters"},
                "all_metrics": {"type": "boolean", "description": "List all available metrics"},
                "filter_pattern": {"type": "string", "description": "Filter results by regex pattern"},
                "category_filter": {"type": "string", "description": "Comma-separated category names to filter by"},
            }
        ),
        required=[]
    )
)


# ── Pure Function Executor ───────────────────────────────────────────────────

async def exec_rocprof_systems_query(
    tool_call: ToolCall,
    working_dir: Path,
) -> ToolResult:
    """Execute rocprof-systems query (pure function)."""
    query_type = tool_call.args.get("query_type", "metrics")
    components_flag = tool_call.args.get("components", False)
    hw_counters_flag = tool_call.args.get("hw_counters", False)
    all_metrics_flag = tool_call.args.get("all_metrics", False)
    filter_pattern = tool_call.args.get("filter_pattern")
    category_filter_str = tool_call.args.get("category_filter")

    # Parse category filter
    category_filter = None
    if category_filter_str:
        category_filter = [c.strip() for c in category_filter_str.split(",") if c.strip()]

    # Determine which query function to call based on query_type
    if query_type == "components":
        result = query_components(filter_pattern=filter_pattern, category_filter=category_filter)
    elif query_type == "hw_counters":
        result = query_hw_counters(filter_pattern=filter_pattern, category_filter=category_filter)
    elif query_type == "metrics" or query_type == "all":
        # Use query_available_metrics with flags
        result = query_available_metrics(
            components=components_flag or query_type == "all",
            hw_counters=hw_counters_flag or query_type == "all",
            all_metrics=all_metrics_flag or query_type == "all",
            filter_pattern=filter_pattern,
            category_filter=category_filter,
        )
    else:
        return ToolResult(
            tool_call_id=tool_call.id,
            is_error=True,
            content="",
            error=f"Unknown query_type: {query_type}. Use: 'metrics', 'components', 'hw_counters', or 'all'"
        )

    # Convert AvailResult to ToolResult
    if result.success:
        content_lines = [
            f"Query completed successfully.",
            f"Query type: {query_type}",
        ]
        if result.output:
            content_lines.append(f"\nResults:\n{result.output[:2000]}")  # Limit output preview

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
            error=result.error or "Query failed"
        )
