"""Cross-artifact correlation for multi-level analysis.

Correlates TTGIR, LLVM-IR, and ISA artifacts to help trace
performance issues from high-level constructs to low-level ISA.
"""

from wafer_core.lib.kernel_scope.correlation.mapper import (
    correlate_artifacts,
    CorrelatedAnalysis,
)

__all__ = [
    "correlate_artifacts",
    "CorrelatedAnalysis",
]
