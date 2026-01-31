"""ISA Analysis Tool - Analyze AMD GPU code objects via wafer-api.

This tool sends .co files to the wafer-api server which has ROCm LLVM tools
installed, and returns the analysis results.
"""

from pathlib import Path

import httpx

from .types import ISAAnalysisResult


def analyze_isa(
    co_file_path: Path,
    api_url: str,
    auth_headers: dict[str, str],
    timeout: float = 60.0,
) -> ISAAnalysisResult:
    """Analyze AMD GPU code object (.co file) via wafer-api.

    Args:
        co_file_path: Path to the .co file to analyze
        api_url: Base URL of the wafer-api server
        auth_headers: Authorization headers (e.g., {"Authorization": "Bearer ..."})
        timeout: Request timeout in seconds

    Returns:
        ISAAnalysisResult with analysis data

    Raises:
        FileNotFoundError: If co_file_path doesn't exist
        ValueError: If file is not a .co file
        httpx.HTTPError: If API request fails
    """
    # Validate file
    if not co_file_path.exists():
        raise FileNotFoundError(f"File not found: {co_file_path}")

    if not co_file_path.suffix == ".co":
        raise ValueError(f"Expected .co file, got: {co_file_path.suffix}")

    # Read file content
    content = co_file_path.read_bytes()

    # Call API
    with httpx.Client(timeout=timeout, headers=auth_headers) as client:
        files = {"file": (co_file_path.name, content, "application/octet-stream")}
        response = client.post(f"{api_url}/v1/isa/analyze", files=files)
        response.raise_for_status()
        data = response.json()

    # Build result
    return ISAAnalysisResult(
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
        annotated_isa_text=data.get("annotated_isa_text", data["isa_text"]),  # Fallback for backward compatibility
    )


def format_isa_summary(result: ISAAnalysisResult) -> str:
    """Format ISA analysis result as human-readable summary.

    Args:
        result: ISAAnalysisResult to format

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
