"""TraceLens - Automated trace analysis tool integration.

This module provides core functionality for TraceLens trace analysis.
TraceLens is an AMD tool for analyzing GPU trace files.

Public API:
    - check_installation: Check if TraceLens is installed
    - generate_perf_report: Generate performance report from trace
    - generate_collective_report: Generate multi-rank collective report
    - compare_reports: Compare two performance reports
    - CheckResult: Installation check result
    - ReportResult: Report generation result
    - CompareResult: Comparison result
    - CollectiveReportResult: Collective report result
    - TraceFormat: Supported trace formats

Example:
    >>> from wafer_core.lib.tracelens import check_installation, generate_perf_report
    >>>
    >>> # Check if TraceLens is installed
    >>> result = check_installation()
    >>> if result.installed:
    ...     print(f"TraceLens version: {result.version}")
    >>>
    >>> # Generate performance report
    >>> report = generate_perf_report(
    ...     trace_path="./trace.json",
    ...     trace_format=TraceFormat.PYTORCH,
    ... )
    >>> if report.success:
    ...     print(f"Report generated: {report.output_path}")
"""

from wafer_core.lib.tracelens.types import (
    CheckResult,
    CollectiveReportResult,
    CompareResult,
    ReportResult,
    TraceFormat,
)
from wafer_core.lib.tracelens.finder import (
    check_installation,
    find_tracelens_command,
)
from wafer_core.lib.tracelens.report_generator import (
    generate_perf_report,
    generate_collective_report,
)
from wafer_core.lib.tracelens.comparator import (
    compare_reports,
)

__all__ = [
    # Installation checking
    "check_installation",
    "find_tracelens_command",
    # Report generation
    "generate_perf_report",
    "generate_collective_report",
    # Comparison
    "compare_reports",
    # Types
    "CheckResult",
    "ReportResult",
    "CompareResult",
    "CollectiveReportResult",
    "TraceFormat",
]
