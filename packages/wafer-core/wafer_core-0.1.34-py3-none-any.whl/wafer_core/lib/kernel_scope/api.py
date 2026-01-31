"""High-level API for Kernel Scope analysis.

Provides simple functions for common analysis workflows.
Supports both:
- Local analysis of Triton compilation artifacts (.s, .ll, .ttgir)
- API-based analysis of AMD GPU code objects (.co files)

Design: Wafer-436 - AMD Kernel Scope
"""

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional, Iterator

import httpx

from wafer_core.lib.kernel_scope.amdgcn import (
    parse_isa_file,
    parse_isa_text,
    analyze_isa,
    ISAAnalysis,
)
from wafer_core.lib.kernel_scope.llvm_ir import (
    parse_llvm_ir_file,
    analyze_llvm_ir,
    LLVMIRAnalysis,
)
from wafer_core.lib.kernel_scope.ttgir import (
    parse_ttgir_file,
    analyze_ttgir,
    TTGIRAnalysis,
)
from wafer_core.lib.kernel_scope.correlation import correlate_artifacts


@dataclass(frozen=True)
class CodeObjectAnalysis:
    """Result of ISA analysis for AMD GPU code object (.co file).

    This is returned when analyzing .co files via the API server.
    The server uses ROCm LLVM tools to extract and analyze the ISA.
    """

    kernel_name: str
    architecture: str

    # Register usage
    vgpr_count: int
    sgpr_count: int
    agpr_count: int
    vgpr_spill_count: int
    sgpr_spill_count: int

    # Memory
    lds_bytes: int
    global_loads: int
    global_stores: int
    lds_ops: int

    # Instructions
    mfma_count: int
    fma_count: int
    packed_ops_count: int
    waitcnt_full_stalls: int
    barriers: int

    # Raw data
    isa_text: str
    metadata_yaml: str
    annotated_isa_text: str


@dataclass(frozen=True)
class AnalysisResult:
    """Result of analyzing a single file.

    Attributes:
        success: Whether analysis succeeded
        error: Error message if failed
        file_path: Path to analyzed file
        file_type: Type of file ("isa", "llvm_ir", "ttgir", "code_object")
        isa_analysis: ISA analysis result (if ISA file)
        llvm_ir_analysis: LLVM-IR analysis (if LLVM-IR file)
        ttgir_analysis: TTGIR analysis (if TTGIR file)
        code_object_analysis: Code object analysis (if .co file)
    """

    success: bool
    error: Optional[str] = None
    file_path: Optional[str] = None
    file_type: Optional[str] = None
    isa_analysis: Optional[ISAAnalysis] = None
    llvm_ir_analysis: Optional[LLVMIRAnalysis] = None
    ttgir_analysis: Optional[TTGIRAnalysis] = None
    code_object_analysis: Optional[CodeObjectAnalysis] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        result = {
            "success": self.success,
            "file_path": self.file_path,
            "file_type": self.file_type,
        }

        if self.error:
            result["error"] = self.error

        if self.isa_analysis:
            result["isa_analysis"] = _isa_analysis_to_dict(self.isa_analysis)

        if self.llvm_ir_analysis:
            result["llvm_ir_analysis"] = asdict(self.llvm_ir_analysis)

        if self.ttgir_analysis:
            result["ttgir_analysis"] = _ttgir_analysis_to_dict(self.ttgir_analysis)

        if self.code_object_analysis:
            result["code_object_analysis"] = _code_object_analysis_to_dict(
                self.code_object_analysis
            )

        return result

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)


@dataclass(frozen=True)
class BatchAnalysisResult:
    """Result of analyzing multiple files.

    Attributes:
        total_files: Total number of files processed
        successful: Number of successful analyses
        failed: Number of failed analyses
        results: Individual results for each file
        summary: Aggregated summary statistics
    """

    total_files: int
    successful: int
    failed: int
    results: tuple[AnalysisResult, ...] = field(default_factory=tuple)
    summary: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "total_files": self.total_files,
            "successful": self.successful,
            "failed": self.failed,
            "summary": self.summary,
            "results": [r.to_dict() for r in self.results],
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)


def analyze_isa_file(
    file_path: str | Path,
    kernel_index: int = 0,
) -> AnalysisResult:
    """Analyze an AMDGCN ISA assembly file.

    This is the main entry point for single-file ISA analysis.

    Args:
        file_path: Path to .s, .gcn, or .asm file
        kernel_index: Which kernel to analyze if multiple present

    Returns:
        AnalysisResult with ISA analysis

    Example:
        >>> result = analyze_isa_file("kernel.s")
        >>> if result.success:
        ...     print(f"VGPR: {result.isa_analysis.vgpr_count}")
        ...     print(f"Spills: {result.isa_analysis.spill_count}")
    """
    path = Path(file_path)

    parse_result = parse_isa_file(path)

    if not parse_result.success:
        return AnalysisResult(
            success=False,
            error=parse_result.error,
            file_path=str(path),
            file_type="isa",
        )

    if not parse_result.kernels:
        return AnalysisResult(
            success=False,
            error="No kernels found in file",
            file_path=str(path),
            file_type="isa",
        )

    try:
        analysis = analyze_isa(parse_result, kernel_index)
        return AnalysisResult(
            success=True,
            file_path=str(path),
            file_type="isa",
            isa_analysis=analysis,
        )
    except Exception as e:
        return AnalysisResult(
            success=False,
            error=str(e),
            file_path=str(path),
            file_type="isa",
        )


def analyze_code_object(
    file_path: str | Path,
    api_url: str,
    auth_headers: dict[str, str],
    timeout: float = 60.0,
) -> AnalysisResult:
    """Analyze AMD GPU code object (.co file) via wafer-api.

    .co files are compiled GPU code objects that require ROCm LLVM tools
    to disassemble and analyze. This function sends the file to the
    wafer-api server which has the necessary tools installed.

    Args:
        file_path: Path to the .co file to analyze
        api_url: Base URL of the wafer-api server
        auth_headers: Authorization headers (e.g., {"Authorization": "Bearer ..."})
        timeout: Request timeout in seconds

    Returns:
        AnalysisResult with code object analysis

    Example:
        >>> result = analyze_code_object(
        ...     "kernel.co",
        ...     api_url="https://api.wafer.dev",
        ...     auth_headers={"Authorization": "Bearer ..."},
        ... )
        >>> if result.success:
        ...     print(f"VGPR: {result.code_object_analysis.vgpr_count}")
    """
    path = Path(file_path)

    # Validate file
    if not path.exists():
        return AnalysisResult(
            success=False,
            error=f"File not found: {file_path}",
            file_path=str(path),
            file_type="code_object",
        )

    if path.suffix.lower() != ".co":
        return AnalysisResult(
            success=False,
            error=f"Expected .co file, got: {path.suffix}",
            file_path=str(path),
            file_type="code_object",
        )

    try:
        # Read file content
        content = path.read_bytes()

        # Call API
        with httpx.Client(timeout=timeout, headers=auth_headers) as client:
            files = {"file": (path.name, content, "application/octet-stream")}
            response = client.post(f"{api_url}/v1/isa/analyze", files=files)
            response.raise_for_status()
            data = response.json()

        # Validate response has required fields
        required_fields = [
            "kernel_name", "architecture", "vgpr_count", "sgpr_count",
            "agpr_count", "vgpr_spill_count", "sgpr_spill_count", "lds_bytes",
            "global_loads", "global_stores", "lds_ops", "mfma_count",
            "fma_count", "packed_ops_count", "waitcnt_full_stalls", "barriers",
            "isa_text", "metadata_yaml"
        ]
        missing = [f for f in required_fields if f not in data]
        if missing:
            return AnalysisResult(
                success=False,
                error=f"API response missing required fields: {missing}",
                file_path=str(path),
                file_type="code_object",
            )

        # Build result
        code_obj = CodeObjectAnalysis(
            kernel_name=data["kernel_name"],
            architecture=data["architecture"],
            vgpr_count=data["vgpr_count"],
            sgpr_count=data["sgpr_count"],
            agpr_count=data["agpr_count"],
            vgpr_spill_count=data["vgpr_spill_count"],
            sgpr_spill_count=data["sgpr_spill_count"],
            lds_bytes=data["lds_bytes"],
            global_loads=data["global_loads"],
            global_stores=data["global_stores"],
            lds_ops=data["lds_ops"],
            mfma_count=data["mfma_count"],
            fma_count=data["fma_count"],
            packed_ops_count=data["packed_ops_count"],
            waitcnt_full_stalls=data["waitcnt_full_stalls"],
            barriers=data["barriers"],
            isa_text=data["isa_text"],
            metadata_yaml=data["metadata_yaml"],
            annotated_isa_text=data.get("annotated_isa_text", data["isa_text"]),
        )

        return AnalysisResult(
            success=True,
            file_path=str(path),
            file_type="code_object",
            code_object_analysis=code_obj,
        )

    except httpx.HTTPStatusError as e:
        return AnalysisResult(
            success=False,
            error=f"API error ({e.response.status_code}): {e.response.text}",
            file_path=str(path),
            file_type="code_object",
        )
    except httpx.RequestError as e:
        return AnalysisResult(
            success=False,
            error=f"Request failed: {str(e)}",
            file_path=str(path),
            file_type="code_object",
        )
    except KeyError as e:
        return AnalysisResult(
            success=False,
            error=f"API response missing required field: {e}",
            file_path=str(path),
            file_type="code_object",
        )
    except Exception as e:
        return AnalysisResult(
            success=False,
            error=f"Unexpected error: {str(e)}",
            file_path=str(path),
            file_type="code_object",
        )


def analyze_file(
    file_path: str | Path,
    api_url: Optional[str] = None,
    auth_headers: Optional[dict[str, str]] = None,
) -> AnalysisResult:
    """Analyze a file, auto-detecting its type.

    Supports:
    - .s, .gcn, .asm: AMDGCN ISA (local analysis)
    - .ll, .bc: LLVM-IR (local analysis)
    - .ttgir, .ttir, .mlir: TTGIR (local analysis)
    - .co: AMD GPU code objects (requires API server with ROCm tools)

    Args:
        file_path: Path to artifact file
        api_url: API URL for .co file analysis (required for .co files)
        auth_headers: Auth headers for API (required for .co files)

    Returns:
        AnalysisResult with appropriate analysis
    """
    path = Path(file_path)
    suffix = path.suffix.lower()

    # Code object files (.co) - need API
    if suffix == ".co":
        if not api_url or not auth_headers:
            return AnalysisResult(
                success=False,
                error="API URL and auth headers required for .co file analysis",
                file_path=str(path),
                file_type="code_object",
            )
        return analyze_code_object(path, api_url, auth_headers)

    # ISA files
    if suffix in (".s", ".gcn", ".asm"):
        return analyze_isa_file(path)

    # LLVM-IR files
    if suffix in (".ll", ".bc"):
        parse_result = parse_llvm_ir_file(path)
        if not parse_result.success:
            return AnalysisResult(
                success=False,
                error=parse_result.error,
                file_path=str(path),
                file_type="llvm_ir",
            )
        try:
            analysis = analyze_llvm_ir(parse_result)
            return AnalysisResult(
                success=True,
                file_path=str(path),
                file_type="llvm_ir",
                llvm_ir_analysis=analysis,
            )
        except Exception as e:
            return AnalysisResult(
                success=False,
                error=str(e),
                file_path=str(path),
                file_type="llvm_ir",
            )

    # TTGIR files
    if suffix in (".ttgir", ".ttir", ".mlir"):
        parse_result = parse_ttgir_file(path)
        if not parse_result.success:
            return AnalysisResult(
                success=False,
                error=parse_result.error,
                file_path=str(path),
                file_type="ttgir",
            )
        try:
            analysis = analyze_ttgir(parse_result)
            return AnalysisResult(
                success=True,
                file_path=str(path),
                file_type="ttgir",
                ttgir_analysis=analysis,
            )
        except Exception as e:
            return AnalysisResult(
                success=False,
                error=str(e),
                file_path=str(path),
                file_type="ttgir",
            )

    return AnalysisResult(
        success=False,
        error=f"Unsupported file type: {suffix}",
        file_path=str(path),
    )


def analyze_directory(
    directory: str | Path,
    recursive: bool = True,
    file_extensions: Optional[list[str]] = None,
    api_url: Optional[str] = None,
    auth_headers: Optional[dict[str, str]] = None,
) -> BatchAnalysisResult:
    """Analyze all supported files in a directory.

    Useful for batch analysis of Triton cache directories.

    Args:
        directory: Directory to scan
        recursive: Whether to scan subdirectories
        file_extensions: Extensions to include (default: all supported except .co)
        api_url: API URL for .co file analysis (required if .co in extensions)
        auth_headers: Auth headers for API (required if .co in extensions)

    Returns:
        BatchAnalysisResult with all analysis results

    Example:
        >>> result = analyze_directory("~/.triton/cache/")
        >>> for r in result.results:
        ...     if r.success and r.isa_analysis.spill_count > 0:
        ...         print(f"Spills in {r.file_path}")
    """
    path = Path(directory).expanduser()

    if not path.exists():
        return BatchAnalysisResult(
            total_files=0,
            successful=0,
            failed=1,
            results=(AnalysisResult(
                success=False,
                error=f"Directory not found: {directory}",
            ),),
        )

    # Default extensions - include .co only when API credentials are provided
    if file_extensions is None:
        file_extensions = [".s", ".gcn", ".asm", ".ll", ".ttgir", ".ttir", ".mlir"]
        # Include .co files when API params are provided
        if api_url and auth_headers:
            file_extensions.append(".co")

    # Find files
    files = list(_find_files(path, file_extensions, recursive))

    if not files:
        return BatchAnalysisResult(
            total_files=0,
            successful=0,
            failed=0,
            summary={"note": "No supported files found"},
        )

    # Analyze each file
    results = []
    successful = 0
    failed = 0

    for file_path in files:
        result = analyze_file(file_path, api_url=api_url, auth_headers=auth_headers)
        results.append(result)

        if result.success:
            successful += 1
        else:
            failed += 1

    # Compute summary
    summary = _compute_batch_summary(results)

    return BatchAnalysisResult(
        total_files=len(files),
        successful=successful,
        failed=failed,
        results=tuple(results),
        summary=summary,
    )


def _find_files(
    directory: Path,
    extensions: list[str],
    recursive: bool,
) -> Iterator[Path]:
    """Find files with given extensions in directory."""
    pattern_func = directory.rglob if recursive else directory.glob

    for ext in extensions:
        for file_path in pattern_func(f"*{ext}"):
            if file_path.is_file():
                yield file_path


def _compute_batch_summary(results: list[AnalysisResult]) -> dict:
    """Compute summary statistics from batch results."""
    summary = {
        "total_vgpr_avg": 0.0,
        "total_sgpr_avg": 0.0,
        "total_spills": 0,
        "files_with_spills": 0,
        "total_mfma": 0,
        "avg_mfma_density": 0.0,
    }

    isa_results = [r for r in results if r.success and r.isa_analysis]

    if not isa_results:
        return summary

    vgpr_sum = sum(r.isa_analysis.vgpr_count for r in isa_results)
    sgpr_sum = sum(r.isa_analysis.sgpr_count for r in isa_results)
    total_spills = sum(r.isa_analysis.spill_count for r in isa_results)
    files_with_spills = sum(1 for r in isa_results if r.isa_analysis.spill_count > 0)
    total_mfma = sum(r.isa_analysis.mfma_count for r in isa_results)
    mfma_density_sum = sum(r.isa_analysis.mfma_density_pct for r in isa_results)

    n = len(isa_results)
    summary["total_vgpr_avg"] = vgpr_sum / n
    summary["total_sgpr_avg"] = sgpr_sum / n
    summary["total_spills"] = total_spills
    summary["files_with_spills"] = files_with_spills
    summary["total_mfma"] = total_mfma
    summary["avg_mfma_density"] = mfma_density_sum / n

    return summary


def _isa_analysis_to_dict(analysis: ISAAnalysis) -> dict:
    """Convert ISAAnalysis to dictionary."""
    return {
        "kernel_name": analysis.kernel_name,
        "architecture": analysis.architecture,
        "vgpr_count": analysis.vgpr_count,
        "sgpr_count": analysis.sgpr_count,
        "agpr_count": analysis.agpr_count,
        "lds_size": analysis.lds_size,
        "scratch_size": analysis.scratch_size,
        "instruction_mix": {
            "valu": analysis.instruction_mix.valu_count,
            "salu": analysis.instruction_mix.salu_count,
            "vmem": analysis.instruction_mix.vmem_count,
            "smem": analysis.instruction_mix.smem_count,
            "lds": analysis.instruction_mix.lds_count,
            "mfma": analysis.instruction_mix.mfma_count,
            "control": analysis.instruction_mix.control_count,
            "sync": analysis.instruction_mix.sync_count,
            "spill": analysis.instruction_mix.spill_count,
            "total": analysis.instruction_mix.total_count,
        },
        "spill_count": analysis.spill_count,
        "vgpr_spill_count": analysis.vgpr_spill_count,
        "sgpr_spill_count": analysis.sgpr_spill_count,
        "mfma_count": analysis.mfma_count,
        "mfma_density_pct": analysis.mfma_density_pct,
        "packed_ops_count": analysis.packed_ops_count,
        "fma_count": analysis.fma_count,
        "barrier_count": analysis.barrier_count,
        "full_stall_count": analysis.full_stall_count,
        "global_load_count": analysis.global_load_count,
        "global_store_count": analysis.global_store_count,
        "lds_ops_count": analysis.lds_ops_count,
        "max_waves_vgpr": analysis.max_waves_vgpr,
        "max_waves_sgpr": analysis.max_waves_sgpr,
        "max_waves_lds": analysis.max_waves_lds,
        "theoretical_occupancy": analysis.theoretical_occupancy,
        "warnings": list(analysis.warnings),
    }


def _ttgir_analysis_to_dict(analysis: TTGIRAnalysis) -> dict:
    """Convert TTGIRAnalysis to dictionary."""
    result = {
        "dot_count": analysis.dot_count,
        "load_count": analysis.load_count,
        "store_count": analysis.store_count,
        "reduce_count": analysis.reduce_count,
        "barrier_count": analysis.barrier_count,
        "has_software_pipelining": analysis.has_software_pipelining,
        "estimated_compute_intensity": analysis.estimated_compute_intensity,
    }

    if analysis.tile_info:
        result["tile_info"] = {
            "block_m": analysis.tile_info.block_m,
            "block_n": analysis.tile_info.block_n,
            "block_k": analysis.tile_info.block_k,
            "num_warps": analysis.tile_info.num_warps,
            "num_stages": analysis.tile_info.num_stages,
        }

    return result


def _code_object_analysis_to_dict(analysis: CodeObjectAnalysis) -> dict:
    """Convert CodeObjectAnalysis to dictionary."""
    return {
        "kernel_name": analysis.kernel_name,
        "architecture": analysis.architecture,
        "vgpr_count": analysis.vgpr_count,
        "sgpr_count": analysis.sgpr_count,
        "agpr_count": analysis.agpr_count,
        "vgpr_spill_count": analysis.vgpr_spill_count,
        "sgpr_spill_count": analysis.sgpr_spill_count,
        "lds_bytes": analysis.lds_bytes,
        "global_loads": analysis.global_loads,
        "global_stores": analysis.global_stores,
        "lds_ops": analysis.lds_ops,
        "mfma_count": analysis.mfma_count,
        "fma_count": analysis.fma_count,
        "packed_ops_count": analysis.packed_ops_count,
        "waitcnt_full_stalls": analysis.waitcnt_full_stalls,
        "barriers": analysis.barriers,
        "isa_text": analysis.isa_text,
        "metadata_yaml": analysis.metadata_yaml,
        "annotated_isa_text": analysis.annotated_isa_text,
    }


def format_code_object_summary(result: CodeObjectAnalysis) -> str:
    """Format code object analysis result as human-readable summary.

    Args:
        result: CodeObjectAnalysis to format

    Returns:
        Formatted string summary
    """
    lines = [
        f"Kernel: {result.kernel_name}",
        f"Architecture: {result.architecture}",
        "",
        "=== Registers ===",
        f"  VGPRs: {result.vgpr_count}",
        f"  SGPRs: {result.sgpr_count}",
        f"  AGPRs: {result.agpr_count}",
    ]

    # Spills warning
    if result.vgpr_spill_count > 0 or result.sgpr_spill_count > 0:
        lines.append("")
        lines.append("!!! SPILLS DETECTED !!!")
        if result.vgpr_spill_count > 0:
            lines.append(f"  VGPR spills: {result.vgpr_spill_count}")
        if result.sgpr_spill_count > 0:
            lines.append(f"  SGPR spills: {result.sgpr_spill_count}")
    else:
        lines.append("  Spills: None (good)")

    lines.extend([
        "",
        "=== Memory ===",
        f"  LDS: {result.lds_bytes} bytes",
        f"  Global loads: {result.global_loads}",
        f"  Global stores: {result.global_stores}",
        f"  LDS ops: {result.lds_ops}",
        "",
        "=== Instructions ===",
        f"  MFMA: {result.mfma_count}",
        f"  FMA: {result.fma_count}",
        f"  Packed (v_pk_*): {result.packed_ops_count}",
        f"  Full stalls (waitcnt 0): {result.waitcnt_full_stalls}",
        f"  Barriers: {result.barriers}",
    ])

    return "\n".join(lines)
