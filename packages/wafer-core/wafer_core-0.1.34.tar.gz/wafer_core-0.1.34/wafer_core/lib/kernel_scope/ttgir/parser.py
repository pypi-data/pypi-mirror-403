"""TTGIR (Triton GPU IR) and MLIR Parser.

Parses GPU intermediate representation files including:
- Triton IR (.ttir) - High-level Triton operations
- Triton GPU IR (.ttgir) - Lowered Triton with GPU-specific constructs
- Generic MLIR (.mlir) - MLIR with GPU, Linalg, SCF, and other dialects

Design: Wafer-436 - AMD Kernel Scope (Phase 2)
"""

import re
from pathlib import Path
from typing import Optional

from wafer_core.lib.kernel_scope.ttgir.types import (
    TTGIRParseResult,
    TritonOperation,
    TritonOpType,
    TileInfo,
)


# Operation patterns - Triton dialect
_TRITON_OP_PATTERNS: list[tuple[re.Pattern, TritonOpType]] = [
    (re.compile(r"tt\.dot\b"), TritonOpType.DOT),
    (re.compile(r"tt\.load\b"), TritonOpType.LOAD),
    (re.compile(r"tt\.store\b"), TritonOpType.STORE),
    (re.compile(r"tt\.reduce\b"), TritonOpType.REDUCE),
    (re.compile(r"tt\.broadcast\b"), TritonOpType.BROADCAST),
    (re.compile(r"tt\.splat\b"), TritonOpType.SPLAT),
    (re.compile(r"tt\.expand_dims\b"), TritonOpType.EXPAND_DIMS),
    (re.compile(r"tt\.make_range\b"), TritonOpType.MAKE_RANGE),
    (re.compile(r"tt\.trans\b"), TritonOpType.TRANS),
    (re.compile(r"tt\.reshape\b"), TritonOpType.RESHAPE),
    (re.compile(r"tt\.atomic"), TritonOpType.ATOMIC),
]

# MLIR GPU dialect patterns
_GPU_OP_PATTERNS: list[tuple[re.Pattern, TritonOpType]] = [
    (re.compile(r"gpu\.barrier\b"), TritonOpType.BARRIER),
    (re.compile(r"gpu\.thread_id\b"), TritonOpType.OTHER),
    (re.compile(r"gpu\.block_id\b"), TritonOpType.OTHER),
    (re.compile(r"gpu\.block_dim\b"), TritonOpType.OTHER),
    (re.compile(r"gpu\.grid_dim\b"), TritonOpType.OTHER),
    (re.compile(r"gpu\.launch_func\b"), TritonOpType.OTHER),
    (re.compile(r"gpu\.launch\b"), TritonOpType.OTHER),
    (re.compile(r"gpu\.func\b"), TritonOpType.OTHER),
    (re.compile(r"gpu\.module\b"), TritonOpType.OTHER),
    (re.compile(r"gpu\.alloc\b"), TritonOpType.OTHER),
    (re.compile(r"gpu\.dealloc\b"), TritonOpType.OTHER),
    (re.compile(r"gpu\.memcpy\b"), TritonOpType.OTHER),
    (re.compile(r"gpu\.wait\b"), TritonOpType.BARRIER),
]

# MLIR memref dialect patterns (for memory operations)
_MEMREF_OP_PATTERNS: list[tuple[re.Pattern, TritonOpType]] = [
    (re.compile(r"memref\.load\b"), TritonOpType.LOAD),
    (re.compile(r"memref\.store\b"), TritonOpType.STORE),
    (re.compile(r"memref\.alloc\b"), TritonOpType.OTHER),
    (re.compile(r"memref\.alloca\b"), TritonOpType.OTHER),
    (re.compile(r"memref\.dealloc\b"), TritonOpType.OTHER),
    (re.compile(r"memref\.copy\b"), TritonOpType.OTHER),
    (re.compile(r"memref\.atomic_rmw\b"), TritonOpType.ATOMIC),
]

# MLIR linalg dialect patterns
_LINALG_OP_PATTERNS: list[tuple[re.Pattern, TritonOpType]] = [
    (re.compile(r"linalg\.matmul\b"), TritonOpType.DOT),
    (re.compile(r"linalg\.batch_matmul\b"), TritonOpType.DOT),
    (re.compile(r"linalg\.matvec\b"), TritonOpType.DOT),
    (re.compile(r"linalg\.dot\b"), TritonOpType.DOT),
    (re.compile(r"linalg\.generic\b"), TritonOpType.OTHER),
    (re.compile(r"linalg\.fill\b"), TritonOpType.OTHER),
    (re.compile(r"linalg\.copy\b"), TritonOpType.OTHER),
]

# MLIR vector dialect patterns
_VECTOR_OP_PATTERNS: list[tuple[re.Pattern, TritonOpType]] = [
    (re.compile(r"vector\.load\b"), TritonOpType.LOAD),
    (re.compile(r"vector\.store\b"), TritonOpType.STORE),
    (re.compile(r"vector\.transfer_read\b"), TritonOpType.LOAD),
    (re.compile(r"vector\.transfer_write\b"), TritonOpType.STORE),
    (re.compile(r"vector\.broadcast\b"), TritonOpType.BROADCAST),
    (re.compile(r"vector\.reduction\b"), TritonOpType.REDUCE),
    (re.compile(r"vector\.contract\b"), TritonOpType.DOT),
    (re.compile(r"vector\.fma\b"), TritonOpType.OTHER),
]

# Combine all operation patterns
_OP_PATTERNS: list[tuple[re.Pattern, TritonOpType]] = (
    _TRITON_OP_PATTERNS + 
    _GPU_OP_PATTERNS + 
    _MEMREF_OP_PATTERNS + 
    _LINALG_OP_PATTERNS +
    _VECTOR_OP_PATTERNS
)

# Tiling attribute patterns
_BLOCK_M_PATTERN = re.compile(r"BLOCK_M\s*=\s*(\d+)")
_BLOCK_N_PATTERN = re.compile(r"BLOCK_N\s*=\s*(\d+)")
_BLOCK_K_PATTERN = re.compile(r"BLOCK_K\s*=\s*(\d+)")
_NUM_WARPS_PATTERN = re.compile(r"num_warps\s*=\s*(\d+)")
_NUM_STAGES_PATTERN = re.compile(r"num_stages\s*=\s*(\d+)")

# Tensor type pattern (e.g., tensor<128x64xf32>)
_TENSOR_TYPE_PATTERN = re.compile(r"tensor<([^>]+)>")


def parse_ttgir_file(file_path: str | Path) -> TTGIRParseResult:
    """Parse a TTGIR file.

    Args:
        file_path: Path to the .ttgir, .ttir, or .mlir file

    Returns:
        TTGIRParseResult with parsed operation and tiling information
    """
    path = Path(file_path)

    if not path.exists():
        return TTGIRParseResult(
            success=False,
            error=f"File not found: {file_path}",
            file_path=str(file_path),
        )

    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return TTGIRParseResult(
            success=False,
            error=f"Failed to read file: {e}",
            file_path=str(file_path),
        )

    result = parse_ttgir_text(text)

    return TTGIRParseResult(
        success=result.success,
        error=result.error,
        operations=result.operations,
        tile_info=result.tile_info,
        raw_text=result.raw_text,
        file_path=str(file_path),
    )


def parse_ttgir_text(text: str) -> TTGIRParseResult:
    """Parse TTGIR from text.

    Args:
        text: TTGIR/MLIR source text

    Returns:
        TTGIRParseResult with parsed information
    """
    if not text.strip():
        return TTGIRParseResult(
            success=False,
            error="Empty input text",
            raw_text=text,
        )

    # Check if this looks like TTGIR/Triton IR
    if not _is_ttgir(text):
        return TTGIRParseResult(
            success=False,
            error="File does not appear to be TTGIR/Triton IR",
            raw_text=text,
        )

    # Parse operations
    operations = _parse_operations(text)

    # Extract tiling info
    tile_info = _extract_tile_info(text)

    return TTGIRParseResult(
        success=True,
        operations=tuple(operations),
        tile_info=tile_info,
        raw_text=text,
    )


def _is_ttgir(text: str) -> bool:
    """Check if text appears to be TTGIR/Triton IR or generic MLIR.
    
    Supports:
    - Triton dialect (tt.func, tt.dot, tt.load, etc.)
    - MLIR GPU dialect (gpu.func, gpu.launch, gpu.barrier, etc.)
    - MLIR Linalg dialect (linalg.matmul, linalg.generic, etc.)
    - MLIR memref dialect (memref.load, memref.store, etc.)
    - MLIR vector dialect (vector.load, vector.contract, etc.)
    - MLIR SCF dialect (scf.for, scf.if, etc.)
    """
    # Triton-specific indicators
    triton_indicators = [
        "tt.func",
        "tt.dot",
        "tt.load",
        "tt.store",
        "tt.reduce",
        "tt.splat",
        "tt.make_range",
        "tt.get_program_id",
        "tt.addptr",
        "triton_gpu",
        "#triton_gpu",
        "ttgir",
        "ttir",
    ]
    
    # MLIR GPU dialect indicators
    gpu_indicators = [
        "gpu.func",
        "gpu.module",
        "gpu.launch",
        "gpu.launch_func",
        "gpu.barrier",
        "gpu.thread_id",
        "gpu.block_id",
        "gpu.block_dim",
        "gpu.alloc",
        "gpu.wait",
    ]
    
    # MLIR general indicators
    mlir_indicators = [
        "memref.load",
        "memref.store",
        "memref.alloc",
        "linalg.matmul",
        "linalg.generic",
        "linalg.fill",
        "vector.load",
        "vector.store",
        "vector.contract",
        "vector.transfer_read",
        "vector.transfer_write",
        "scf.for",
        "scf.if",
        "scf.while",
        "scf.yield",
        "arith.addf",
        "arith.mulf",
        "arith.addi",
        "arith.muli",
        "func.func",
        "func.return",
        "module {",  # MLIR module start
    ]
    
    # Also detect by MLIR type syntax
    mlir_type_indicators = [
        "tensor<",
        "memref<",
        "vector<",
        "!tt.ptr",
        "!gpu.async.token",
        "#gpu.address_space",
    ]

    text_lower = text.lower()
    
    # Check all indicators
    all_indicators = triton_indicators + gpu_indicators + mlir_indicators + mlir_type_indicators
    return any(ind.lower() in text_lower for ind in all_indicators)


def _parse_operations(text: str) -> list[TritonOperation]:
    """Parse all Triton operations from text."""
    operations = []
    lines = text.splitlines()

    for line_num, line in enumerate(lines, start=1):
        line_stripped = line.strip()

        # Skip comments and empty lines
        if not line_stripped or line_stripped.startswith("//"):
            continue

        # Check each operation pattern
        for pattern, op_type in _OP_PATTERNS:
            if pattern.search(line_stripped):
                # Extract result type
                result_type = _extract_result_type(line_stripped)

                operations.append(TritonOperation(
                    line_number=line_num,
                    op_type=op_type,
                    raw_text=line_stripped,
                    result_type=result_type,
                ))
                break

    return operations


def _extract_result_type(line: str) -> Optional[str]:
    """Extract result tensor type from operation line."""
    # Look for -> type pattern
    if "->" in line:
        after_arrow = line.split("->", 1)[1].strip()
        tensor_match = _TENSOR_TYPE_PATTERN.search(after_arrow)
        if tensor_match:
            return f"tensor<{tensor_match.group(1)}>"

    # Look for : type pattern at end
    if ":" in line:
        # Get last : followed by type
        parts = line.rsplit(":", 1)
        if len(parts) == 2:
            type_part = parts[1].strip()
            tensor_match = _TENSOR_TYPE_PATTERN.search(type_part)
            if tensor_match:
                return f"tensor<{tensor_match.group(1)}>"

    return None


def _extract_tile_info(text: str) -> Optional[TileInfo]:
    """Extract tiling information from TTGIR."""
    block_m = None
    block_n = None
    block_k = None
    num_warps = None
    num_stages = None

    # Search for tiling parameters
    m_match = _BLOCK_M_PATTERN.search(text)
    if m_match:
        block_m = int(m_match.group(1))

    n_match = _BLOCK_N_PATTERN.search(text)
    if n_match:
        block_n = int(n_match.group(1))

    k_match = _BLOCK_K_PATTERN.search(text)
    if k_match:
        block_k = int(k_match.group(1))

    warps_match = _NUM_WARPS_PATTERN.search(text)
    if warps_match:
        num_warps = int(warps_match.group(1))

    stages_match = _NUM_STAGES_PATTERN.search(text)
    if stages_match:
        num_stages = int(stages_match.group(1))

    # Only return TileInfo if we found something
    if any([block_m, block_n, block_k, num_warps, num_stages]):
        return TileInfo(
            block_m=block_m,
            block_n=block_n,
            block_k=block_k,
            num_warps=num_warps,
            num_stages=num_stages,
        )

    return None
