"""Kernel Scope - Static ISA Analysis for Triton Kernels.

This module provides static analysis tools for AMD GPU compilation artifacts:
- AMDGCN ISA assembly files (.s, .gcn, .asm) - Local parsing
- LLVM-IR files (.ll, .bc) - Local parsing
- TTGIR files (.ttgir, .ttir, .mlir) - Local parsing
- AMD GPU code objects (.co) - Via API server with ROCm tools

Design: Wafer-436

Example usage:
    from wafer_core.lib.kernel_scope import (
        analyze_isa_file,
        analyze_code_object,
        analyze_file,
        analyze_directory,
    )

    # Single ISA file analysis (local)
    result = analyze_isa_file("kernel.s")
    if result.success:
        print(f"VGPR count: {result.isa_analysis.vgpr_count}")
        print(f"Register spills: {result.isa_analysis.spill_count}")
        print(f"MFMA density: {result.isa_analysis.mfma_density_pct:.1f}%")

    # Code object analysis (via API)
    result = analyze_code_object(
        "kernel.co",
        api_url="https://api.wafer.dev",
        auth_headers={"Authorization": "Bearer ..."},
    )
    if result.success:
        print(f"VGPR count: {result.code_object_analysis.vgpr_count}")

    # Auto-detect file type
    result = analyze_file("kernel.s")  # Local
    result = analyze_file("kernel.co", api_url=..., auth_headers=...)  # API

    # Directory batch analysis
    results = analyze_directory("~/.triton/cache/")
    for r in results.results:
        if r.success and r.isa_analysis and r.isa_analysis.spill_count > 0:
            print(f"WARNING: {r.file_path} has spills")
"""

from wafer_core.lib.kernel_scope.amdgcn.parser import parse_isa_file, parse_isa_text
from wafer_core.lib.kernel_scope.amdgcn.analyzer import analyze_isa, ISAAnalysis
from wafer_core.lib.kernel_scope.amdgcn.types import (
    ISAParseResult,
    KernelMetadata,
    InstructionInfo,
    InstructionCategory,
)
from wafer_core.lib.kernel_scope.metrics.occupancy import (
    compute_occupancy,
    OccupancyResult,
)
from wafer_core.lib.kernel_scope.targets import get_target_specs, TargetSpecs
from wafer_core.lib.kernel_scope.api import (
    analyze_isa_file,
    analyze_code_object,
    analyze_file,
    analyze_directory,
    AnalysisResult,
    BatchAnalysisResult,
    CodeObjectAnalysis,
    format_code_object_summary,
)

__all__ = [
    # High-level API
    "analyze_isa_file",
    "analyze_code_object",
    "analyze_file",
    "analyze_directory",
    "AnalysisResult",
    "BatchAnalysisResult",
    "CodeObjectAnalysis",
    "format_code_object_summary",
    # Low-level components
    "parse_isa_file",
    "parse_isa_text",
    "analyze_isa",
    "ISAAnalysis",
    "ISAParseResult",
    "KernelMetadata",
    "InstructionInfo",
    "InstructionCategory",
    "compute_occupancy",
    "OccupancyResult",
    "get_target_specs",
    "TargetSpecs",
]
