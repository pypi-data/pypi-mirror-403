"""Analyzer for kernel trace output.

Parses profiler output to extract kernel information and identify the primary kernel.
"""

import json
import re
from dataclasses import dataclass
from typing import Any

from wafer_core.tools.dispatch_baseline.dtypes import KernelInfo, KernelTraceResult, OpSpec


@dataclass(frozen=True)
class ParsedTraceResult:
    """Parsed trace output with environment info for caching."""

    result: KernelTraceResult
    pytorch_version: str
    runtime_version: str
    gpu_arch: str


def parse_trace_output(output: str, op_spec: OpSpec, hardware: str) -> ParsedTraceResult:
    """Parse kernel trace script output and extract kernel information.

    Args:
        output: Raw output from the trace script (stdout)
        op_spec: The operation that was traced
        hardware: Target hardware name

    Returns:
        ParsedTraceResult with extracted kernel information and environment info
    """
    # Look for our JSON marker in the output
    json_match = re.search(r"KERNEL_TRACE_RESULT_JSON:(.+)$", output, re.MULTILINE)

    if not json_match:
        return ParsedTraceResult(
            result=KernelTraceResult(
                op_spec=op_spec,
                hardware=hardware,
                kernels=[],
                primary_kernel=None,
                raw_output=output,
                error="Could not find KERNEL_TRACE_RESULT_JSON marker in output",
            ),
            pytorch_version="unknown",
            runtime_version="unknown",
            gpu_arch="unknown",
        )

    try:
        result_json = json.loads(json_match.group(1))
    except json.JSONDecodeError as e:
        return ParsedTraceResult(
            result=KernelTraceResult(
                op_spec=op_spec,
                hardware=hardware,
                kernels=[],
                primary_kernel=None,
                raw_output=output,
                error=f"Failed to parse JSON: {e}",
            ),
            pytorch_version="unknown",
            runtime_version="unknown",
            gpu_arch="unknown",
        )

    # Extract environment info
    env_info = result_json.get("environment", {})
    pytorch_version = env_info.get("pytorch_version", "unknown")
    runtime_version = env_info.get("runtime_version", "unknown")
    gpu_arch = env_info.get("gpu_arch", "unknown")

    # Extract kernels from JSON
    kernels = []
    for k in result_json.get("kernels", []):
        kernel_info = _parse_kernel_dict(k)
        if kernel_info:
            kernels.append(kernel_info)

    # Identify primary kernel (longest duration)
    primary_kernel = kernels[0] if kernels else None

    return ParsedTraceResult(
        result=KernelTraceResult(
            op_spec=op_spec,
            hardware=hardware,
            kernels=kernels,
            primary_kernel=primary_kernel,
            raw_output=output,
        ),
        pytorch_version=pytorch_version,
        runtime_version=runtime_version,
        gpu_arch=gpu_arch,
    )


def _parse_kernel_dict(kernel_dict: dict[str, Any]) -> KernelInfo | None:
    """Parse a kernel dictionary into KernelInfo."""
    name = kernel_dict.get("name", "")
    if not name:
        return None

    return KernelInfo(
        name=name,
        duration_us=kernel_dict.get("duration_us", 0.0),
    )


def extract_kernels_from_nsys(nsys_output: str) -> list[dict[str, Any]]:
    """Extract kernel information from nsys output.

    This is a fallback for when torch.profiler doesn't capture all kernels.

    Args:
        nsys_output: Output from `nsys stats` or similar

    Returns:
        List of kernel dictionaries
    """
    kernels = []

    # Look for GPU kernel summary lines
    # Format varies, but typically: name, duration, count, etc.
    lines = nsys_output.split("\n")

    for line in lines:
        # Skip headers and empty lines
        if not line.strip() or "---" in line or "Name" in line:
            continue

        # Try to parse as nsys kernel line
        # This is a simplified parser - real nsys output varies
        parts = line.split()
        if len(parts) >= 2:
            # Heuristic: last column is often the kernel name
            name = parts[-1]
            if any(c.isalpha() for c in name) and "_" in name:
                kernels.append({"name": name, "duration_us": 0.0})

    return kernels


def merge_kernel_infos(
    profiler_kernels: list[KernelInfo], nsys_kernels: list[dict[str, Any]]
) -> list[KernelInfo]:
    """Merge kernel info from multiple sources.

    Prefers profiler data when available, but adds any missing kernels from nsys.

    Args:
        profiler_kernels: Kernels from torch.profiler
        nsys_kernels: Kernels from nsys

    Returns:
        Merged list of KernelInfo objects
    """
    seen_names = {k.name for k in profiler_kernels}
    result = list(profiler_kernels)

    for nsys_kernel in nsys_kernels:
        name = nsys_kernel.get("name", "")
        if name and name not in seen_names:
            result.append(
                KernelInfo(
                    name=name,
                    duration_us=nsys_kernel.get("duration_us", 0.0),
                )
            )
            seen_names.add(name)

    return result
