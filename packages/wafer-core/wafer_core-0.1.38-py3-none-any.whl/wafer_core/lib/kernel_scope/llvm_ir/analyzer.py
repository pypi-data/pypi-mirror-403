"""LLVM-IR Analyzer.

Analyzes parsed LLVM-IR to extract optimization insights.

Design: Wafer-436 - AMD Kernel Scope (Phase 2)
"""

from dataclasses import dataclass, field
from typing import Optional

from wafer_core.lib.kernel_scope.llvm_ir.types import LLVMIRParseResult, FunctionInfo


@dataclass(frozen=True)
class LLVMIRAnalysis:
    """Analysis results for LLVM-IR.

    Attributes:
        function_count: Number of functions defined
        total_instructions: Total instruction count across all functions
        functions_with_loops: Number of functions containing loops
        estimated_unroll_factor: Estimated loop unroll factor
        target_triple: Target triple string
        has_vector_ops: Whether vectorized operations detected
        kernel_functions: Functions that appear to be GPU kernels
    """

    function_count: int = 0
    total_instructions: int = 0
    functions_with_loops: int = 0
    estimated_unroll_factor: Optional[int] = None
    target_triple: Optional[str] = None
    has_vector_ops: bool = False
    kernel_functions: tuple[str, ...] = field(default_factory=tuple)


def analyze_llvm_ir(parse_result: LLVMIRParseResult) -> LLVMIRAnalysis:
    """Analyze parsed LLVM-IR.

    Args:
        parse_result: Result from parse_llvm_ir_file or parse_llvm_ir_text

    Returns:
        LLVMIRAnalysis with optimization insights

    Raises:
        ValueError: If parse_result is not successful
    """
    if not parse_result.success:
        raise ValueError(f"Cannot analyze failed parse result: {parse_result.error}")

    functions = parse_result.functions
    function_count = len(functions)
    total_instructions = sum(f.instruction_count for f in functions)
    functions_with_loops = sum(1 for f in functions if f.has_loop)

    # Detect kernel functions (common naming patterns)
    kernel_functions = [
        f.name for f in functions
        if _is_likely_kernel(f)
    ]

    # Check for vector operations in raw text
    has_vector_ops = _detect_vector_ops(parse_result.raw_text)

    return LLVMIRAnalysis(
        function_count=function_count,
        total_instructions=total_instructions,
        functions_with_loops=functions_with_loops,
        target_triple=parse_result.target_triple,
        has_vector_ops=has_vector_ops,
        kernel_functions=tuple(kernel_functions),
    )


def _is_likely_kernel(func: FunctionInfo) -> bool:
    """Check if function appears to be a GPU kernel."""
    name_lower = func.name.lower()

    # Common kernel naming patterns
    kernel_indicators = [
        "kernel",
        "_kernel",
        "__device__",
        "__global__",
        "triton_",
        "_hip_",
    ]

    return any(ind in name_lower for ind in kernel_indicators)


def _detect_vector_ops(text: str) -> bool:
    """Detect presence of vector operations in LLVM-IR."""
    # Look for vector types like <4 x float>, <8 x i32>, etc.
    import re
    vector_pattern = re.compile(r"<\d+\s+x\s+\w+>")
    return bool(vector_pattern.search(text))
