"""Grep tool using ripgrep (with fallback to standard grep)."""

from pathlib import Path

from wafer_core.rollouts.dtypes import (
    Tool,
    ToolCall,
    ToolFunction,
    ToolFunctionParameter,
    ToolResult,
)

GREP_TOOL = Tool(
    type="function",
    function=ToolFunction(
        name="grep",
        description=(
            "Search for a pattern in files. "
            "Returns matching lines with file paths and line numbers. "
            "Supports regex patterns by default."
        ),
        parameters=ToolFunctionParameter(
            type="object",
            properties={
                "pattern": {
                    "type": "string",
                    "description": "Regex pattern to search for",
                },
                "path": {
                    "type": "string",
                    "description": "File or directory to search in (defaults to current directory)",
                },
                "glob": {
                    "type": "string",
                    "description": "Glob pattern to filter files (e.g., '*.py', '*.{ts,tsx}')",
                },
                "case_insensitive": {
                    "type": "boolean",
                    "description": "Case insensitive search (default: false)",
                },
                "context_lines": {
                    "type": "integer",
                    "description": "Number of context lines before and after match",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of matches to return (default: 50)",
                },
            },
        ),
        required=["pattern"],
    ),
)


async def exec_grep(tool_call: ToolCall, working_dir: Path) -> ToolResult:
    """Execute grep using ripgrep (preferred) or standard grep (fallback)."""
    import shutil
    import subprocess

    args = tool_call.args
    pattern = args.get("pattern")
    search_path = args.get("path", ".")
    glob_pattern = args.get("glob")
    case_insensitive = args.get("case_insensitive", False)
    context_lines = args.get("context_lines")
    max_results = args.get("max_results", 50)

    if not pattern:
        return ToolResult(
            tool_call_id=tool_call.id,
            is_error=True,
            content="",
            error="'pattern' is required",
        )

    # Try ripgrep first, fall back to standard grep
    rg_path = shutil.which("rg")
    grep_path = shutil.which("grep")
    
    if rg_path:
        # Use ripgrep (faster, better defaults)
        cmd = [rg_path, "--line-number", "--no-heading", "--color=never"]
        
        if case_insensitive:
            cmd.append("--ignore-case")
        
        if context_lines:
            cmd.extend(["--context", str(context_lines)])
        
        if glob_pattern:
            cmd.extend(["--glob", glob_pattern])
        
        # Limit results
        cmd.extend(["--max-count", str(max_results)])
        
        cmd.append(pattern)
        cmd.append(search_path)
        use_ripgrep = True
    elif grep_path:
        # Fallback to standard grep
        cmd = [grep_path, "-r", "-n", "--color=never"]
        
        if case_insensitive:
            cmd.append("-i")
        
        if context_lines:
            cmd.extend(["-C", str(context_lines)])
        
        if glob_pattern:
            # Standard grep uses --include for glob patterns
            cmd.extend(["--include", glob_pattern])
        
        cmd.append(pattern)
        cmd.append(search_path)
        use_ripgrep = False
    else:
        return ToolResult(
            tool_call_id=tool_call.id,
            is_error=True,
            content="",
            error="Neither ripgrep (rg) nor grep found. Please install one.",
        )

    # Run the search
    try:
        result = subprocess.run(
            cmd,
            cwd=working_dir,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        return ToolResult(
            tool_call_id=tool_call.id,
            is_error=True,
            content="",
            error="Search timed out after 30 seconds",
        )
    except Exception as e:
        return ToolResult(
            tool_call_id=tool_call.id,
            is_error=True,
            content="",
            error=f"Search failed: {e}",
        )

    # Both ripgrep and grep return exit code 1 for no matches (not an error)
    if result.returncode not in (0, 1):
        tool_name = "ripgrep" if use_ripgrep else "grep"
        return ToolResult(
            tool_call_id=tool_call.id,
            is_error=True,
            content="",
            error=result.stderr or f"{tool_name} exited with code {result.returncode}",
        )

    output = result.stdout.strip()
    if not output:
        return ToolResult(
            tool_call_id=tool_call.id,
            is_error=False,
            content=f"No matches found for pattern: {pattern}",
        )

    # Count matches and limit output for standard grep
    lines = output.split("\n")
    if not use_ripgrep and len(lines) > max_results:
        lines = lines[:max_results]
        output = "\n".join(lines)
        output += f"\n... (truncated to {max_results} results)"
    
    match_count = min(len(lines), max_results)
    header = f"Found {match_count} matches:\n\n"

    return ToolResult(
        tool_call_id=tool_call.id,
        is_error=False,
        content=header + output,
    )
