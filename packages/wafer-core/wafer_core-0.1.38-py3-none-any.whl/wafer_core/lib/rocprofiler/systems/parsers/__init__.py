"""Parsers for rocprof-sys output formats.

Provides parsing utilities for:
- JSON outputs (wall_clock, metadata, functions)
- Text outputs (wall-clock.txt)
- Perfetto traces (reuse existing infrastructure)
- rocpd databases (reuse from sdk)
"""

from wafer_core.lib.rocprofiler.systems.parsers.json_parser import (
    parse_functions_json,
    parse_metadata_json,
    parse_wall_clock_json,
)
from wafer_core.lib.rocprofiler.systems.parsers.text_parser import parse_text_summary

__all__ = [
    "parse_wall_clock_json",
    "parse_metadata_json",
    "parse_functions_json",
    "parse_text_summary",
]
