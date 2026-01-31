"""Metric extraction from trial outputs."""

import json
import re
from typing import Any


def auto_detect_metric(metric_name: str, output: str) -> float | str | None:
    """Auto-detect metric value from common output patterns.

    Args:
        metric_name: Name of the metric to find
        output: stdout/stderr to search

    Returns:
        Extracted metric value (float/string) or None if not found
    """
    # Try multiple common patterns (case-insensitive)
    # Patterns now support both numeric and string values
    # Use word boundaries to avoid matching partial words (e.g., "tflops" shouldn't match inside "TFLOPS")
    patterns = [
        rf"\b{re.escape(metric_name)}\s*:\s*(\S+)",    # "metric: value" (any non-whitespace)
        rf"\b{re.escape(metric_name)}\s*=\s*(\S+)",    # "metric = value"
        rf"\b{re.escape(metric_name)}\s+(\S+)",        # "metric value"
        rf"\b{re.escape(metric_name)}\s*\|\s*(\S+)",   # "metric | value"
    ]

    for pattern in patterns:
        match = re.search(pattern, output, re.IGNORECASE)
        if match:
            value_str = match.group(1)
            # Try to parse as float if it looks numeric
            try:
                return float(value_str)
            except ValueError:
                # Not numeric, return as string
                return value_str

    return None


def extract_metrics_from_output(
    output: str,
    metrics_config: dict[str, str],
) -> dict[str, Any]:
    """Extract metrics from trial output using patterns or auto-detection.

    Args:
        output: stdout from the trial
        metrics_config: Dict of metric_name -> pattern (or "auto")

    Returns:
        Dict of extracted metrics
    """
    metrics: dict[str, Any] = {}

    # First, try to parse entire output as JSON
    try:
        data = json.loads(output.strip())
        if isinstance(data, dict):
            # If it's JSON, extract metrics from it
            for metric_name in metrics_config.keys():
                if metric_name in data:
                    value = data[metric_name]
                    # Try to convert to float if it looks numeric
                    if isinstance(value, (int, float)):
                        metrics[metric_name] = float(value)
                    else:
                        metrics[metric_name] = value

            # If we found all metrics in JSON, return early
            if len(metrics) == len(metrics_config):
                return metrics
    except (json.JSONDecodeError, ValueError):
        pass  # Not JSON, continue with pattern matching

    # Extract each metric using pattern or auto-detection
    for metric_name, pattern in metrics_config.items():
        # Skip if already extracted from JSON
        if metric_name in metrics:
            continue

        if pattern == "auto":
            # Auto-detect the metric
            value = auto_detect_metric(metric_name, output)
            if value is not None:
                metrics[metric_name] = value
        else:
            # Use regex pattern (legacy behavior)
            # Check if it's a simple presence check
            if "(" not in pattern:
                # Simple string presence check
                if pattern in output:
                    metrics[metric_name] = True
            else:
                # Regex with capture group
                match = re.search(pattern, output, re.IGNORECASE)
                if match:
                    try:
                        # Extract first capture group
                        value_str = match.group(1)
                        # Try to parse as float
                        try:
                            metrics[metric_name] = float(value_str)
                        except ValueError:
                            # Not numeric, keep as string
                            metrics[metric_name] = value_str
                    except IndexError:
                        # No capture group, use whole match
                        metrics[metric_name] = match.group(0)

    return metrics
