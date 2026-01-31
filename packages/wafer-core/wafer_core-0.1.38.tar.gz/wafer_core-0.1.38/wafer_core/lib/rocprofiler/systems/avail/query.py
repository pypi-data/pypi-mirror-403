"""Query available metrics and components using rocprof-sys-avail.

Follows Wafer-391: ROCprofiler Tools Architecture.
"""

import subprocess
from dataclasses import dataclass
from typing import Optional

from wafer_core.lib.rocprofiler.systems.finder import find_rocprof_sys_avail


@dataclass(frozen=True)
class AvailResult:
    """Result of querying available metrics/components.

    Attributes:
        success: Whether query completed successfully
        output: Text output from rocprof-sys-avail
        error: Error message if unsuccessful
    """

    success: bool
    output: Optional[str] = None
    error: Optional[str] = None


def query_available_metrics(
    components: bool = False,
    hw_counters: bool = False,
    all_metrics: bool = False,
    filter_pattern: Optional[str] = None,
    category_filter: Optional[list[str]] = None,
) -> AvailResult:
    """Query available metrics and components using rocprof-sys-avail.

    Args:
        components: List available components
        hw_counters: List available hardware counters
        all_metrics: List all available metrics
        filter_pattern: Filter results by regex pattern
        category_filter: Filter by category (list of category names)

    Returns:
        AvailResult with query output

    Example:
        >>> result = query_available_metrics(components=True)
        >>> if result.success:
        ...     print(result.output)
    """
    rocprof_path = find_rocprof_sys_avail()
    if not rocprof_path:
        return AvailResult(
            success=False,
            error="rocprof-sys-avail not found. Install ROCm toolkit with rocprofiler-systems.",
        )

    # Build rocprof-sys-avail command
    rocprof_cmd = [rocprof_path]

    # Query options
    if components:
        rocprof_cmd.append("--components")
    if hw_counters:
        rocprof_cmd.append("--hw-counters")
    if all_metrics:
        rocprof_cmd.append("--all")

    # Filtering
    if filter_pattern:
        rocprof_cmd.extend(["--filter", filter_pattern])

    if category_filter:
        for category in category_filter:
            rocprof_cmd.extend(["--category-filter", category])

    # Execute query
    try:
        result = subprocess.run(
            rocprof_cmd,
            capture_output=True,
            text=True,
            timeout=30,  # 30 seconds should be enough
        )

        return AvailResult(
            success=result.returncode == 0,
            output=result.stdout,
            error=None if result.returncode == 0 else result.stderr,
        )

    except subprocess.TimeoutExpired:
        return AvailResult(
            success=False,
            error="Query timed out after 30 seconds",
        )
    except FileNotFoundError as e:
        return AvailResult(success=False, error=f"Command not found: {e}")
    except Exception as e:
        return AvailResult(success=False, error=str(e))


def query_components(filter_pattern: Optional[str] = None) -> AvailResult:
    """Query available rocprof-sys components.

    This is a convenience wrapper for query_available_metrics(components=True).

    Args:
        filter_pattern: Optional filter pattern

    Returns:
        AvailResult with component list
    """
    return query_available_metrics(components=True, filter_pattern=filter_pattern)


def query_hw_counters(filter_pattern: Optional[str] = None) -> AvailResult:
    """Query available hardware counters.

    This is a convenience wrapper for query_available_metrics(hw_counters=True).

    Args:
        filter_pattern: Optional filter pattern

    Returns:
        AvailResult with hardware counter list
    """
    return query_available_metrics(hw_counters=True, filter_pattern=filter_pattern)
