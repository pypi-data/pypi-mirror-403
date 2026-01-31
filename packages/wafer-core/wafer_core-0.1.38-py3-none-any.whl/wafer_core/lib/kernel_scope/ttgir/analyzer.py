"""TTGIR Analyzer.

Analyzes parsed TTGIR to extract tiling and optimization insights.

Design: Wafer-436 - AMD Kernel Scope (Phase 2)
"""

from dataclasses import dataclass, field
from typing import Optional

from wafer_core.lib.kernel_scope.ttgir.types import (
    TTGIRParseResult,
    TritonOperation,
    TritonOpType,
    TileInfo,
)


@dataclass(frozen=True)
class TTGIRAnalysis:
    """Analysis results for TTGIR.

    Attributes:
        dot_count: Number of tt.dot (matmul) operations
        load_count: Number of tt.load operations
        store_count: Number of tt.store operations
        reduce_count: Number of tt.reduce operations
        barrier_count: Number of barriers
        tile_info: Detected tiling parameters
        has_software_pipelining: Whether multi-stage pipelining detected
        estimated_compute_intensity: Compute to memory ratio estimate
    """

    dot_count: int = 0
    load_count: int = 0
    store_count: int = 0
    reduce_count: int = 0
    barrier_count: int = 0
    tile_info: Optional[TileInfo] = None
    has_software_pipelining: bool = False
    estimated_compute_intensity: Optional[float] = None


def analyze_ttgir(parse_result: TTGIRParseResult) -> TTGIRAnalysis:
    """Analyze parsed TTGIR.

    Args:
        parse_result: Result from parse_ttgir_file or parse_ttgir_text

    Returns:
        TTGIRAnalysis with tiling and optimization insights

    Raises:
        ValueError: If parse_result is not successful
    """
    if not parse_result.success:
        raise ValueError(f"Cannot analyze failed parse result: {parse_result.error}")

    operations = parse_result.operations

    # Count operations by type
    dot_count = sum(1 for op in operations if op.op_type == TritonOpType.DOT)
    load_count = sum(1 for op in operations if op.op_type == TritonOpType.LOAD)
    store_count = sum(1 for op in operations if op.op_type == TritonOpType.STORE)
    reduce_count = sum(1 for op in operations if op.op_type == TritonOpType.REDUCE)
    barrier_count = sum(1 for op in operations if op.op_type == TritonOpType.BARRIER)

    # Check for software pipelining
    tile_info = parse_result.tile_info
    has_pipelining = tile_info is not None and tile_info.num_stages is not None and tile_info.num_stages > 1

    # Estimate compute intensity (FLOPs per byte)
    compute_intensity = _estimate_compute_intensity(
        dot_count=dot_count,
        load_count=load_count,
        store_count=store_count,
        tile_info=tile_info,
    )

    return TTGIRAnalysis(
        dot_count=dot_count,
        load_count=load_count,
        store_count=store_count,
        reduce_count=reduce_count,
        barrier_count=barrier_count,
        tile_info=tile_info,
        has_software_pipelining=has_pipelining,
        estimated_compute_intensity=compute_intensity,
    )


def _estimate_compute_intensity(
    dot_count: int,
    load_count: int,
    store_count: int,
    tile_info: Optional[TileInfo],
) -> Optional[float]:
    """Estimate arithmetic intensity (FLOPs per byte).

    For GEMM with tile sizes M, N, K:
    - FLOPs = 2 * M * N * K (multiply-add)
    - Bytes = (M*K + K*N + M*N) * sizeof(dtype)

    Higher is better - indicates more compute per memory access.
    """
    if dot_count == 0:
        return None

    if tile_info is None:
        return None

    m = tile_info.block_m
    n = tile_info.block_n
    k = tile_info.block_k

    if not all([m, n, k]):
        return None

    # Assume float32 (4 bytes)
    dtype_size = 4

    # FLOPs for one dot
    flops = 2 * m * n * k

    # Bytes loaded/stored (simplified: A, B tiles loaded, C tile stored)
    # Real implementation would need to account for data reuse
    bytes_accessed = (m * k + k * n + m * n) * dtype_size

    if bytes_accessed == 0:
        return None

    return flops / bytes_accessed
