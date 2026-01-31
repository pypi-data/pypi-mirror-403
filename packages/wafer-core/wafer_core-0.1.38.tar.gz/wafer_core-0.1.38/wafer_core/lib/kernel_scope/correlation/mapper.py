"""Cross-artifact correlation engine.

Maps constructs across TTGIR, LLVM-IR, and AMDGCN ISA to help
trace performance bottlenecks from high-level to low-level.

Design: Wafer-436 - AMD Kernel Scope (Phase 2)
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from wafer_core.lib.kernel_scope.amdgcn import parse_isa_file, analyze_isa, ISAAnalysis
from wafer_core.lib.kernel_scope.llvm_ir import parse_llvm_ir_file, analyze_llvm_ir, LLVMIRAnalysis
from wafer_core.lib.kernel_scope.ttgir import parse_ttgir_file, analyze_ttgir, TTGIRAnalysis


@dataclass(frozen=True)
class CorrelationPoint:
    """A point of correlation between artifacts.

    Attributes:
        ttgir_line: Line number in TTGIR (if applicable)
        ttgir_op: TTGIR operation description
        llvm_ir_line: Line number in LLVM-IR (if applicable)
        llvm_ir_func: LLVM-IR function name
        isa_line: Line number in ISA (if applicable)
        isa_instruction: ISA instruction mnemonic
        description: Human-readable description
    """

    ttgir_line: Optional[int] = None
    ttgir_op: Optional[str] = None
    llvm_ir_line: Optional[int] = None
    llvm_ir_func: Optional[str] = None
    isa_line: Optional[int] = None
    isa_instruction: Optional[str] = None
    description: str = ""


@dataclass(frozen=True)
class CorrelatedAnalysis:
    """Combined analysis from multiple artifacts.

    Attributes:
        isa_analysis: ISA-level analysis (if ISA provided)
        llvm_ir_analysis: LLVM-IR analysis (if provided)
        ttgir_analysis: TTGIR analysis (if provided)
        correlation_points: Identified correlation points
        summary: High-level summary of findings
        recommendations: Optimization recommendations
    """

    isa_analysis: Optional[ISAAnalysis] = None
    llvm_ir_analysis: Optional[LLVMIRAnalysis] = None
    ttgir_analysis: Optional[TTGIRAnalysis] = None
    correlation_points: tuple[CorrelationPoint, ...] = field(default_factory=tuple)
    summary: str = ""
    recommendations: tuple[str, ...] = field(default_factory=tuple)


def correlate_artifacts(
    isa_path: Optional[str | Path] = None,
    llvm_ir_path: Optional[str | Path] = None,
    ttgir_path: Optional[str | Path] = None,
) -> CorrelatedAnalysis:
    """Analyze and correlate multiple compilation artifacts.

    Accepts any combination of ISA, LLVM-IR, and TTGIR files and
    produces a combined analysis with cross-artifact correlations.

    Args:
        isa_path: Path to AMDGCN ISA file (.s, .gcn, .asm)
        llvm_ir_path: Path to LLVM-IR file (.ll)
        ttgir_path: Path to TTGIR file (.ttgir, .ttir, .mlir)

    Returns:
        CorrelatedAnalysis with combined results and correlations

    Example:
        >>> result = correlate_artifacts(
        ...     isa_path="kernel.s",
        ...     ttgir_path="kernel.ttgir"
        ... )
        >>> for rec in result.recommendations:
        ...     print(rec)
    """
    isa_analysis = None
    llvm_ir_analysis = None
    ttgir_analysis = None

    # Parse and analyze ISA
    if isa_path:
        parse_result = parse_isa_file(isa_path)
        if parse_result.success and parse_result.kernels:
            isa_analysis = analyze_isa(parse_result)

    # Parse and analyze LLVM-IR
    if llvm_ir_path:
        parse_result = parse_llvm_ir_file(llvm_ir_path)
        if parse_result.success:
            llvm_ir_analysis = analyze_llvm_ir(parse_result)

    # Parse and analyze TTGIR
    if ttgir_path:
        parse_result = parse_ttgir_file(ttgir_path)
        if parse_result.success:
            ttgir_analysis = analyze_ttgir(parse_result)

    # Generate correlation points
    correlation_points = _generate_correlations(
        isa_analysis, llvm_ir_analysis, ttgir_analysis
    )

    # Generate summary
    summary = _generate_summary(isa_analysis, llvm_ir_analysis, ttgir_analysis)

    # Generate recommendations
    recommendations = _generate_recommendations(
        isa_analysis, llvm_ir_analysis, ttgir_analysis
    )

    return CorrelatedAnalysis(
        isa_analysis=isa_analysis,
        llvm_ir_analysis=llvm_ir_analysis,
        ttgir_analysis=ttgir_analysis,
        correlation_points=tuple(correlation_points),
        summary=summary,
        recommendations=tuple(recommendations),
    )


def _generate_correlations(
    isa: Optional[ISAAnalysis],
    llvm_ir: Optional[LLVMIRAnalysis],
    ttgir: Optional[TTGIRAnalysis],
) -> list[CorrelationPoint]:
    """Generate correlation points between artifacts."""
    points = []

    # Correlate MFMA instructions with tt.dot operations
    if isa and ttgir:
        if isa.mfma_count > 0 and ttgir.dot_count > 0:
            points.append(CorrelationPoint(
                ttgir_op="tt.dot",
                isa_instruction="v_mfma_*",
                description=f"{ttgir.dot_count} tt.dot operations "
                           f"compiled to {isa.mfma_count} MFMA instructions",
            ))

        # Correlate loads
        if isa.global_load_count > 0 and ttgir.load_count > 0:
            points.append(CorrelationPoint(
                ttgir_op="tt.load",
                isa_instruction="global_load_*",
                description=f"{ttgir.load_count} tt.load operations "
                           f"compiled to {isa.global_load_count} global loads",
            ))

    # Correlate spills with potential causes
    if isa and isa.spill_count > 0:
        if ttgir and ttgir.tile_info:
            tile = ttgir.tile_info
            sizes = []
            if tile.block_m:
                sizes.append(f"M={tile.block_m}")
            if tile.block_n:
                sizes.append(f"N={tile.block_n}")
            if tile.block_k:
                sizes.append(f"K={tile.block_k}")

            if sizes:
                points.append(CorrelationPoint(
                    ttgir_op=f"tile sizes: {', '.join(sizes)}",
                    isa_instruction="scratch_store/load",
                    description=f"Large tile sizes may be causing {isa.spill_count} register spills",
                ))

    return points


def _generate_summary(
    isa: Optional[ISAAnalysis],
    llvm_ir: Optional[LLVMIRAnalysis],
    ttgir: Optional[TTGIRAnalysis],
) -> str:
    """Generate a high-level summary of the analysis."""
    parts = []

    if isa:
        parts.append(f"ISA: {isa.kernel_name} ({isa.architecture})")
        parts.append(f"  VGPRs: {isa.vgpr_count}, SGPRs: {isa.sgpr_count}")
        parts.append(f"  MFMA: {isa.mfma_count}, Spills: {isa.spill_count}")
        parts.append(f"  Occupancy: {isa.theoretical_occupancy} waves/CU")

    if ttgir:
        parts.append("TTGIR:")
        parts.append(f"  tt.dot: {ttgir.dot_count}, tt.load: {ttgir.load_count}")
        if ttgir.tile_info:
            tile = ttgir.tile_info
            parts.append(f"  Tiles: M={tile.block_m}, N={tile.block_n}, K={tile.block_k}")
            if ttgir.has_software_pipelining:
                parts.append(f"  Pipelining: {tile.num_stages} stages")

    if llvm_ir:
        parts.append("LLVM-IR:")
        parts.append(f"  Functions: {llvm_ir.function_count}")
        if llvm_ir.has_vector_ops:
            parts.append("  Vectorization: detected")

    return "\n".join(parts)


def _generate_recommendations(
    isa: Optional[ISAAnalysis],
    llvm_ir: Optional[LLVMIRAnalysis],
    ttgir: Optional[TTGIRAnalysis],
) -> list[str]:
    """Generate optimization recommendations based on analysis."""
    recommendations = []

    if isa:
        # Spill recommendations
        if isa.spill_count > 0:
            recommendations.append(
                "CRITICAL: Register spills detected. Consider:\n"
                "  - Reducing tile sizes (BLOCK_M, BLOCK_N, BLOCK_K)\n"
                "  - Simplifying kernel logic\n"
                "  - Using smaller data types (fp16 instead of fp32)"
            )

        # Low MFMA density
        if isa.mfma_count > 0 and isa.mfma_density_pct < 20:
            recommendations.append(
                f"Low MFMA density ({isa.mfma_density_pct:.1f}%). Consider:\n"
                "  - Increasing tile sizes for better compute intensity\n"
                "  - Reducing control flow in hot loops\n"
                "  - Using tensor core-friendly layouts"
            )

        # Low occupancy
        if isa.theoretical_occupancy < 4:
            if isa.vgpr_count > 128:
                recommendations.append(
                    f"Low occupancy ({isa.theoretical_occupancy} waves) due to high VGPR usage ({isa.vgpr_count}). Consider:\n"
                    "  - Reducing live register pressure\n"
                    "  - Using more temporaries that can be reused"
                )
            if isa.lds_size > 32768:
                recommendations.append(
                    f"Low occupancy due to high LDS usage ({isa.lds_size} bytes). Consider:\n"
                    "  - Reducing shared memory footprint\n"
                    "  - Using multi-stage approaches to reduce peak LDS"
                )

    if ttgir:
        # Pipelining recommendation
        if ttgir.dot_count > 0 and not ttgir.has_software_pipelining:
            recommendations.append(
                "No software pipelining detected. Consider:\n"
                "  - Adding num_stages > 1 to enable pipelining\n"
                "  - This helps hide memory latency"
            )

        # Compute intensity
        if ttgir.estimated_compute_intensity is not None:
            if ttgir.estimated_compute_intensity < 10:
                recommendations.append(
                    f"Low compute intensity ({ttgir.estimated_compute_intensity:.1f} FLOPs/byte). Consider:\n"
                    "  - Increasing tile sizes to improve data reuse\n"
                    "  - Kernel fusion to reduce memory traffic"
                )

    return recommendations
