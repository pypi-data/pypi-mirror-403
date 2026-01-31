"""TraceLens multi-rank collective report tool.

Pure function executor for generating multi-rank collective performance reports.
"""

from pathlib import Path

from wafer_core.lib.tracelens import generate_collective_report
from wafer_core.rollouts.dtypes import (
    Tool,
    ToolCall,
    ToolFunction,
    ToolFunctionParameter,
    ToolResult,
)


# ── Tool Definition ──────────────────────────────────────────────────────────

TRACELENS_COLLECTIVE_TOOL = Tool(
    type="function",
    function=ToolFunction(
        name="tracelens_collective",
        description=(
            "Generate multi-rank collective performance report from distributed training traces. "
            "Analyzes communication patterns across multiple GPUs/ranks, providing insights on "
            "collective operations, synchronization overhead, and scaling efficiency."
        ),
        parameters=ToolFunctionParameter(
            type="object",
            properties={
                "trace_dir": {
                    "type": "string",
                    "description": "Directory containing trace files for all ranks"
                },
                "world_size": {
                    "type": "integer",
                    "description": "Number of ranks (GPUs) in the distributed setup"
                },
                "output_path": {
                    "type": "string",
                    "description": "Output path for the collective report (optional)"
                },
            }
        ),
        required=["trace_dir", "world_size"]
    )
)


# ── Pure Function Executor ───────────────────────────────────────────────────

async def exec_tracelens_collective(
    tool_call: ToolCall,
    working_dir: Path,
) -> ToolResult:
    """Execute TraceLens multi-rank collective report generation.
    
    Args:
        tool_call: Tool call with arguments
        working_dir: Working directory for relative paths
        
    Returns:
        ToolResult with success/error status
    """
    # Validate required args
    if "trace_dir" not in tool_call.args:
        return ToolResult(
            tool_call_id=tool_call.id,
            is_error=True,
            content="",
            error="Missing required argument: 'trace_dir'"
        )
    
    if "world_size" not in tool_call.args:
        return ToolResult(
            tool_call_id=tool_call.id,
            is_error=True,
            content="",
            error="Missing required argument: 'world_size'"
        )
    
    trace_dir_str = tool_call.args["trace_dir"]
    trace_dir = Path(trace_dir_str)
    
    # Resolve relative paths
    if not trace_dir.is_absolute():
        trace_dir = working_dir / trace_dir
    
    # Parse args
    world_size = int(tool_call.args["world_size"])
    output_path = tool_call.args.get("output_path")
    
    # Resolve output_path relative to working_dir
    if output_path is not None:
        output_path_obj = Path(output_path)
        if not output_path_obj.is_absolute():
            output_path = str(working_dir / output_path_obj)
    
    # Call core library function
    result = generate_collective_report(
        trace_dir=str(trace_dir),
        world_size=world_size,
        output_path=output_path,
    )
    
    # Convert to ToolResult
    if result.success:
        content_lines = [
            "✓ Multi-rank collective report generated successfully",
            f"  Trace directory: {trace_dir}",
            f"  World size: {result.world_size}",
        ]
        if result.output_path:
            content_lines.append(f"  Output: {result.output_path}")
        
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
            error=result.error or "Collective report generation failed"
        )
