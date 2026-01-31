"""Tests for Kernel Scope static analysis module.

Tests the full kernel scope analysis pipeline for AMDGCN ISA,
LLVM-IR, and TTGIR parsing and analysis.

Run with: PYTHONPATH=packages/wafer-core uv run pytest packages/wafer-core/tests/test_kernel_scope.py -v
"""

import pytest
from pathlib import Path
from dataclasses import FrozenInstanceError

from wafer_core.lib.kernel_scope.amdgcn.types import (
    ISAParseResult,
    KernelMetadata,
    InstructionInfo,
    InstructionCategory,
    InstructionMix,
    SpillInfo,
)
from wafer_core.lib.kernel_scope.amdgcn.parser import (
    parse_isa_file,
    parse_isa_text,
)
from wafer_core.lib.kernel_scope.amdgcn.analyzer import (
    analyze_isa,
    ISAAnalysis,
)
from wafer_core.lib.kernel_scope.amdgcn.instruction_db import (
    classify_instruction,
    is_packed_instruction,
    is_fma_instruction,
    is_full_stall,
    is_barrier,
    get_spill_type,
    extract_mnemonic,
)
from wafer_core.lib.kernel_scope.targets import get_target_specs, SUPPORTED_TARGETS
from wafer_core.lib.kernel_scope.targets.specs import TargetSpecs
from wafer_core.lib.kernel_scope.api import (
    analyze_isa_file,
    analyze_file,
    analyze_directory,
    AnalysisResult,
    BatchAnalysisResult,
)


# ============================================================================
# Sample AMDGCN ISA for testing
# ============================================================================

SAMPLE_ISA_TEXT = '''
.amdgcn_target "amdgcn-amd-amdhsa--gfx90a"

.text
.globl matmul_kernel
.p2align 8
.type matmul_kernel,@function

matmul_kernel:
    s_load_dwordx4 s[0:3], s[4:5], 0x0
    s_load_dwordx4 s[8:11], s[4:5], 0x10
    s_waitcnt lgkmcnt(0)
    
    ; Main compute loop
    global_load_dwordx4 v[0:3], v[4:5], off
    ds_read_b128 v[8:11], v12
    s_waitcnt vmcnt(0) lgkmcnt(0)
    
    ; MFMA operations
    v_mfma_f32_32x32x8f16 a[0:15], v[0:1], v[2:3], a[0:15]
    v_mfma_f32_32x32x8f16 a[16:31], v[4:5], v[6:7], a[16:31]
    
    ; Regular VALU
    v_add_f32 v0, v1, v2
    v_mul_f32 v3, v4, v5
    v_fma_f32 v6, v7, v8, v9
    v_pk_add_f16 v10, v11, v12
    
    ; Store results
    global_store_dwordx4 v[20:21], v[0:3], off
    s_barrier
    s_endpgm

.amdhsa_kernel matmul_kernel
    .amdhsa_next_free_vgpr 64
    .amdhsa_next_free_sgpr 32
    .amdhsa_group_segment_fixed_size 16384
    .amdhsa_private_segment_fixed_size 0
    .amdhsa_accum_offset 32
.end_amdhsa_kernel
'''

SAMPLE_ISA_WITH_SPILLS = '''
.amdgcn_target "amdgcn-amd-amdhsa--gfx942"

.text
.globl spilling_kernel

spilling_kernel:
    s_load_dwordx4 s[0:3], s[4:5], 0x0
    s_waitcnt lgkmcnt(0)
    
    ; Spill operations
    scratch_store_dwordx4 off, v[0:3], s0
    scratch_store_dwordx4 off, v[4:7], s0
    scratch_load_dwordx4 v[8:11], off, s0
    
    ; Some compute
    v_add_f32 v0, v1, v2
    s_waitcnt 0
    
    s_endpgm

.amdhsa_kernel spilling_kernel
    .amdhsa_next_free_vgpr 256
    .amdhsa_next_free_sgpr 100
    .amdhsa_group_segment_fixed_size 0
    .amdhsa_private_segment_fixed_size 1024
.end_amdhsa_kernel
'''

MULTI_KERNEL_ISA = '''
.amdgcn_target "amdgcn-amd-amdhsa--gfx90a"

.text

.amdhsa_kernel kernel_a
    .amdhsa_next_free_vgpr 32
    .amdhsa_next_free_sgpr 16
    .amdhsa_group_segment_fixed_size 4096
    .amdhsa_private_segment_fixed_size 0
.end_amdhsa_kernel

.amdhsa_kernel kernel_b
    .amdhsa_next_free_vgpr 128
    .amdhsa_next_free_sgpr 64
    .amdhsa_group_segment_fixed_size 32768
    .amdhsa_private_segment_fixed_size 512
.end_amdhsa_kernel
'''


# ============================================================================
# Instruction Classification Tests
# ============================================================================

class TestInstructionClassification:
    """Tests for instruction_db classification functions."""

    def test_classify_mfma_instructions(self) -> None:
        """MFMA instructions should be classified correctly."""
        assert classify_instruction("v_mfma_f32_32x32x8f16") == InstructionCategory.MFMA
        assert classify_instruction("v_mfma_f16_16x16x16f16") == InstructionCategory.MFMA
        assert classify_instruction("v_smfmac_f32_16x16x32_f16") == InstructionCategory.MFMA
        assert classify_instruction("V_MFMA_F32_4x4x4F16") == InstructionCategory.MFMA  # Case insensitive

    def test_classify_valu_instructions(self) -> None:
        """Vector ALU instructions should be classified correctly."""
        assert classify_instruction("v_add_f32") == InstructionCategory.VALU
        assert classify_instruction("v_mul_f32") == InstructionCategory.VALU
        assert classify_instruction("v_fma_f32") == InstructionCategory.VALU
        assert classify_instruction("v_pk_add_f16") == InstructionCategory.VALU

    def test_classify_salu_instructions(self) -> None:
        """Scalar ALU instructions should be classified correctly."""
        assert classify_instruction("s_add_i32") == InstructionCategory.SALU
        assert classify_instruction("s_mul_i32") == InstructionCategory.SALU
        assert classify_instruction("s_and_b64") == InstructionCategory.SALU

    def test_classify_vmem_instructions(self) -> None:
        """Vector memory instructions should be classified correctly."""
        assert classify_instruction("global_load_dwordx4") == InstructionCategory.VMEM
        assert classify_instruction("global_store_dword") == InstructionCategory.VMEM
        assert classify_instruction("buffer_load_dword") == InstructionCategory.VMEM
        assert classify_instruction("flat_load_dwordx2") == InstructionCategory.VMEM

    def test_classify_smem_instructions(self) -> None:
        """Scalar memory instructions should be classified correctly."""
        assert classify_instruction("s_load_dwordx4") == InstructionCategory.SMEM
        assert classify_instruction("s_buffer_load_dword") == InstructionCategory.SMEM

    def test_classify_lds_instructions(self) -> None:
        """LDS instructions should be classified correctly."""
        assert classify_instruction("ds_read_b32") == InstructionCategory.LDS
        assert classify_instruction("ds_write_b64") == InstructionCategory.LDS
        assert classify_instruction("ds_bpermute_b32") == InstructionCategory.LDS

    def test_classify_spill_instructions(self) -> None:
        """Spill instructions should be classified correctly."""
        assert classify_instruction("scratch_store_dwordx4") == InstructionCategory.SPILL
        assert classify_instruction("scratch_load_dword") == InstructionCategory.SPILL

    def test_classify_sync_instructions(self) -> None:
        """Sync instructions should be classified correctly."""
        assert classify_instruction("s_barrier") == InstructionCategory.SYNC
        assert classify_instruction("s_waitcnt") == InstructionCategory.SYNC
        assert classify_instruction("s_wait_loadcnt") == InstructionCategory.SYNC

    def test_classify_control_instructions(self) -> None:
        """Control flow instructions should be classified correctly."""
        assert classify_instruction("s_branch") == InstructionCategory.CONTROL
        assert classify_instruction("s_cbranch_scc0") == InstructionCategory.CONTROL
        assert classify_instruction("s_endpgm") == InstructionCategory.CONTROL

    def test_is_packed_instruction(self) -> None:
        """Packed instructions should be identified correctly."""
        assert is_packed_instruction("v_pk_add_f16")
        assert is_packed_instruction("v_pk_mul_f16")
        assert is_packed_instruction("v_pk_fma_f16")
        assert not is_packed_instruction("v_add_f32")
        assert not is_packed_instruction("v_mfma_f32_32x32x8f16")

    def test_is_fma_instruction(self) -> None:
        """FMA instructions should be identified correctly."""
        assert is_fma_instruction("v_fma_f32")
        assert is_fma_instruction("v_fmac_f32")
        assert is_fma_instruction("v_fmaak_f32")
        assert is_fma_instruction("v_pk_fma_f16")
        assert not is_fma_instruction("v_mul_f32")
        assert not is_fma_instruction("v_add_f32")

    def test_is_full_stall(self) -> None:
        """Full stall detection should work correctly."""
        assert is_full_stall("s_waitcnt 0")
        assert is_full_stall("s_waitcnt vmcnt(0) lgkmcnt(0)")
        assert is_full_stall("  s_waitcnt 0  ; comment")
        assert not is_full_stall("s_waitcnt vmcnt(0)")
        assert not is_full_stall("s_waitcnt lgkmcnt(0)")

    def test_is_barrier(self) -> None:
        """Barrier detection should work correctly."""
        assert is_barrier("s_barrier")
        assert is_barrier("S_BARRIER")  # Case insensitive
        assert not is_barrier("s_waitcnt")
        assert not is_barrier("s_barrier_scc")  # Doesn't exist but tests prefix

    def test_get_spill_type(self) -> None:
        """Spill type detection should work correctly."""
        assert get_spill_type("scratch_store_dwordx4") == "store"
        assert get_spill_type("scratch_store_dword") == "store"
        assert get_spill_type("scratch_load_dwordx4") == "load"
        assert get_spill_type("scratch_load_dword") == "load"
        assert get_spill_type("global_store_dword") is None
        assert get_spill_type("v_add_f32") is None

    def test_extract_mnemonic(self) -> None:
        """Mnemonic extraction should work correctly."""
        assert extract_mnemonic("  v_add_f32 v0, v1, v2") == "v_add_f32"
        assert extract_mnemonic("v_mfma_f32_32x32x8f16 a[0:15], v[0:1], v[2:3], a[0:15]") == "v_mfma_f32_32x32x8f16"
        assert extract_mnemonic("  s_endpgm  ; end") == "s_endpgm"
        assert extract_mnemonic("") is None
        assert extract_mnemonic("  ; comment only") is None
        assert extract_mnemonic(".amdhsa_kernel foo") is None
        assert extract_mnemonic(".L_label:") is None


# ============================================================================
# Parser Tests
# ============================================================================

class TestISAParser:
    """Tests for AMDGCN ISA parser."""

    def test_parse_empty_text_fails(self) -> None:
        """Parsing empty text should fail."""
        result = parse_isa_text("")
        assert not result.success
        assert "Empty input" in result.error

    def test_parse_non_isa_text_fails(self) -> None:
        """Parsing non-ISA text should fail."""
        result = parse_isa_text("def python_function():\n    pass")
        assert not result.success
        assert "not appear to be AMDGCN" in result.error

    def test_parse_valid_isa(self) -> None:
        """Parsing valid ISA should succeed."""
        result = parse_isa_text(SAMPLE_ISA_TEXT)
        
        assert result.success
        assert result.error is None
        assert len(result.kernels) == 1
        
        kernel = result.kernels[0]
        assert kernel.kernel_name == "matmul_kernel"
        assert kernel.architecture == "gfx90a"
        assert kernel.vgpr_count == 64
        assert kernel.sgpr_count == 32
        assert kernel.lds_size == 16384
        assert kernel.scratch_size == 0

    def test_parse_extracts_architecture(self) -> None:
        """Parser should extract architecture from target directive."""
        result = parse_isa_text(SAMPLE_ISA_TEXT)
        assert result.success
        assert result.kernels[0].architecture == "gfx90a"

    def test_parse_multiple_kernels(self) -> None:
        """Parser should handle multiple kernels in one file."""
        result = parse_isa_text(MULTI_KERNEL_ISA)
        
        assert result.success
        assert len(result.kernels) == 2
        
        kernel_a = result.kernels[0]
        assert kernel_a.kernel_name == "kernel_a"
        assert kernel_a.vgpr_count == 32
        assert kernel_a.sgpr_count == 16
        
        kernel_b = result.kernels[1]
        assert kernel_b.kernel_name == "kernel_b"
        assert kernel_b.vgpr_count == 128
        assert kernel_b.sgpr_count == 64

    def test_parse_detects_spill_allocations(self) -> None:
        """Parser should detect scratch allocation."""
        result = parse_isa_text(SAMPLE_ISA_WITH_SPILLS)
        
        assert result.success
        kernel = result.kernels[0]
        assert kernel.scratch_size == 1024

    def test_parse_extracts_instructions(self) -> None:
        """Parser should extract instructions."""
        result = parse_isa_text(SAMPLE_ISA_TEXT)
        
        assert result.success
        assert len(result.instructions) > 0
        
        # Find MFMA instructions
        mfma_instrs = [i for i in result.instructions if i.category == InstructionCategory.MFMA]
        assert len(mfma_instrs) == 2

    def test_parse_file_not_found(self, tmp_path: Path) -> None:
        """Parsing non-existent file should fail gracefully."""
        result = parse_isa_file(tmp_path / "nonexistent.s")
        
        assert not result.success
        assert "not found" in result.error

    def test_parse_file_success(self, tmp_path: Path) -> None:
        """Parsing file should work."""
        isa_file = tmp_path / "kernel.s"
        isa_file.write_text(SAMPLE_ISA_TEXT)
        
        result = parse_isa_file(isa_file)
        
        assert result.success
        assert result.file_path == str(isa_file)
        assert len(result.kernels) == 1


# ============================================================================
# Analyzer Tests
# ============================================================================

class TestISAAnalyzer:
    """Tests for AMDGCN ISA analyzer."""

    def test_analyze_requires_successful_parse(self) -> None:
        """Analyzer should require successful parse result."""
        failed_parse = ISAParseResult(success=False, error="Test error")
        
        with pytest.raises(ValueError, match="Cannot analyze failed parse"):
            analyze_isa(failed_parse)

    def test_analyze_requires_kernels(self) -> None:
        """Analyzer should require at least one kernel."""
        empty_parse = ISAParseResult(success=True, kernels=())
        
        with pytest.raises(ValueError, match="No kernels found"):
            analyze_isa(empty_parse)

    def test_analyze_basic_metrics(self) -> None:
        """Analyzer should compute basic metrics."""
        parse_result = parse_isa_text(SAMPLE_ISA_TEXT)
        analysis = analyze_isa(parse_result)
        
        assert analysis.kernel_name == "matmul_kernel"
        assert analysis.architecture == "gfx90a"
        assert analysis.vgpr_count == 64
        assert analysis.sgpr_count == 32
        assert analysis.lds_size == 16384
        assert analysis.scratch_size == 0

    def test_analyze_mfma_count(self) -> None:
        """Analyzer should count MFMA instructions."""
        parse_result = parse_isa_text(SAMPLE_ISA_TEXT)
        analysis = analyze_isa(parse_result)
        
        assert analysis.mfma_count == 2

    def test_analyze_mfma_density(self) -> None:
        """Analyzer should compute MFMA density."""
        parse_result = parse_isa_text(SAMPLE_ISA_TEXT)
        analysis = analyze_isa(parse_result)
        
        # MFMA density = MFMA / total compute ops
        assert analysis.mfma_density_pct > 0

    def test_analyze_spill_detection(self) -> None:
        """Analyzer should detect spills."""
        parse_result = parse_isa_text(SAMPLE_ISA_WITH_SPILLS)
        analysis = analyze_isa(parse_result)
        
        assert analysis.spill_count == 3  # 2 stores + 1 load
        assert analysis.vgpr_spill_count == 3
        assert analysis.scratch_size == 1024

    def test_analyze_instruction_mix(self) -> None:
        """Analyzer should compute instruction mix."""
        parse_result = parse_isa_text(SAMPLE_ISA_TEXT)
        analysis = analyze_isa(parse_result)
        
        mix = analysis.instruction_mix
        assert mix.mfma_count == 2
        assert mix.valu_count > 0
        assert mix.total_count > 0

    def test_analyze_occupancy_limits(self) -> None:
        """Analyzer should compute occupancy limits."""
        parse_result = parse_isa_text(SAMPLE_ISA_TEXT)
        analysis = analyze_isa(parse_result)
        
        assert analysis.max_waves_vgpr > 0
        assert analysis.max_waves_sgpr > 0
        assert analysis.max_waves_lds > 0
        assert analysis.theoretical_occupancy > 0
        assert analysis.theoretical_occupancy <= 10  # Max for MI200

    def test_analyze_generates_spill_warning(self) -> None:
        """Analyzer should generate warnings for spills."""
        parse_result = parse_isa_text(SAMPLE_ISA_WITH_SPILLS)
        analysis = analyze_isa(parse_result)
        
        assert any("CRITICAL" in w and "spill" in w.lower() for w in analysis.warnings)

    def test_analyze_generates_scratch_warning(self) -> None:
        """Analyzer should warn about non-zero scratch allocation."""
        parse_result = parse_isa_text(SAMPLE_ISA_WITH_SPILLS)
        analysis = analyze_isa(parse_result)
        
        assert any("scratch" in w.lower() for w in analysis.warnings)

    def test_analyze_full_stall_detection(self) -> None:
        """Analyzer should detect full stalls."""
        parse_result = parse_isa_text(SAMPLE_ISA_WITH_SPILLS)
        analysis = analyze_isa(parse_result)
        
        assert analysis.full_stall_count == 1  # s_waitcnt 0

    def test_analyze_barrier_count(self) -> None:
        """Analyzer should count barriers."""
        parse_result = parse_isa_text(SAMPLE_ISA_TEXT)
        analysis = analyze_isa(parse_result)
        
        assert analysis.barrier_count == 1

    def test_analyze_kernel_index(self) -> None:
        """Analyzer should support kernel index selection."""
        parse_result = parse_isa_text(MULTI_KERNEL_ISA)
        
        analysis_a = analyze_isa(parse_result, kernel_index=0)
        assert analysis_a.kernel_name == "kernel_a"
        
        analysis_b = analyze_isa(parse_result, kernel_index=1)
        assert analysis_b.kernel_name == "kernel_b"

    def test_analyze_invalid_kernel_index(self) -> None:
        """Analyzer should reject invalid kernel index."""
        parse_result = parse_isa_text(SAMPLE_ISA_TEXT)
        
        with pytest.raises(ValueError, match="out of range"):
            analyze_isa(parse_result, kernel_index=5)


# ============================================================================
# Target Specs Tests
# ============================================================================

class TestTargetSpecs:
    """Tests for GPU target specifications."""

    def test_supported_targets(self) -> None:
        """All supported targets should be in the list."""
        assert "gfx90a" in SUPPORTED_TARGETS
        assert "gfx942" in SUPPORTED_TARGETS
        assert "gfx908" in SUPPORTED_TARGETS

    def test_get_known_target(self) -> None:
        """Getting known target should return correct specs."""
        specs = get_target_specs("gfx90a")
        
        assert specs.name == "gfx90a"
        assert specs.series == "MI200"
        assert specs.vgprs_per_cu == 512
        assert specs.sgprs_per_cu == 800
        assert specs.lds_per_cu == 65536
        assert specs.max_waves_per_cu == 10

    def test_get_unknown_target(self) -> None:
        """Getting unknown target should return default specs."""
        specs = get_target_specs("gfx_unknown")
        
        assert specs.name == "unknown"
        assert specs.vgprs_per_cu > 0  # Should have sensible defaults

    def test_case_insensitive_lookup(self) -> None:
        """Target lookup should be case insensitive."""
        specs_lower = get_target_specs("gfx90a")
        specs_upper = get_target_specs("GFX90A")
        
        assert specs_lower.name == specs_upper.name

    def test_extract_from_longer_string(self) -> None:
        """Target lookup should extract gfx* from longer strings."""
        specs = get_target_specs("amdgcn-amd-amdhsa--gfx90a")
        
        assert specs.name == "gfx90a"

    def test_specs_are_frozen(self) -> None:
        """TargetSpecs should be immutable."""
        specs = get_target_specs("gfx90a")
        
        with pytest.raises(FrozenInstanceError):
            specs.vgprs_per_cu = 1024  # type: ignore


# ============================================================================
# High-Level API Tests
# ============================================================================

class TestHighLevelAPI:
    """Tests for the high-level kernel scope API."""

    def test_analyze_isa_file_success(self, tmp_path: Path) -> None:
        """analyze_isa_file should work for valid files."""
        isa_file = tmp_path / "kernel.s"
        isa_file.write_text(SAMPLE_ISA_TEXT)
        
        result = analyze_isa_file(isa_file)
        
        assert result.success
        assert result.file_type == "isa"
        assert result.isa_analysis is not None
        assert result.isa_analysis.kernel_name == "matmul_kernel"

    def test_analyze_isa_file_not_found(self, tmp_path: Path) -> None:
        """analyze_isa_file should handle missing files."""
        result = analyze_isa_file(tmp_path / "missing.s")
        
        assert not result.success
        assert "not found" in result.error

    def test_analyze_file_auto_detect_isa(self, tmp_path: Path) -> None:
        """analyze_file should auto-detect ISA files."""
        for ext in [".s", ".gcn", ".asm"]:
            isa_file = tmp_path / f"kernel{ext}"
            isa_file.write_text(SAMPLE_ISA_TEXT)
            
            result = analyze_file(isa_file)
            
            assert result.file_type == "isa", f"Failed for extension {ext}"

    def test_analyze_file_unsupported_extension(self, tmp_path: Path) -> None:
        """analyze_file should reject unsupported extensions."""
        bad_file = tmp_path / "file.xyz"
        bad_file.write_text("content")
        
        result = analyze_file(bad_file)
        
        assert not result.success
        assert "Unsupported" in result.error

    def test_analyze_directory_finds_files(self, tmp_path: Path) -> None:
        """analyze_directory should find and analyze ISA files."""
        # Create test files
        (tmp_path / "kernel1.s").write_text(SAMPLE_ISA_TEXT)
        (tmp_path / "kernel2.s").write_text(SAMPLE_ISA_WITH_SPILLS)
        
        result = analyze_directory(tmp_path)
        
        assert result.total_files == 2
        assert result.successful >= 1

    def test_analyze_directory_recursive(self, tmp_path: Path) -> None:
        """analyze_directory should scan recursively."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "kernel.s").write_text(SAMPLE_ISA_TEXT)
        
        result = analyze_directory(tmp_path, recursive=True)
        
        assert result.total_files >= 1

    def test_analyze_directory_empty(self, tmp_path: Path) -> None:
        """analyze_directory should handle empty directories."""
        result = analyze_directory(tmp_path)
        
        assert result.total_files == 0
        assert result.successful == 0

    def test_analysis_result_to_json(self, tmp_path: Path) -> None:
        """AnalysisResult should serialize to JSON."""
        isa_file = tmp_path / "kernel.s"
        isa_file.write_text(SAMPLE_ISA_TEXT)
        
        result = analyze_isa_file(isa_file)
        json_str = result.to_json()
        
        import json
        data = json.loads(json_str)
        
        assert data["success"] is True
        assert data["file_type"] == "isa"
        assert "isa_analysis" in data
        assert data["isa_analysis"]["kernel_name"] == "matmul_kernel"

    def test_batch_result_summary(self, tmp_path: Path) -> None:
        """BatchAnalysisResult should compute summary stats."""
        (tmp_path / "kernel1.s").write_text(SAMPLE_ISA_TEXT)
        (tmp_path / "kernel2.s").write_text(SAMPLE_ISA_WITH_SPILLS)
        
        result = analyze_directory(tmp_path)
        
        assert "total_vgpr_avg" in result.summary
        assert "total_spills" in result.summary
        assert "files_with_spills" in result.summary


# ============================================================================
# Data Structure Tests
# ============================================================================

class TestDataStructures:
    """Tests for frozen dataclasses."""

    def test_isa_analysis_is_frozen(self) -> None:
        """ISAAnalysis should be immutable."""
        analysis = ISAAnalysis(
            kernel_name="test",
            architecture="gfx90a",
            vgpr_count=64,
            sgpr_count=32,
        )
        
        with pytest.raises(FrozenInstanceError):
            analysis.vgpr_count = 128  # type: ignore

    def test_kernel_metadata_is_frozen(self) -> None:
        """KernelMetadata should be immutable."""
        metadata = KernelMetadata(
            kernel_name="test",
            architecture="gfx90a",
            vgpr_count=64,
            sgpr_count=32,
        )
        
        with pytest.raises(FrozenInstanceError):
            metadata.kernel_name = "modified"  # type: ignore

    def test_instruction_mix_total_count(self) -> None:
        """InstructionMix should compute total correctly."""
        mix = InstructionMix(
            valu_count=10,
            salu_count=5,
            vmem_count=3,
            smem_count=2,
            lds_count=4,
            mfma_count=2,
            control_count=1,
            sync_count=2,
            spill_count=0,
            other_count=1,
        )
        
        assert mix.total_count == 30

    def test_instruction_mix_compute_count(self) -> None:
        """InstructionMix should compute compute_count correctly."""
        mix = InstructionMix(
            valu_count=10,
            salu_count=5,
            mfma_count=2,
        )
        
        # Compute = VALU + MFMA (SALU is not counted as "compute" in GPU terminology)
        assert mix.compute_count == 12  # 10 VALU + 2 MFMA


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_parse_isa_with_only_directives(self) -> None:
        """Parser should handle files with only directives."""
        text = '''
.amdgcn_target "amdgcn-amd-amdhsa--gfx90a"

.amdhsa_kernel empty_kernel
    .amdhsa_next_free_vgpr 32
    .amdhsa_next_free_sgpr 16
.end_amdhsa_kernel
'''
        result = parse_isa_text(text)
        
        assert result.success
        assert len(result.kernels) == 1
        assert len(result.instructions) == 0  # No instructions

    def test_occupancy_with_high_vgpr(self) -> None:
        """Occupancy should decrease with high VGPR usage."""
        text = '''
.amdgcn_target "amdgcn-amd-amdhsa--gfx90a"

.amdhsa_kernel high_vgpr_kernel
    .amdhsa_next_free_vgpr 256
    .amdhsa_next_free_sgpr 32
    .amdhsa_group_segment_fixed_size 0
.end_amdhsa_kernel
'''
        parse_result = parse_isa_text(text)
        analysis = analyze_isa(parse_result)
        
        # With 256 VGPRs per wave, should get max 2 waves (512/256=2)
        assert analysis.max_waves_vgpr == 2

    def test_occupancy_with_high_lds(self) -> None:
        """Occupancy should decrease with high LDS usage."""
        text = '''
.amdgcn_target "amdgcn-amd-amdhsa--gfx90a"

.amdhsa_kernel high_lds_kernel
    .amdhsa_next_free_vgpr 32
    .amdhsa_next_free_sgpr 32
    .amdhsa_group_segment_fixed_size 65536
.end_amdhsa_kernel
'''
        parse_result = parse_isa_text(text)
        analysis = analyze_isa(parse_result)
        
        # With full 64KB LDS, only 1 workgroup can fit
        assert analysis.max_waves_lds == 1

    def test_instruction_with_complex_operands(self) -> None:
        """Parser should handle complex operand formats."""
        text = '''
.amdgcn_target "amdgcn-amd-amdhsa--gfx90a"

.text
test_kernel:
    v_mfma_f32_32x32x8f16 a[0:15], v[0:1], v[2:3], a[0:15] cbsz:1 abid:2 blgp:3
    global_load_dwordx4 v[0:3], v[4:5], off offset:256
    s_endpgm

.amdhsa_kernel test_kernel
    .amdhsa_next_free_vgpr 32
    .amdhsa_next_free_sgpr 16
.end_amdhsa_kernel
'''
        result = parse_isa_text(text)
        
        assert result.success
        mfma_instrs = [i for i in result.instructions if i.category == InstructionCategory.MFMA]
        assert len(mfma_instrs) == 1


# ============================================================================
# Code Object Analysis Tests
# ============================================================================


class TestCodeObjectAnalysis:
    """Tests for code object (.co) file analysis via API."""

    def test_code_object_analysis_requires_api_params(self) -> None:
        """analyze_file should require API params for .co files."""
        from wafer_core.lib.kernel_scope.api import analyze_file

        # Without API params, should return error for .co files
        result = analyze_file("test.co")
        assert not result.success
        assert result.error is not None
        assert "API" in result.error or "auth" in result.error.lower()

    def test_code_object_analysis_result_structure(self) -> None:
        """CodeObjectAnalysis should have correct structure."""
        from wafer_core.lib.kernel_scope.api import CodeObjectAnalysis

        # Create a sample result
        result = CodeObjectAnalysis(
            kernel_name="test_kernel",
            architecture="gfx942",
            vgpr_count=64,
            sgpr_count=32,
            agpr_count=16,
            vgpr_spill_count=0,
            sgpr_spill_count=0,
            lds_bytes=16384,
            global_loads=10,
            global_stores=5,
            lds_ops=20,
            mfma_count=8,
            fma_count=4,
            packed_ops_count=2,
            waitcnt_full_stalls=1,
            barriers=2,
            isa_text="...",
            metadata_yaml="...",
            annotated_isa_text="...",
        )

        assert result.kernel_name == "test_kernel"
        assert result.architecture == "gfx942"
        assert result.vgpr_count == 64
        assert result.sgpr_count == 32
        assert result.mfma_count == 8
        assert result.lds_bytes == 16384

    def test_analysis_result_code_object_field(self) -> None:
        """AnalysisResult should support code_object_analysis field."""
        from wafer_core.lib.kernel_scope.api import AnalysisResult, CodeObjectAnalysis

        code_obj = CodeObjectAnalysis(
            kernel_name="test",
            architecture="gfx90a",
            vgpr_count=32,
            sgpr_count=16,
            agpr_count=0,
            vgpr_spill_count=0,
            sgpr_spill_count=0,
            lds_bytes=0,
            global_loads=0,
            global_stores=0,
            lds_ops=0,
            mfma_count=0,
            fma_count=0,
            packed_ops_count=0,
            waitcnt_full_stalls=0,
            barriers=0,
            isa_text="",
            metadata_yaml="",
            annotated_isa_text="",
        )

        result = AnalysisResult(
            success=True,
            file_path="test.co",
            file_type="code_object",
            code_object_analysis=code_obj,
        )

        assert result.success
        assert result.file_type == "code_object"
        assert result.code_object_analysis is not None
        assert result.code_object_analysis.kernel_name == "test"

    def test_analysis_result_to_dict_with_code_object(self) -> None:
        """to_dict should include code_object_analysis."""
        from wafer_core.lib.kernel_scope.api import AnalysisResult, CodeObjectAnalysis

        code_obj = CodeObjectAnalysis(
            kernel_name="matmul",
            architecture="gfx942",
            vgpr_count=128,
            sgpr_count=64,
            agpr_count=32,
            vgpr_spill_count=2,
            sgpr_spill_count=1,
            lds_bytes=32768,
            global_loads=20,
            global_stores=10,
            lds_ops=40,
            mfma_count=16,
            fma_count=8,
            packed_ops_count=4,
            waitcnt_full_stalls=2,
            barriers=4,
            isa_text="isa...",
            metadata_yaml="yaml...",
            annotated_isa_text="annotated...",
        )

        result = AnalysisResult(
            success=True,
            file_path="/path/to/kernel.co",
            file_type="code_object",
            code_object_analysis=code_obj,
        )

        d = result.to_dict()

        assert d["success"] is True
        assert d["file_path"] == "/path/to/kernel.co"
        assert d["file_type"] == "code_object"
        assert "code_object_analysis" in d
        assert d["code_object_analysis"]["kernel_name"] == "matmul"
        assert d["code_object_analysis"]["vgpr_count"] == 128
        assert d["code_object_analysis"]["mfma_count"] == 16
        assert d["code_object_analysis"]["vgpr_spill_count"] == 2

    def test_format_code_object_summary(self) -> None:
        """format_code_object_summary should produce readable output."""
        from wafer_core.lib.kernel_scope.api import CodeObjectAnalysis, format_code_object_summary

        code_obj = CodeObjectAnalysis(
            kernel_name="gemm_kernel",
            architecture="gfx90a",
            vgpr_count=96,
            sgpr_count=48,
            agpr_count=16,
            vgpr_spill_count=0,
            sgpr_spill_count=0,
            lds_bytes=8192,
            global_loads=15,
            global_stores=5,
            lds_ops=30,
            mfma_count=12,
            fma_count=6,
            packed_ops_count=3,
            waitcnt_full_stalls=2,
            barriers=3,
            isa_text="...",
            metadata_yaml="...",
            annotated_isa_text="...",
        )

        summary = format_code_object_summary(code_obj)

        assert "gemm_kernel" in summary
        assert "gfx90a" in summary
        assert "96" in summary  # VGPR count
        assert "12" in summary  # MFMA count
        assert "None (good)" in summary  # No spills

    def test_format_code_object_summary_with_spills(self) -> None:
        """format_code_object_summary should warn about spills."""
        from wafer_core.lib.kernel_scope.api import CodeObjectAnalysis, format_code_object_summary

        code_obj = CodeObjectAnalysis(
            kernel_name="spilling_kernel",
            architecture="gfx942",
            vgpr_count=256,
            sgpr_count=128,
            agpr_count=0,
            vgpr_spill_count=5,
            sgpr_spill_count=2,
            lds_bytes=0,
            global_loads=0,
            global_stores=0,
            lds_ops=0,
            mfma_count=0,
            fma_count=0,
            packed_ops_count=0,
            waitcnt_full_stalls=0,
            barriers=0,
            isa_text="...",
            metadata_yaml="...",
            annotated_isa_text="...",
        )

        summary = format_code_object_summary(code_obj)

        assert "SPILLS DETECTED" in summary
        assert "VGPR spills: 5" in summary
        assert "SGPR spills: 2" in summary


class TestUnifiedAnalyzeFile:
    """Tests for unified analyze_file API supporting both .co and .s files."""

    def test_analyze_file_detects_isa_extension(self) -> None:
        """analyze_file should detect .s files as ISA type."""
        from wafer_core.lib.kernel_scope.api import analyze_file
        import tempfile
        import os

        # Create temp ISA file
        isa_content = SAMPLE_ISA_TEXT
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.s', delete=False) as f:
            f.write(isa_content)
            temp_path = f.name

        try:
            result = analyze_file(temp_path)
            assert result.success
            assert result.file_type == "isa"
            assert result.isa_analysis is not None
        finally:
            os.unlink(temp_path)

    def test_analyze_file_detects_co_extension(self) -> None:
        """analyze_file should detect .co files as code_object type."""
        from wafer_core.lib.kernel_scope.api import analyze_file

        # Without API params, .co files should error
        result = analyze_file("nonexistent.co")
        assert not result.success
        assert result.file_type == "code_object"

    def test_analyze_file_rejects_unknown_extension(self) -> None:
        """analyze_file should reject unknown file extensions."""
        from wafer_core.lib.kernel_scope.api import analyze_file

        result = analyze_file("test.xyz")
        assert not result.success
        assert "Unsupported" in result.error


# ============================================================================
# Code Object API Tests (with mocked httpx)
# ============================================================================


class TestCodeObjectAPIIntegration:
    """Tests for .co file analysis via API with mocked responses."""

    def test_analyze_code_object_success(self, tmp_path: Path) -> None:
        """analyze_code_object should return result on successful API call."""
        from unittest.mock import patch, MagicMock
        from wafer_core.lib.kernel_scope.api import analyze_code_object

        # Create fake .co file
        co_file = tmp_path / "kernel.co"
        co_file.write_bytes(b"fake code object content")

        # Mock API response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "kernel_name": "test_matmul",
            "architecture": "gfx942",
            "vgpr_count": 64,
            "sgpr_count": 32,
            "agpr_count": 16,
            "vgpr_spill_count": 0,
            "sgpr_spill_count": 0,
            "lds_bytes": 16384,
            "global_loads": 10,
            "global_stores": 5,
            "lds_ops": 20,
            "mfma_count": 8,
            "fma_count": 4,
            "packed_ops_count": 2,
            "waitcnt_full_stalls": 1,
            "barriers": 2,
            "isa_text": "test isa",
            "metadata_yaml": "test yaml",
            "annotated_isa_text": "annotated",
        }

        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.post.return_value = mock_response
            mock_client_class.return_value = mock_client

            result = analyze_code_object(
                co_file,
                api_url="https://api.test.com",
                auth_headers={"Authorization": "Bearer test"},
            )

        assert result.success
        assert result.file_type == "code_object"
        assert result.code_object_analysis is not None
        assert result.code_object_analysis.kernel_name == "test_matmul"
        assert result.code_object_analysis.architecture == "gfx942"
        assert result.code_object_analysis.vgpr_count == 64
        assert result.code_object_analysis.mfma_count == 8

    def test_analyze_code_object_file_not_found(self, tmp_path: Path) -> None:
        """analyze_code_object should return error for missing file."""
        from wafer_core.lib.kernel_scope.api import analyze_code_object

        result = analyze_code_object(
            tmp_path / "nonexistent.co",
            api_url="https://api.test.com",
            auth_headers={"Authorization": "Bearer test"},
        )

        assert not result.success
        assert "not found" in result.error.lower()

    def test_analyze_code_object_wrong_extension(self, tmp_path: Path) -> None:
        """analyze_code_object should return error for non-.co file."""
        from wafer_core.lib.kernel_scope.api import analyze_code_object

        wrong_ext = tmp_path / "kernel.txt"
        wrong_ext.write_bytes(b"not a code object")

        result = analyze_code_object(
            wrong_ext,
            api_url="https://api.test.com",
            auth_headers={"Authorization": "Bearer test"},
        )

        assert not result.success
        assert ".co" in result.error

    def test_analyze_code_object_api_error(self, tmp_path: Path) -> None:
        """analyze_code_object should handle API errors gracefully."""
        from unittest.mock import patch, MagicMock
        import httpx
        from wafer_core.lib.kernel_scope.api import analyze_code_object

        co_file = tmp_path / "kernel.co"
        co_file.write_bytes(b"fake code object")

        # Mock API error response
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal server error"

        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.post.side_effect = httpx.HTTPStatusError(
                "Server error",
                request=MagicMock(),
                response=mock_response,
            )
            mock_client_class.return_value = mock_client

            result = analyze_code_object(
                co_file,
                api_url="https://api.test.com",
                auth_headers={"Authorization": "Bearer test"},
            )

        assert not result.success
        assert "API error" in result.error or "500" in result.error

    def test_analyze_code_object_network_error(self, tmp_path: Path) -> None:
        """analyze_code_object should handle network errors gracefully."""
        from unittest.mock import patch, MagicMock
        import httpx
        from wafer_core.lib.kernel_scope.api import analyze_code_object

        co_file = tmp_path / "kernel.co"
        co_file.write_bytes(b"fake code object")

        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.post.side_effect = httpx.RequestError("Connection refused")
            mock_client_class.return_value = mock_client

            result = analyze_code_object(
                co_file,
                api_url="https://api.test.com",
                auth_headers={"Authorization": "Bearer test"},
            )

        assert not result.success
        assert "Request failed" in result.error or "Connection" in result.error

    def test_analyze_code_object_with_spills(self, tmp_path: Path) -> None:
        """analyze_code_object should correctly report spills."""
        from unittest.mock import patch, MagicMock
        from wafer_core.lib.kernel_scope.api import analyze_code_object

        co_file = tmp_path / "kernel.co"
        co_file.write_bytes(b"fake code object")

        # Mock API response with spills
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "kernel_name": "spilling_kernel",
            "architecture": "gfx90a",
            "vgpr_count": 256,
            "sgpr_count": 128,
            "agpr_count": 0,
            "vgpr_spill_count": 10,
            "sgpr_spill_count": 5,
            "lds_bytes": 0,
            "global_loads": 0,
            "global_stores": 0,
            "lds_ops": 0,
            "mfma_count": 0,
            "fma_count": 0,
            "packed_ops_count": 0,
            "waitcnt_full_stalls": 0,
            "barriers": 0,
            "isa_text": "",
            "metadata_yaml": "",
            "annotated_isa_text": "",
        }

        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.post.return_value = mock_response
            mock_client_class.return_value = mock_client

            result = analyze_code_object(
                co_file,
                api_url="https://api.test.com",
                auth_headers={"Authorization": "Bearer test"},
            )

        assert result.success
        assert result.code_object_analysis.vgpr_spill_count == 10
        assert result.code_object_analysis.sgpr_spill_count == 5

    def test_analyze_file_with_co_and_api_params(self, tmp_path: Path) -> None:
        """analyze_file should work for .co files when API params provided."""
        from unittest.mock import patch, MagicMock
        from wafer_core.lib.kernel_scope.api import analyze_file

        co_file = tmp_path / "kernel.co"
        co_file.write_bytes(b"fake code object")

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "kernel_name": "unified_test",
            "architecture": "gfx942",
            "vgpr_count": 48,
            "sgpr_count": 24,
            "agpr_count": 8,
            "vgpr_spill_count": 0,
            "sgpr_spill_count": 0,
            "lds_bytes": 8192,
            "global_loads": 5,
            "global_stores": 3,
            "lds_ops": 10,
            "mfma_count": 4,
            "fma_count": 2,
            "packed_ops_count": 1,
            "waitcnt_full_stalls": 0,
            "barriers": 1,
            "isa_text": "isa",
            "metadata_yaml": "yaml",
            "annotated_isa_text": "annotated",
        }

        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.post.return_value = mock_response
            mock_client_class.return_value = mock_client

            result = analyze_file(
                str(co_file),
                api_url="https://api.test.com",
                auth_headers={"Authorization": "Bearer test"},
            )

        assert result.success
        assert result.file_type == "code_object"
        assert result.code_object_analysis.kernel_name == "unified_test"


class TestCodeObjectAnalysisDataclass:
    """Tests for CodeObjectAnalysis frozen dataclass."""

    def test_code_object_analysis_is_frozen(self) -> None:
        """CodeObjectAnalysis should be immutable."""
        from wafer_core.lib.kernel_scope.api import CodeObjectAnalysis

        code_obj = CodeObjectAnalysis(
            kernel_name="test",
            architecture="gfx90a",
            vgpr_count=32,
            sgpr_count=16,
            agpr_count=0,
            vgpr_spill_count=0,
            sgpr_spill_count=0,
            lds_bytes=0,
            global_loads=0,
            global_stores=0,
            lds_ops=0,
            mfma_count=0,
            fma_count=0,
            packed_ops_count=0,
            waitcnt_full_stalls=0,
            barriers=0,
            isa_text="",
            metadata_yaml="",
            annotated_isa_text="",
        )

        # Should raise FrozenInstanceError when trying to mutate
        with pytest.raises(Exception):  # FrozenInstanceError
            code_obj.vgpr_count = 64

    def test_code_object_analysis_hashable(self) -> None:
        """CodeObjectAnalysis should be hashable."""
        from wafer_core.lib.kernel_scope.api import CodeObjectAnalysis

        code_obj = CodeObjectAnalysis(
            kernel_name="test",
            architecture="gfx90a",
            vgpr_count=32,
            sgpr_count=16,
            agpr_count=0,
            vgpr_spill_count=0,
            sgpr_spill_count=0,
            lds_bytes=0,
            global_loads=0,
            global_stores=0,
            lds_ops=0,
            mfma_count=0,
            fma_count=0,
            packed_ops_count=0,
            waitcnt_full_stalls=0,
            barriers=0,
            isa_text="",
            metadata_yaml="",
            annotated_isa_text="",
        )

        # Should be usable in sets and as dict keys
        s = {code_obj}
        assert code_obj in s

        d = {code_obj: "value"}
        assert d[code_obj] == "value"
