"""Trace comparison library for analyzing GPU traces across platforms.

This module provides functionality to compare performance traces from AMD and NVIDIA GPUs,
identifying kernel-level performance differences and fusion opportunities.
"""

from .analyzer import analyze_traces
from .classifier import Op, classify
from .formatter import (
    format_csv,
    format_fusion_csv,
    format_fusion_json,
    format_fusion_text,
    format_json,
    format_text,
)
from .fusion_analyzer import analyze_fusion_differences
from .loader import load_trace

__all__ = [
    "Op",
    "classify",
    "load_trace",
    "analyze_traces",
    "analyze_fusion_differences",
    "format_text",
    "format_csv",
    "format_json",
    "format_fusion_text",
    "format_fusion_csv",
    "format_fusion_json",
]
