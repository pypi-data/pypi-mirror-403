"""Tests for roofline analysis module."""

import pytest

from wafer_core.roofline import (
    Bottleneck,
    Dtype,
    get_gpu_spec,
    list_gpus,
    roofline_analysis,
)


class TestGpuSpecs:
    def test_list_gpus_returns_sorted_list(self):
        gpus = list_gpus()
        assert isinstance(gpus, list)
        assert len(gpus) > 0
        assert gpus == sorted(gpus)

    def test_get_gpu_spec_direct(self):
        spec = get_gpu_spec("H100")
        assert spec.name == "NVIDIA H100 SXM"
        assert spec.peak_bandwidth_gbps == 3350
        assert spec.peak_tflops_fp16 == 1979

    def test_get_gpu_spec_case_insensitive(self):
        spec1 = get_gpu_spec("h100")
        spec2 = get_gpu_spec("H100")
        assert spec1 == spec2

    def test_get_gpu_spec_alias(self):
        spec = get_gpu_spec("4090")
        assert spec.name == "NVIDIA RTX 4090"

    def test_get_gpu_spec_unknown_raises(self):
        with pytest.raises(ValueError, match="Unknown GPU"):
            get_gpu_spec("nonexistent_gpu")

    def test_all_gpus_have_required_fields(self):
        for name in list_gpus():
            spec = get_gpu_spec(name)
            assert spec.peak_bandwidth_gbps > 0
            assert spec.peak_tflops_fp16 > 0
            assert spec.peak_tflops_fp32 > 0


class TestRooflineAnalysis:
    def test_compute_bound_matmul(self):
        # 4096^3 matmul - very compute heavy
        result = roofline_analysis(
            gpu="H100",
            dtype="fp16",
            bytes_moved=100.7e6,  # ~100 MB
            flops=137.4e12,  # 137 TFLOPS
            time_ms=85,
        )
        assert result.bottleneck == Bottleneck.COMPUTE
        assert result.arithmetic_intensity > result.ridge_point
        # 85ms actual vs ~69ms theoretical = ~81% efficiency
        assert 75 < result.efficiency_pct < 90

    def test_memory_bound_elementwise(self):
        # Elementwise add - very memory heavy
        result = roofline_analysis(
            gpu="H100",
            dtype="fp16",
            bytes_moved=4e9,  # 4 GB
            flops=1e9,  # 1 GFLOP
            time_ms=2.0,
        )
        assert result.bottleneck == Bottleneck.MEMORY
        assert result.arithmetic_intensity < result.ridge_point
        # Memory bound time should be ~1.2ms, so 2ms = ~60% efficiency
        assert 50 < result.efficiency_pct < 70

    def test_time_s_vs_time_ms(self):
        result1 = roofline_analysis(
            gpu="H100",
            dtype="fp16",
            bytes_moved=1e9,
            flops=1e12,
            time_ms=10,
        )
        result2 = roofline_analysis(
            gpu="H100",
            dtype="fp16",
            bytes_moved=1e9,
            flops=1e12,
            time_s=0.01,
        )
        assert result1.actual_time_s == result2.actual_time_s
        assert result1.efficiency_pct == result2.efficiency_pct

    def test_cannot_provide_both_time_s_and_time_ms(self):
        with pytest.raises(ValueError, match="only one of"):
            roofline_analysis(
                gpu="H100",
                dtype="fp16",
                bytes_moved=1e9,
                flops=1e12,
                time_s=0.01,
                time_ms=10,
            )

    def test_must_provide_time(self):
        with pytest.raises(ValueError, match="Must provide"):
            roofline_analysis(
                gpu="H100",
                dtype="fp16",
                bytes_moved=1e9,
                flops=1e12,
            )

    def test_dtype_enum_and_string(self):
        result1 = roofline_analysis(
            gpu="H100",
            dtype="fp16",
            bytes_moved=1e9,
            flops=1e12,
            time_ms=1,
        )
        result2 = roofline_analysis(
            gpu="H100",
            dtype=Dtype.FP16,
            bytes_moved=1e9,
            flops=1e12,
            time_ms=1,
        )
        assert result1.peak_flops_per_s == result2.peak_flops_per_s

    def test_format_report_contains_key_info(self):
        result = roofline_analysis(
            gpu="H100",
            dtype="fp16",
            bytes_moved=1e9,
            flops=1e12,
            time_ms=1,
        )
        report = result.format_report()
        assert "H100" in report
        assert "FP16" in report
        assert "Efficiency" in report
        assert "Bottleneck" in report


class TestDifferentGpus:
    @pytest.mark.parametrize("gpu", ["H100", "A100", "B200", "MI300X", "RTX_4090"])
    def test_analysis_works_for_all_gpus(self, gpu: str) -> None:
        result = roofline_analysis(
            gpu=gpu,
            dtype="fp16",
            bytes_moved=1e9,
            flops=1e12,
            time_ms=1,
        )
        assert result.efficiency_pct > 0
        assert result.theoretical_time_s > 0
