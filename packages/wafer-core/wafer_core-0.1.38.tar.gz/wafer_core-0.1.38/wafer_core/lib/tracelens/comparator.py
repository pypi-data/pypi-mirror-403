"""Compare TraceLens performance reports.

Wraps TraceLens comparison CLI for side-by-side analysis.
"""

import subprocess
from pathlib import Path
from typing import Optional

from wafer_core.lib.tracelens.types import CompareResult
from wafer_core.lib.tracelens.finder import find_tracelens_command


def compare_reports(
    baseline_path: str,
    candidate_path: str,
    output_path: Optional[str] = None,
    baseline_name: str = "baseline",
    candidate_name: str = "candidate",
    sheets: str = "all",
) -> CompareResult:
    """Compare two performance reports.
    
    Logic:
    1. Validate both input Excel files exist
    2. Find the comparison command
    3. Build command with paths, names, output, sheets
    4. Execute with 2-minute timeout
    5. Return CompareResult with output path
    
    Use cases:
    - Compare before/after optimization runs
    - Regression detection between versions
    - Hardware comparison (same workload, different GPUs)
    
    Args:
        baseline_path: Path to baseline Excel report
        candidate_path: Path to candidate Excel report
        output_path: Path for comparison output (default: comparison.xlsx)
        baseline_name: Display name for baseline
        candidate_name: Display name for candidate
        sheets: Which sheets to compare ("all" or comma-separated list)
        
    Returns:
        CompareResult with comparison summary
    """
    cmd_name = "TraceLens_compare_perf_reports_pytorch"
    cmd_path = find_tracelens_command(cmd_name)
    
    if not cmd_path:
        return CompareResult(
            success=False,
            error=f"TraceLens command not found: {cmd_name}. "
                  f"Install with: pip install git+https://github.com/AMD-AGI/TraceLens.git"
        )
    
    # Validate inputs
    baseline = Path(baseline_path)
    candidate = Path(candidate_path)
    
    if not baseline.exists():
        return CompareResult(
            success=False,
            error=f"Baseline file not found: {baseline_path}"
        )
    
    if not candidate.exists():
        return CompareResult(
            success=False,
            error=f"Candidate file not found: {candidate_path}"
        )
    
    # Build command
    output_file = output_path or "comparison.xlsx"
    
    cmd = [
        cmd_path,
        str(baseline),
        str(candidate),
        "--names", baseline_name, candidate_name,
        "--sheets", sheets,
        "-o", output_file,
    ]
    
    # Execute with 2-minute timeout
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
        )
        
        if result.returncode == 0:
            sheets_list = [sheets] if sheets != "all" else ["all"]
            return CompareResult(
                success=True,
                output_path=output_file,
                sheets_compared=sheets_list,
            )
        else:
            error_msg = result.stderr.strip() if result.stderr else f"Exit code {result.returncode}"
            return CompareResult(
                success=False,
                error=error_msg,
            )
    
    except subprocess.TimeoutExpired:
        return CompareResult(
            success=False,
            error="Timeout: Comparison took too long (>2 minutes)"
        )
    except Exception as e:
        return CompareResult(
            success=False,
            error=str(e)
        )
