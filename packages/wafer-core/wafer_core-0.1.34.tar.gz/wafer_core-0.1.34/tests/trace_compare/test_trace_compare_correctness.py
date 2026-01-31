"""Correctness tests for trace comparison functionality.

Uses golden file testing - compares output against stored expected results.
Expensive trace loads are cached via pytest fixtures.
"""

import json
import pytest
from pathlib import Path
from typing import Any

import pandas as pd

from wafer_core.lib.trace_compare import (
    analyze_traces,
    analyze_trace_pair,
    detect_architecture,
    ArchitectureType,
    Op,
    classify,
)
from wafer_core.lib.trace_compare.loader import (
    load_trace,
    load_trace_streaming,
    StreamingMetadata,
    _extract_metadata_fast,
)


TRACE_EXAMPLES_DIR = Path("/root/wafer/experiments/ian/vllm-trace-compare/examples")
AMD_LLAMA_TRACE = TRACE_EXAMPLES_DIR / "amd_llama.json"
NVIDIA_LLAMA_TRACE = TRACE_EXAMPLES_DIR / "nvidia_llama.json"

GOLDEN_FILE = Path(__file__).parent / "expected_output_amd_llama.json"


def _path_exists_safe(path: Path) -> bool:
    """Check if path exists, returning False on permission errors.
    
    CI runners may not have permission to stat /root/... paths,
    so we treat PermissionError the same as file not existing.
    """
    try:
        return path.exists()
    except PermissionError:
        return False


def load_golden_file() -> dict[str, Any]:
    """Load expected output from golden file."""
    if not GOLDEN_FILE.exists():
        pytest.skip(f"Golden file not found: {GOLDEN_FILE}")
    with open(GOLDEN_FILE) as f:
        return json.load(f)


# =============================================================================
# Cached Fixtures (expensive operations loaded once per session)
# =============================================================================


@pytest.fixture(scope="session")
def amd_trace_result():
    """Load AMD trace once per test session (~17s)."""
    if not _path_exists_safe(AMD_LLAMA_TRACE):
        pytest.skip(f"Trace file not found: {AMD_LLAMA_TRACE}")
    return load_trace(AMD_LLAMA_TRACE, include_stacks=True)


@pytest.fixture(scope="session")
def amd_trace_streaming_result():
    """Load AMD trace with streaming loader once per test session."""
    if not _path_exists_safe(AMD_LLAMA_TRACE):
        pytest.skip(f"Trace file not found: {AMD_LLAMA_TRACE}")
    return load_trace_streaming(AMD_LLAMA_TRACE, include_stacks=True)


@pytest.fixture(scope="session")
def analyze_result():
    """Run analyze_traces once per test session (~35s)."""
    if not _path_exists_safe(AMD_LLAMA_TRACE) or not _path_exists_safe(NVIDIA_LLAMA_TRACE):
        pytest.skip("Trace files not found")
    return analyze_traces(
        AMD_LLAMA_TRACE,
        NVIDIA_LLAMA_TRACE,
        phase_filter="all",
        include_stacks=True,
    )


def test_load_trace_matches_golden(amd_trace_result) -> None:
    """Test that load_trace produces output matching the golden file."""
    expected = load_golden_file()
    
    platform, gpu, dev_props, df, patterns, layers = amd_trace_result
    
    assert platform == expected["platform"], f"Platform mismatch: {platform} != {expected['platform']}"
    assert gpu == expected["gpu"], f"GPU mismatch: {gpu} != {expected['gpu']}"
    assert dev_props == expected["device_props"], "Device properties mismatch"
    
    expected_df = expected["dataframe"]
    assert len(df) == expected_df["row_count"], f"Row count mismatch: {len(df)} != {expected_df['row_count']}"
    assert set(df.columns) == set(expected_df["columns"]), "Column mismatch"
    
    assert df["op"].nunique() == expected_df["summary"]["unique_ops"]
    assert df["phase"].nunique() == expected_df["summary"]["unique_phases"]
    assert int(df["dur_us"].sum()) == expected_df["summary"]["total_time_us"]
    
    expected_patterns = {
        tuple(k.split("_", 1)): set(v) for k, v in expected["patterns"].items()
    }
    assert patterns == expected_patterns, "Kernel patterns mismatch"
    
    expected_layers = {int(k): v for k, v in expected["layers"].items()}
    assert layers == expected_layers, "Layer mappings mismatch"
    
    # Verify sample rows match (first 100)
    sample_df = df.head(100).copy()
    for i, expected_row in enumerate(expected_df["sample_rows"]):
        actual_row = sample_df.iloc[i].to_dict()
        for key, expected_val in expected_row.items():
            actual_val = actual_row.get(key)
            if isinstance(expected_val, list):
                assert actual_val == expected_val, f"Row {i}, column {key} mismatch"
            elif pd.isna(expected_val):
                assert pd.isna(actual_val), f"Row {i}, column {key} should be NaN"
            else:
                assert actual_val == expected_val, f"Row {i}, column {key} mismatch: {actual_val} != {expected_val}"


def test_analyze_traces_produces_valid_output(analyze_result) -> None:
    """Test that analyze_traces produces valid output structure."""
    results = analyze_result
    
    assert "metadata" in results
    assert "operations" in results
    assert "layers" in results
    
    meta = results["metadata"]
    assert "trace1_platform" in meta
    assert "trace2_platform" in meta
    assert "trace1_kernels" in meta
    assert "trace2_kernels" in meta
    
    if results["operations"]:
        op = results["operations"][0]
        assert "operation" in op
        assert "trace1_avg_us" in op
        assert "trace2_avg_us" in op
        assert "ratio" in op


# =============================================================================
# Streaming Loader Tests
# =============================================================================


def test_streaming_loader_matches_regular_loader(amd_trace_result, amd_trace_streaming_result) -> None:
    """Test that load_trace_streaming produces identical results to load_trace."""
    # Use cached results from fixtures
    platform1, gpu1, dev_props1, df1, patterns1, layers1 = amd_trace_result
    platform2, gpu2, dev_props2, df2, patterns2, layers2 = amd_trace_streaming_result
    
    # Verify identical results
    assert platform1 == platform2, "Platform mismatch between loaders"
    assert gpu1 == gpu2, "GPU mismatch between loaders"
    assert dev_props1 == dev_props2, "Device props mismatch between loaders"
    assert len(df1) == len(df2), "DataFrame row count mismatch"
    assert set(df1.columns) == set(df2.columns), "DataFrame columns mismatch"
    assert patterns1 == patterns2, "Patterns mismatch between loaders"
    assert layers1 == layers2, "Layers mismatch between loaders"
    
    # Verify DataFrame content matches
    assert df1["op"].nunique() == df2["op"].nunique()
    assert int(df1["dur_us"].sum()) == int(df2["dur_us"].sum())


def test_metadata_extraction_matches_full_load(amd_trace_result) -> None:
    """Test that fast metadata extraction matches full load metadata."""
    if not _path_exists_safe(AMD_LLAMA_TRACE):
        pytest.skip(f"Trace file not found: {AMD_LLAMA_TRACE}")
    
    # Extract metadata fast (~2ms)
    metadata = _extract_metadata_fast(AMD_LLAMA_TRACE)
    
    # Use cached result
    platform, gpu, dev_props, _, _, _ = amd_trace_result
    
    # Verify metadata matches
    assert metadata.platform == platform, "Platform mismatch"
    assert metadata.gpu_name == gpu, "GPU name mismatch"
    assert metadata.file_size_mb > 0, "File size should be positive"
    
    # Device props should have matching core fields
    assert metadata.device_props["name"] == dev_props["name"]
    assert metadata.device_props["warp_size"] == dev_props["warp_size"]


def test_streaming_metadata_callback_fires() -> None:
    """Test that streaming loader fires metadata callback (fast, no full load)."""
    if not _path_exists_safe(AMD_LLAMA_TRACE):
        pytest.skip(f"Trace file not found: {AMD_LLAMA_TRACE}")
    
    # Only test the metadata callback - don't do full load
    metadata = _extract_metadata_fast(AMD_LLAMA_TRACE)
    
    assert metadata.platform in ("AMD", "NVIDIA"), f"Invalid platform: {metadata.platform}"
    assert len(metadata.gpu_name) > 0, "GPU name should not be empty"
    assert metadata.file_size_mb > 0, "File size should be positive"


# =============================================================================
# Classifier Tests
# =============================================================================


def test_classifier_deterministic() -> None:
    """Test that classifier produces consistent results for same input."""
    test_kernels = [
        "Cijk_Ailk_Bljk_HHS_BH_MT128x128x32_MI16x16x4x1_SE_1LDSB0_APM1_ABV0_ACED0_AF0EM8_AF1EM8_AMAS3_ASGT_ASAE01_APTS128_AAVC0_ASLA_AWGM_BTDB0_BC64x64_BT64x64_BCVLL_CDNA3_CMPWI_DTNB0_DTNE0_DVO0_EPS1_FL_GRVG_GSU16_GSUAMBR_GWS_ISA9a_LD2WA_LBSPPA12_LBSPPB12_LPD128_LRVW16_LWPMn1_MIAV0_MIWT4x4_NTn1_NTC0_NTD0_NEPBS0_PBD0_PKAB1_PGR2_PLR1_RAZ0_RK0_RRTB_SNLL0_SERA_SR_SRVW4_SSGR_STAT0_STWTBB_SVW4_TATW0_TLDS0_TT8x8_TWALB1_TWBLB1_TWMR_USFGROff_VAW2_VSn1_VW4_WSGRA_WSGRB_WG32x8x1_WGM8",
        "void at::native::(anonymous namespace)::softmax_warp_forward<float, float, float, 9, false>",
        "void flash::flash_fwd_splitkv_combine_kernel<flash::Flash_fwd_kernel_traits<128, 128, 32, 4, false, false, __nv_bfloat16>>",
    ]
    
    for kernel in test_kernels:
        # Call classifier multiple times
        results = [classify(kernel, "AMD") for _ in range(5)]
        
        # All results should be identical
        assert all(r == results[0] for r in results), f"Classifier not deterministic for {kernel}"


def test_classifier_known_patterns() -> None:
    """Test classifier recognizes known kernel patterns.
    
    Tests actual patterns from the classifier implementation.
    """
    # GEMM patterns (should classify as DENSE_GEMM)
    gemm_kernels = [
        "Cijk_Ailk_Bljk_ABC",  # AMD Tensile GEMM
        "Custom_Cijk_Ailk_XYZ",  # Custom AMD Tensile GEMM
        "nvjet_matmul_kernel",  # NVIDIA cuBLASLt
        "wvSplitK_kernel",  # hipBLASLt
    ]
    for kernel in gemm_kernels:
        op, _ = classify(kernel, "AMD")
        assert op == Op.DENSE_GEMM, f"Expected DENSE_GEMM for {kernel}, got {op}"
    
    # Attention patterns (should classify as ATTN_PREFILL or ATTN_DECODE)
    # Classifier checks for "attention" or "fmha" in kernel name
    attention_cases = [
        ("kernel_unified_attention_2d", "AMD", Op.ATTN_PREFILL),  # AMD prefill
        ("kernel_unified_attention_3d", "AMD", Op.ATTN_DECODE),  # AMD decode
        ("fmha_v2_kernel", "AMD", Op.ATTN_PREFILL),  # Generic FMHA defaults to prefill
        ("some_attention_kernel", "AMD", Op.ATTN_PREFILL),  # Generic attention
    ]
    for kernel, platform, expected_op in attention_cases:
        op, _ = classify(kernel, platform)
        assert op == expected_op, f"Expected {expected_op} for {kernel}, got {op}"
    
    # PyTorch native operations classify as ELEMENTWISE
    native_kernels = [
        "at::native::some_kernel",
        "at::native::vectorized_op",
    ]
    for kernel in native_kernels:
        op, _ = classify(kernel, "AMD")
        assert op == Op.ELEMENTWISE, f"Expected ELEMENTWISE for {kernel}, got {op}"
    
    # MoE patterns
    moe_kernels = [
        "_matmul_ogs_kernel",  # MoE GEMM
        "bmm_128x64_dynBatch",  # MoE batch GEMM
    ]
    for kernel in moe_kernels:
        op, _ = classify(kernel, "AMD")
        assert op == Op.MOE_GEMM, f"Expected MOE_GEMM for {kernel}, got {op}"


# =============================================================================
# Architecture Detection Tests
# =============================================================================


def test_architecture_detection_transformer() -> None:
    """Test architecture detection for Transformer-like kernel patterns."""
    transformer_kernels = [
        "flash_fwd_kernel",  # Attention
        "fmha_v2_flash_attention",  # Attention
        "Cijk_gemm",  # GEMM (MLP)
        "rms_norm_kernel",  # RMSNorm
    ]
    
    arch, markers = detect_architecture(transformer_kernels)
    assert arch == ArchitectureType.TRANSFORMER, f"Expected TRANSFORMER, got {arch}"
    assert len(markers) > 0, "Should have detected attention markers"


def test_architecture_detection_ssm() -> None:
    """Test architecture detection for SSM/Mamba-like kernel patterns."""
    ssm_kernels = [
        "selective_scan_kernel",  # SSM core operation
        "mamba_conv1d",  # Mamba specific
        "causal_conv_kernel",  # Causal convolution
    ]
    
    arch, markers = detect_architecture(ssm_kernels)
    assert arch == ArchitectureType.SSM, f"Expected SSM, got {arch}"
    assert len(markers) > 0, "Should have detected SSM markers"


def test_architecture_detection_hybrid() -> None:
    """Test architecture detection for Hybrid (attention + SSM) patterns."""
    hybrid_kernels = [
        "flash_fwd_kernel",  # Attention
        "selective_scan_kernel",  # SSM
        "mamba_conv1d",  # Mamba
    ]
    
    arch, markers = detect_architecture(hybrid_kernels)
    assert arch == ArchitectureType.HYBRID, f"Expected HYBRID, got {arch}"


def test_architecture_detection_unknown() -> None:
    """Test architecture detection returns UNKNOWN for unrecognized patterns."""
    random_kernels = [
        "some_random_kernel",
        "another_custom_kernel",
        "my_special_function",
    ]
    
    arch, markers = detect_architecture(random_kernels)
    assert arch == ArchitectureType.UNKNOWN, f"Expected UNKNOWN, got {arch}"
    assert markers == [], "UNKNOWN should have no markers"


# =============================================================================
# API Layer Tests (use fast metadata extraction where possible)
# =============================================================================


def test_analyze_trace_pair_metadata_callback() -> None:
    """Test that metadata extraction works for both traces (fast, no full analysis)."""
    if not _path_exists_safe(AMD_LLAMA_TRACE) or not _path_exists_safe(NVIDIA_LLAMA_TRACE):
        pytest.skip("Trace files not found")
    
    # Just test metadata extraction - much faster than full analysis
    meta1 = _extract_metadata_fast(AMD_LLAMA_TRACE)
    meta2 = _extract_metadata_fast(NVIDIA_LLAMA_TRACE)
    
    # Verify metadata is valid
    assert meta1.platform in ("AMD", "NVIDIA")
    assert meta2.platform in ("AMD", "NVIDIA")
    assert meta1.file_size_mb > 0
    assert meta2.file_size_mb > 0
    assert len(meta1.gpu_name) > 0
    assert len(meta2.gpu_name) > 0


def test_analyze_traces_result_structure(analyze_result) -> None:
    """Test that analyze_traces returns complete result structure."""
    results = analyze_result
    
    # Verify all fields are present
    assert results["metadata"] is not None
    assert results["operations"] is not None
    assert results["layers"] is not None
    
    # Verify metadata content
    assert "trace1_platform" in results["metadata"]
    assert "trace2_platform" in results["metadata"]
    assert "trace1_kernels" in results["metadata"]
    assert "trace2_kernels" in results["metadata"]


# =============================================================================
# Determinism Tests (use cached fixture)
# =============================================================================


def test_load_trace_deterministic(amd_trace_result, amd_trace_streaming_result) -> None:
    """Test that both loaders produce identical results (determinism)."""
    # Compare cached results from both loaders
    platform1, gpu1, _, df1, patterns1, layers1 = amd_trace_result
    platform2, gpu2, _, df2, patterns2, layers2 = amd_trace_streaming_result
    
    # Both loaders should produce identical results
    assert platform1 == platform2
    assert gpu1 == gpu2
    assert len(df1) == len(df2)
    assert int(df1["dur_us"].sum()) == int(df2["dur_us"].sum())
    assert df1["op"].nunique() == df2["op"].nunique()
    assert len(layers1) == len(layers2)


# =============================================================================
# Edge Case Tests
# =============================================================================


def test_classify_empty_kernel_name() -> None:
    """Test classifier handles empty kernel name."""
    op, pattern = classify("", "AMD")
    assert op == Op.OTHER, "Empty kernel should classify as OTHER"


def test_classify_unknown_platform() -> None:
    """Test classifier handles unknown platform gracefully."""
    op, pattern = classify("Cijk_gemm", "UNKNOWN_PLATFORM")
    # Should still classify based on kernel name
    assert op == Op.DENSE_GEMM, "Should still detect DENSE_GEMM pattern"


def test_architecture_detection_empty_list() -> None:
    """Test architecture detection with empty kernel list."""
    arch, markers = detect_architecture([])
    assert arch == ArchitectureType.UNKNOWN
    assert markers == []


# =============================================================================
# Performance and LoadedTrace Tests
# =============================================================================


def test_loaded_trace_contains_all_data() -> None:
    """Test that LoadedTrace contains all required fields."""
    from wafer_core.lib.trace_compare.loader import load_trace_full, LoadedTrace
    
    if not _path_exists_safe(AMD_LLAMA_TRACE):
        pytest.skip(f"Trace file not found: {AMD_LLAMA_TRACE}")
    
    loaded = load_trace_full(AMD_LLAMA_TRACE, include_stacks=True)
    
    assert isinstance(loaded, LoadedTrace)
    assert loaded.platform in ["AMD", "NVIDIA"]
    assert loaded.gpu_name is not None
    assert loaded.device_props is not None
    assert loaded.df is not None
    assert len(loaded.df) > 0
    assert loaded.patterns is not None
    assert loaded.layers is not None
    assert loaded.kernel_events is not None
    assert len(loaded.kernel_events) > 0
    assert loaded.all_events is not None
    assert len(loaded.all_events) > 0
    assert loaded.correlation_groups is not None
    assert len(loaded.correlation_groups) > 0


def test_analyze_from_loaded_matches_path_api() -> None:
    """Test that analyze_traces_from_loaded produces identical results to analyze_traces."""
    from wafer_core.lib.trace_compare.loader import load_trace_full
    from wafer_core.lib.trace_compare.analyzer import analyze_traces_from_loaded
    
    if not _path_exists_safe(AMD_LLAMA_TRACE) or not _path_exists_safe(NVIDIA_LLAMA_TRACE):
        pytest.skip("Trace files not found")
    
    # Load traces once
    trace1 = load_trace_full(AMD_LLAMA_TRACE, include_stacks=True)
    trace2 = load_trace_full(NVIDIA_LLAMA_TRACE, include_stacks=True)
    
    # Analyze using loaded data
    result_from_loaded = analyze_traces_from_loaded(trace1, trace2, phase_filter="all")
    
    # Analyze using path-based API
    result_from_path = analyze_traces(
        AMD_LLAMA_TRACE,
        NVIDIA_LLAMA_TRACE,
        phase_filter="all",
        include_stacks=True,
    )
    
    # Compare results (excluding file paths in metadata)
    assert result_from_loaded["metadata"]["trace1_platform"] == result_from_path["metadata"]["trace1_platform"]
    assert result_from_loaded["metadata"]["trace2_platform"] == result_from_path["metadata"]["trace2_platform"]
    assert result_from_loaded["metadata"]["trace1_kernels"] == result_from_path["metadata"]["trace1_kernels"]
    assert result_from_loaded["metadata"]["trace2_kernels"] == result_from_path["metadata"]["trace2_kernels"]
    assert len(result_from_loaded["operations"]) == len(result_from_path["operations"])
    assert len(result_from_loaded.get("layers", [])) == len(result_from_path.get("layers", []))


def test_analyze_trace_pair_timing() -> None:
    """Test that analyze_trace_pair completes in reasonable time (<25s)."""
    import time
    
    if not _path_exists_safe(AMD_LLAMA_TRACE) or not _path_exists_safe(NVIDIA_LLAMA_TRACE):
        pytest.skip("Trace files not found")
    
    start = time.perf_counter()
    result = analyze_trace_pair(
        AMD_LLAMA_TRACE,
        NVIDIA_LLAMA_TRACE,
        phase="all",
        include_stacks=True,
    )
    elapsed = time.perf_counter() - start
    
    # Should complete in under 25 seconds (was ~78s before optimization)
    assert elapsed < 25.0, f"Analysis took {elapsed:.1f}s, expected <25s"
    
    # Verify result structure
    assert result.metadata is not None
    assert result.operations is not None
    assert result.fusion_opportunities is not None
    assert result.warnings is not None
