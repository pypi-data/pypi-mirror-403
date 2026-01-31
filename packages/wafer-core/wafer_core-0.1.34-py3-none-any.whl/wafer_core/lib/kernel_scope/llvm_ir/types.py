"""Type definitions for LLVM-IR parsing and analysis."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class FunctionInfo:
    """Information about an LLVM function.

    Attributes:
        name: Function name
        line_number: Starting line in source
        return_type: Return type string
        parameter_count: Number of parameters
        basic_block_count: Number of basic blocks
        instruction_count: Total instruction count
        has_loop: Whether function contains loops
        attributes: Function attributes (e.g., "nounwind", "readnone")
    """

    name: str
    line_number: int
    return_type: str = "void"
    parameter_count: int = 0
    basic_block_count: int = 0
    instruction_count: int = 0
    has_loop: bool = False
    attributes: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class LoopInfo:
    """Information about a loop in LLVM-IR.

    Attributes:
        function_name: Containing function
        header_label: Loop header basic block label
        unroll_count: Detected unroll count (if visible)
        vectorization_width: Vector width (if vectorized)
    """

    function_name: str
    header_label: str
    unroll_count: Optional[int] = None
    vectorization_width: Optional[int] = None


@dataclass(frozen=True)
class LLVMIRParseResult:
    """Result of parsing an LLVM-IR file.

    Attributes:
        success: Whether parsing succeeded
        error: Error message if failed
        functions: List of function definitions
        loops: List of detected loops
        target_triple: Target triple string
        data_layout: Data layout string
        raw_text: Original source text
        file_path: Path to source file
    """

    success: bool
    error: Optional[str] = None
    functions: tuple[FunctionInfo, ...] = field(default_factory=tuple)
    loops: tuple[LoopInfo, ...] = field(default_factory=tuple)
    target_triple: Optional[str] = None
    data_layout: Optional[str] = None
    raw_text: str = ""
    file_path: Optional[str] = None
