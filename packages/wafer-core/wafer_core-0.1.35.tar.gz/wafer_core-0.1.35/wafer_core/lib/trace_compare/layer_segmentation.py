"""Layer segmentation based on architecture type.

Segments kernels into transformer layers based on architecture-specific markers
(e.g., attention kernels for transformers, SSM scan kernels for Mamba).
"""

import bisect
from typing import Any

from .architecture import ArchitectureType
from .warnings import TraceWarning


def segment_layers_by_architecture(
    kernels: list[dict[str, Any]],
    architecture: ArchitectureType,
) -> tuple[dict[int, list[dict[str, Any]]], list[TraceWarning]]:
    """Segment kernels into layers based on architecture.
    
    Args:
        kernels: List of kernel events with 'name', 'ts', and other fields
        architecture: Detected architecture type
        
    Returns:
        Tuple of (layer_mapping, warnings)
        layer_mapping: Dict mapping layer_num -> list of kernel events
        warnings: List of warnings if segmentation fails
    """
    warnings: list[TraceWarning] = []
    
    if architecture == ArchitectureType.HYBRID:
        warnings.append(
            TraceWarning(
                code="HYBRID_ARCHITECTURE",
                severity="info",
                message="Hybrid architecture detected (both attention and SSM kernels). Layer segmentation unavailable.",
                suggestion="Hybrid models require custom segmentation logic. Layer analysis will be skipped.",
            )
        )
        return {}, warnings
    
    if architecture == ArchitectureType.UNKNOWN:
        warnings.append(
            TraceWarning(
                code="UNKNOWN_ARCHITECTURE",
                severity="warning",
                message="Cannot determine model architecture. Layer segmentation unavailable.",
                suggestion="Ensure trace contains recognizable kernel patterns (attention, SSM, etc.).",
            )
        )
        return {}, warnings
    
    layer_markers: list[tuple[int, str]] = []
    
    for kernel in kernels:
        name_lower = kernel.get("name", "").lower()
        
        if architecture == ArchitectureType.TRANSFORMER:
            if any(pattern in name_lower for pattern in ["fmha", "attention", "flash"]):
                if "context" in name_lower or "2d" in name_lower or "fmhasm100a" in name_lower:
                    layer_markers.append((kernel.get("ts", 0), kernel.get("name", "")))
        elif architecture == ArchitectureType.SSM:
            if any(pattern in name_lower for pattern in ["selective_scan", "mamba", "ssd"]):
                layer_markers.append((kernel.get("ts", 0), kernel.get("name", "")))
    
    if not layer_markers:
        warnings.append(
            TraceWarning(
                code="NO_LAYER_MARKERS",
                severity="warning",
                message=f"No layer marker kernels found for {architecture.value} architecture.",
                suggestion="Ensure trace contains expected kernel patterns for this architecture type.",
            )
        )
        return {}, warnings
    
    layer_markers.sort(key=lambda x: x[0])
    
    # Sort kernels by timestamp for binary search
    sorted_kernels = sorted(kernels, key=lambda k: k.get("ts", 0))
    kernel_timestamps = [k.get("ts", 0) for k in sorted_kernels]
    
    layer_mapping: dict[int, list[dict[str, Any]]] = {}
    
    for i, (marker_ts, _) in enumerate(layer_markers):
        layer_num = i
        ts_start = marker_ts
        ts_end = layer_markers[i + 1][0] if i + 1 < len(layer_markers) else float("inf")
        
        # Binary search for start and end indices
        start_idx = bisect.bisect_left(kernel_timestamps, ts_start)
        end_idx = bisect.bisect_left(kernel_timestamps, ts_end) if ts_end != float("inf") else len(sorted_kernels)
        
        layer_kernels = sorted_kernels[start_idx:end_idx]
        
        if layer_kernels:
            layer_mapping[layer_num] = layer_kernels
    
    if layer_mapping:
        kernel_counts = [len(kernels) for kernels in layer_mapping.values()]
        if kernel_counts:
            mean_count = sum(kernel_counts) / len(kernel_counts)
            variances = [abs(count - mean_count) / mean_count for count in kernel_counts]
            if any(v > 0.3 for v in variances):
                warnings.append(
                    TraceWarning(
                        code="LAYER_SIZE_VARIANCE",
                        severity="info",
                        message="Layer kernel counts vary significantly. Segmentation may be inaccurate.",
                        suggestion="This is normal for models with varying layer sizes or non-uniform workloads.",
                    )
                )
    
    return layer_mapping, warnings
