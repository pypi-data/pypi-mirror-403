"""Tests for ISA analysis tools.

Tests the ISA analysis tool for AMD GPU code objects.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import httpx

from wafer_core.tools.isa_analysis_tools import (
    analyze_isa,
    format_isa_summary,
    ISAAnalysisResult,
)


class TestISAAnalysisResultDataclass:
    """Test ISAAnalysisResult dataclass."""

    def test_result_is_frozen(self) -> None:
        """ISAAnalysisResult should be immutable."""
        result = ISAAnalysisResult(
            kernel_name="test_kernel",
            architecture="gfx942",
            vgpr_count=32,
            sgpr_count=24,
            agpr_count=16,
            vgpr_spill_count=0,
            sgpr_spill_count=0,
            lds_bytes=65536,
            global_loads=10,
            global_stores=5,
            lds_ops=20,
            mfma_count=8,
            fma_count=4,
            packed_ops_count=2,
            waitcnt_full_stalls=3,
            barriers=1,
            isa_text="test isa",
            metadata_yaml="test metadata",
            annotated_isa_text="test annotated isa",
        )

        with pytest.raises(AttributeError):
            result.kernel_name = "modified"  # type: ignore

    def test_result_fields(self) -> None:
        """ISAAnalysisResult should have all expected fields."""
        result = ISAAnalysisResult(
            kernel_name="test_kernel",
            architecture="gfx942",
            vgpr_count=32,
            sgpr_count=24,
            agpr_count=16,
            vgpr_spill_count=0,
            sgpr_spill_count=0,
            lds_bytes=65536,
            global_loads=10,
            global_stores=5,
            lds_ops=20,
            mfma_count=8,
            fma_count=4,
            packed_ops_count=2,
            waitcnt_full_stalls=3,
            barriers=1,
            isa_text="test isa",
            metadata_yaml="test metadata",
            annotated_isa_text="test annotated isa",
        )

        assert result.kernel_name == "test_kernel"
        assert result.architecture == "gfx942"
        assert result.vgpr_count == 32
        assert result.sgpr_count == 24
        assert result.agpr_count == 16
        assert result.vgpr_spill_count == 0
        assert result.sgpr_spill_count == 0
        assert result.lds_bytes == 65536
        assert result.global_loads == 10
        assert result.global_stores == 5
        assert result.lds_ops == 20
        assert result.mfma_count == 8
        assert result.fma_count == 4
        assert result.packed_ops_count == 2
        assert result.waitcnt_full_stalls == 3
        assert result.barriers == 1
        assert result.isa_text == "test isa"
        assert result.metadata_yaml == "test metadata"


class TestAnalyzeIsa:
    """Tests for analyze_isa function."""

    def test_file_not_found_raises_error(self, tmp_path: Path) -> None:
        """Should raise FileNotFoundError for missing file."""
        fake_path = tmp_path / "nonexistent.co"

        with pytest.raises(FileNotFoundError):
            analyze_isa(
                co_file_path=fake_path,
                api_url="http://localhost:8000",
                auth_headers={},
            )

    def test_wrong_extension_raises_error(self, tmp_path: Path) -> None:
        """Should raise ValueError for wrong file extension."""
        wrong_ext = tmp_path / "test.txt"
        wrong_ext.write_bytes(b"not a code object")

        with pytest.raises(ValueError, match=r"\.co"):
            analyze_isa(
                co_file_path=wrong_ext,
                api_url="http://localhost:8000",
                auth_headers={},
            )

    def test_calls_api_with_correct_url(self, tmp_path: Path) -> None:
        """Should call API with correct URL and file."""
        co_file = tmp_path / "test.co"
        co_file.write_bytes(b"fake code object")

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "kernel_name": "test",
            "architecture": "gfx942",
            "vgpr_count": 32,
            "sgpr_count": 24,
            "agpr_count": 16,
            "vgpr_spill_count": 0,
            "sgpr_spill_count": 0,
            "lds_bytes": 0,
            "global_loads": 10,
            "global_stores": 5,
            "lds_ops": 0,
            "mfma_count": 8,
            "fma_count": 0,
            "packed_ops_count": 0,
            "waitcnt_full_stalls": 0,
            "barriers": 0,
            "isa_text": "",
            "metadata_yaml": "",
        }

        with patch("httpx.Client") as mock_client:
            mock_instance = MagicMock()
            mock_instance.__enter__.return_value = mock_instance
            mock_instance.__exit__.return_value = None
            mock_instance.post.return_value = mock_response
            mock_client.return_value = mock_instance

            result = analyze_isa(
                co_file_path=co_file,
                api_url="http://test-api:8000",
                auth_headers={"Authorization": "Bearer test-token"},
            )

            # Check API was called with correct URL
            mock_instance.post.assert_called_once()
            call_args = mock_instance.post.call_args
            assert call_args[0][0] == "http://test-api:8000/v1/isa/analyze"

            # Check result
            assert result.kernel_name == "test"
            assert result.architecture == "gfx942"

    def test_passes_auth_headers(self, tmp_path: Path) -> None:
        """Should pass auth headers to API."""
        co_file = tmp_path / "test.co"
        co_file.write_bytes(b"fake code object")

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "kernel_name": "test",
            "architecture": "gfx942",
            "vgpr_count": 0,
            "sgpr_count": 0,
            "agpr_count": 0,
            "vgpr_spill_count": 0,
            "sgpr_spill_count": 0,
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
        }

        with patch("httpx.Client") as mock_client:
            mock_instance = MagicMock()
            mock_instance.__enter__.return_value = mock_instance
            mock_instance.__exit__.return_value = None
            mock_instance.post.return_value = mock_response
            mock_client.return_value = mock_instance

            analyze_isa(
                co_file_path=co_file,
                api_url="http://test-api:8000",
                auth_headers={"Authorization": "Bearer secret"},
            )

            # Check client was created with auth headers
            mock_client.assert_called_once()
            call_kwargs = mock_client.call_args[1]
            assert call_kwargs["headers"] == {"Authorization": "Bearer secret"}


class TestFormatIsaSummary:
    """Tests for format_isa_summary function."""

    def test_basic_formatting(self) -> None:
        """Should format basic result correctly."""
        result = ISAAnalysisResult(
            kernel_name="gemm_kernel",
            architecture="gfx942",
            vgpr_count=32,
            sgpr_count=24,
            agpr_count=16,
            vgpr_spill_count=0,
            sgpr_spill_count=0,
            lds_bytes=65536,
            global_loads=10,
            global_stores=5,
            lds_ops=20,
            mfma_count=8,
            fma_count=4,
            packed_ops_count=2,
            waitcnt_full_stalls=3,
            barriers=1,
            isa_text="",
            metadata_yaml="",
            annotated_isa_text="",
        )

        summary = format_isa_summary(result)

        assert "gemm_kernel" in summary
        assert "gfx942" in summary
        assert "32" in summary  # VGPR count
        assert "24" in summary  # SGPR count
        assert "16" in summary  # AGPR count
        assert "Spills: None" in summary

    def test_spills_warning(self) -> None:
        """Should show spills warning when spills present."""
        result = ISAAnalysisResult(
            kernel_name="spilling_kernel",
            architecture="gfx942",
            vgpr_count=256,
            sgpr_count=100,
            agpr_count=0,
            vgpr_spill_count=8,
            sgpr_spill_count=4,
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

        summary = format_isa_summary(result)

        assert "SPILLS DETECTED" in summary
        assert "VGPR spills: 8" in summary
        assert "SGPR spills: 4" in summary

    def test_vgpr_spills_only(self) -> None:
        """Should show only VGPR spills when SGPR has none."""
        result = ISAAnalysisResult(
            kernel_name="vgpr_spilling",
            architecture="gfx942",
            vgpr_count=256,
            sgpr_count=100,
            agpr_count=0,
            vgpr_spill_count=16,
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

        summary = format_isa_summary(result)

        assert "SPILLS DETECTED" in summary
        assert "VGPR spills: 16" in summary
        assert "SGPR spills" not in summary

    def test_contains_all_sections(self) -> None:
        """Summary should contain all sections."""
        result = ISAAnalysisResult(
            kernel_name="test",
            architecture="gfx942",
            vgpr_count=32,
            sgpr_count=24,
            agpr_count=16,
            vgpr_spill_count=0,
            sgpr_spill_count=0,
            lds_bytes=65536,
            global_loads=10,
            global_stores=5,
            lds_ops=20,
            mfma_count=8,
            fma_count=4,
            packed_ops_count=2,
            waitcnt_full_stalls=3,
            barriers=1,
            isa_text="",
            metadata_yaml="",
            annotated_isa_text="",
        )

        summary = format_isa_summary(result)

        assert "=== Registers ===" in summary
        assert "=== Memory ===" in summary
        assert "=== Instructions ===" in summary
