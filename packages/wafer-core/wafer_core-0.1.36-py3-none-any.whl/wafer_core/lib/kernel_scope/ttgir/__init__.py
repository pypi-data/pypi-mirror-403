"""TTGIR (Triton GPU IR) parsing and analysis.

Parses Triton's GPU-specific intermediate representation to extract
tiling strategy, memory layout decisions, and block dimensions.
"""

from wafer_core.lib.kernel_scope.ttgir.parser import parse_ttgir_file, parse_ttgir_text
from wafer_core.lib.kernel_scope.ttgir.analyzer import analyze_ttgir, TTGIRAnalysis
from wafer_core.lib.kernel_scope.ttgir.types import TTGIRParseResult, TritonOperation

__all__ = [
    "parse_ttgir_file",
    "parse_ttgir_text",
    "analyze_ttgir",
    "TTGIRAnalysis",
    "TTGIRParseResult",
    "TritonOperation",
]
