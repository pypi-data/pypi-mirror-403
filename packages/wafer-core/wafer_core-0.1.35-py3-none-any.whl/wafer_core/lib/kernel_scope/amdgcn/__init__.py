"""AMDGCN ISA parsing and analysis."""

from wafer_core.lib.kernel_scope.amdgcn.parser import parse_isa_file, parse_isa_text
from wafer_core.lib.kernel_scope.amdgcn.analyzer import analyze_isa, ISAAnalysis
from wafer_core.lib.kernel_scope.amdgcn.types import (
    ISAParseResult,
    KernelMetadata,
    InstructionInfo,
    InstructionCategory,
)

__all__ = [
    "parse_isa_file",
    "parse_isa_text",
    "analyze_isa",
    "ISAAnalysis",
    "ISAParseResult",
    "KernelMetadata",
    "InstructionInfo",
    "InstructionCategory",
]
