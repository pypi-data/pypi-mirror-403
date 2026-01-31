"""Same kernel analysis - comparing identical kernel names across platforms.

Identifies kernels where AMD and NVIDIA use the same kernel name/pattern
and compares their performance directly.
"""

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from .aligner import KernelPair, LayerAlignment


@dataclass
class SameKernelComparison:
    """Comparison of identical kernels across platforms."""

    layer: int
    kernel_name: str
    operation: str
    amd_avg_us: float
    nvidia_avg_us: float
    ratio: float
    gap_us: float
    amd_count: int
    nvidia_count: int


@dataclass
class SameKernelAnalysis:
    """Complete same kernel analysis result."""

    kernels: list[SameKernelComparison] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)


def analyze_same_kernels(
    layer_alignments: list[LayerAlignment],
) -> SameKernelAnalysis:
    """Find and compare kernels with identical names across platforms.

    Args:
        layer_alignments: List of aligned layers

    Returns:
        SameKernelAnalysis with comparisons
    """
    same_kernels: list[SameKernelComparison] = []

    for layer_alignment in layer_alignments:
        for pair in layer_alignment.kernel_pairs:
            if pair.is_same_kernel and pair.amd_kernel and pair.nvidia_kernel:
                same_kernels.append(
                    SameKernelComparison(
                        layer=layer_alignment.layer,
                        kernel_name=pair.amd_kernel,
                        operation=pair.operation,
                        amd_avg_us=pair.amd_avg_us,
                        nvidia_avg_us=pair.nvidia_avg_us,
                        ratio=pair.ratio,
                        gap_us=pair.gap_us,
                        amd_count=pair.amd_count,
                        nvidia_count=pair.nvidia_count,
                    )
                )

    if same_kernels:
        ratios = [k.ratio for k in same_kernels if k.ratio != float("inf")]
        avg_ratio = sum(ratios) / len(ratios) if ratios else 1.0
        amd_faster = sum(1 for k in same_kernels if k.ratio < 1.0)
        nvidia_faster = sum(1 for k in same_kernels if k.ratio > 1.0)
    else:
        avg_ratio = 1.0
        amd_faster = 0
        nvidia_faster = 0

    return SameKernelAnalysis(
        kernels=same_kernels,
        summary={
            "total_same_kernels": len(same_kernels),
            "avg_ratio": avg_ratio,
            "kernels_where_amd_faster": amd_faster,
            "kernels_where_nvidia_faster": nvidia_faster,
        },
    )


def analyze_same_kernels_from_alignment(
    layer_alignments: list[LayerAlignment],
) -> dict[str, Any]:
    """Analyze same kernels from alignment data (for API compatibility).

    Args:
        layer_alignments: List of aligned layers

    Returns:
        Dictionary with same kernel analysis results
    """
    analysis = analyze_same_kernels(layer_alignments)

    kernels = [
        {
            "layer": k.layer,
            "kernel_name": k.kernel_name,
            "operation": k.operation,
            "amd_avg_us": k.amd_avg_us,
            "nvidia_avg_us": k.nvidia_avg_us,
            "ratio": k.ratio,
            "gap_us": k.gap_us,
            "amd_count": k.amd_count,
            "nvidia_count": k.nvidia_count,
        }
        for k in analysis.kernels
    ]

    return {
        "kernels": kernels,
        "summary": analysis.summary,
    }
