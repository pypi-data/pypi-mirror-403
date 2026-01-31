"""ISA Analysis Tools - Analyze AMD GPU code objects.

Provides functions for analyzing .co (code object) files to extract
register usage, instruction counts, and other performance-relevant metrics.
"""

from wafer_core.tools.isa_analysis_tools.isa_analysis_tool import (
    analyze_isa,
    format_isa_summary,
)
from wafer_core.tools.isa_analysis_tools.types import ISAAnalysisResult

__all__ = [
    "analyze_isa",
    "format_isa_summary",
    "ISAAnalysisResult",
]
