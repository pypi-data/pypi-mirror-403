"""Type definitions for TTGIR parsing and analysis."""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional


class TritonOpType(Enum):
    """Types of Triton operations."""

    DOT = auto()  # tt.dot - matrix multiply
    LOAD = auto()  # tt.load - memory load
    STORE = auto()  # tt.store - memory store
    REDUCE = auto()  # tt.reduce - reduction operation
    BROADCAST = auto()  # tt.broadcast
    SPLAT = auto()  # tt.splat
    EXPAND_DIMS = auto()  # tt.expand_dims
    MAKE_RANGE = auto()  # tt.make_range
    TRANS = auto()  # tt.trans - transpose
    RESHAPE = auto()  # tt.reshape
    ATOMIC = auto()  # tt.atomic_*
    BARRIER = auto()  # gpu.barrier
    OTHER = auto()


@dataclass(frozen=True)
class TritonOperation:
    """Information about a Triton operation.

    Attributes:
        line_number: Line number in source
        op_type: Operation type
        raw_text: Raw operation text
        result_type: Result tensor type (shape and dtype)
        operand_types: Operand tensor types
    """

    line_number: int
    op_type: TritonOpType
    raw_text: str
    result_type: Optional[str] = None
    operand_types: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class TileInfo:
    """Information about a tiling strategy.

    Attributes:
        block_m: Block size in M dimension
        block_n: Block size in N dimension
        block_k: Block size in K dimension
        num_warps: Number of warps
        num_stages: Number of pipeline stages
    """

    block_m: Optional[int] = None
    block_n: Optional[int] = None
    block_k: Optional[int] = None
    num_warps: Optional[int] = None
    num_stages: Optional[int] = None


@dataclass(frozen=True)
class TTGIRParseResult:
    """Result of parsing a TTGIR file.

    Attributes:
        success: Whether parsing succeeded
        error: Error message if failed
        operations: List of Triton operations
        tile_info: Detected tiling information
        raw_text: Original source text
        file_path: Path to source file
    """

    success: bool
    error: Optional[str] = None
    operations: tuple[TritonOperation, ...] = field(default_factory=tuple)
    tile_info: Optional[TileInfo] = None
    raw_text: str = ""
    file_path: Optional[str] = None
