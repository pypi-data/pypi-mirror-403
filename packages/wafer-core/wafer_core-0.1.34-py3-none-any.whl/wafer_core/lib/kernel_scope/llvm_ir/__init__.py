"""LLVM-IR parsing and analysis.

Parses LLVM Intermediate Representation files to extract
optimization insights like loop unrolling and vectorization.
"""

from wafer_core.lib.kernel_scope.llvm_ir.parser import parse_llvm_ir_file, parse_llvm_ir_text
from wafer_core.lib.kernel_scope.llvm_ir.analyzer import analyze_llvm_ir, LLVMIRAnalysis
from wafer_core.lib.kernel_scope.llvm_ir.types import LLVMIRParseResult, FunctionInfo

__all__ = [
    "parse_llvm_ir_file",
    "parse_llvm_ir_text",
    "analyze_llvm_ir",
    "LLVMIRAnalysis",
    "LLVMIRParseResult",
    "FunctionInfo",
]
