"""TraceLens report comparison tool.

Pure function executor for comparing two performance reports.
"""

from pathlib import Path

from wafer_core.lib.tracelens import compare_reports
from wafer_core.rollouts.dtypes import (
    Tool,
    ToolCall,
    ToolFunction,
    ToolFunctionParameter,
    ToolResult,
)


# Tool schema definition
TRACELENS_COMPARE_TOOL = Tool(
    type="function",
    function=ToolFunction(
        name="tracelens_compare",
        description=(
            "Compare two TraceLens performance reports to quantify differences. "
            "Useful for measuring optimization impact, regression detection, "
            "or comparing performance across different hardware."
        ),
        parameters=ToolFunctionParameter(
            type="object",
            properties={
                "baseline_path": {
                    "type": "string",
                    "description": "Path to baseline Excel report"
                },
                "candidate_path": {
                    "type": "string",
                    "description": "Path to candidate Excel report"
                },
                "output_path": {
                    "type": "string",
                    "description": "Output path for comparison (default: comparison.xlsx)"
                },
                "baseline_name": {
                    "type": "string",
                    "description": "Display name for baseline (default: 'baseline')"
                },
                "candidate_name": {
                    "type": "string",
                    "description": "Display name for candidate (default: 'candidate')"
                },
            }
        ),
        required=["baseline_path", "candidate_path"]
    )
)


async def exec_tracelens_compare(
    tool_call: ToolCall,
    working_dir: Path,
) -> ToolResult:
    """Execute TraceLens report comparison.
    
    Logic:
    1. Validate both required path arguments exist
    2. Resolve relative paths against working_dir
    3. Call compare_reports() from lib
    4. Convert CompareResult to ToolResult
    
    Args:
        tool_call: Tool call with arguments
        working_dir: Working directory for relative paths
        
    Returns:
        ToolResult with success/error status
    """
    # Validate required args
    if "baseline_path" not in tool_call.args:
        return ToolResult(
            tool_call_id=tool_call.id,
            is_error=True,
            content="",
            error="Missing required argument: 'baseline_path'"
        )
    
    if "candidate_path" not in tool_call.args:
        return ToolResult(
            tool_call_id=tool_call.id,
            is_error=True,
            content="",
            error="Missing required argument: 'candidate_path'"
        )
    
    # Resolve paths
    baseline = Path(tool_call.args["baseline_path"])
    candidate = Path(tool_call.args["candidate_path"])
    
    if not baseline.is_absolute():
        baseline = working_dir / baseline
    if not candidate.is_absolute():
        candidate = working_dir / candidate
    
    # Parse optional args
    output_path = tool_call.args.get("output_path")
    
    # Resolve output_path relative to working_dir
    if output_path is not None:
        output_path_obj = Path(output_path)
        if not output_path_obj.is_absolute():
            output_path = str(working_dir / output_path_obj)
    
    baseline_name = tool_call.args.get("baseline_name", "baseline")
    candidate_name = tool_call.args.get("candidate_name", "candidate")
    
    # Call core library function
    result = compare_reports(
        baseline_path=str(baseline),
        candidate_path=str(candidate),
        output_path=output_path,
        baseline_name=baseline_name,
        candidate_name=candidate_name,
    )
    
    # Convert to ToolResult
    if result.success:
        content_lines = [
            "✓ Comparison complete",
            f"  Output: {result.output_path}",
        ]
        if result.sheets_compared:
            content_lines.append(f"  Sheets: {', '.join(result.sheets_compared)}")
        
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
            error=result.error or "Comparison failed"
        )
