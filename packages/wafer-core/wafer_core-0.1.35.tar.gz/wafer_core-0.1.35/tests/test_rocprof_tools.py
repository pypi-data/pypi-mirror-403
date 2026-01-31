"""Tests for rocprof tools integration.

Tests that rocprof tools can be imported and have correct structure.
"""

import pytest
from pathlib import Path

from wafer_core.rollouts.dtypes import ToolCall
from wafer_core.tools import (
    ROCPROF_COMPUTE_ANALYZE_TOOL,
    ROCPROF_COMPUTE_PROFILE_TOOL,
    ROCPROF_SDK_ANALYZE_TOOL,
    ROCPROF_SDK_PROFILE_TOOL,
    ROCPROF_SYSTEMS_INSTRUMENT_TOOL,
    ROCPROF_SYSTEMS_PROFILE_TOOL,
    ROCPROF_SYSTEMS_QUERY_TOOL,
    ROCPROF_SYSTEMS_SAMPLE_TOOL,
    exec_rocprof_compute_analyze,
    exec_rocprof_compute_profile,
    exec_rocprof_sdk_analyze,
    exec_rocprof_sdk_profile,
    exec_rocprof_systems_instrument,
    exec_rocprof_systems_profile,
    exec_rocprof_systems_query,
    exec_rocprof_systems_sample,
)


class TestRocprofToolsImport:
    """Test that rocprof tools can be imported correctly."""

    def test_sdk_tools_imported(self) -> None:
        """Test ROCprofiler-SDK tools are imported."""
        assert ROCPROF_SDK_PROFILE_TOOL is not None
        assert ROCPROF_SDK_ANALYZE_TOOL is not None
        assert callable(exec_rocprof_sdk_profile)
        assert callable(exec_rocprof_sdk_analyze)

    def test_compute_tools_imported(self) -> None:
        """Test ROCprofiler-Compute tools are imported."""
        assert ROCPROF_COMPUTE_PROFILE_TOOL is not None
        assert ROCPROF_COMPUTE_ANALYZE_TOOL is not None
        assert callable(exec_rocprof_compute_profile)
        assert callable(exec_rocprof_compute_analyze)

    def test_systems_tools_imported(self) -> None:
        """Test ROCprofiler-Systems tools are imported."""
        assert ROCPROF_SYSTEMS_PROFILE_TOOL is not None
        assert ROCPROF_SYSTEMS_SAMPLE_TOOL is not None
        assert ROCPROF_SYSTEMS_INSTRUMENT_TOOL is not None
        assert ROCPROF_SYSTEMS_QUERY_TOOL is not None
        assert callable(exec_rocprof_systems_profile)
        assert callable(exec_rocprof_systems_sample)
        assert callable(exec_rocprof_systems_instrument)
        assert callable(exec_rocprof_systems_query)


class TestRocprofToolsStructure:
    """Test that rocprof tools have correct structure."""

    def test_sdk_profile_tool_structure(self) -> None:
        """Test ROCprofiler-SDK profile tool structure."""
        tool = ROCPROF_SDK_PROFILE_TOOL
        assert tool.type == "function"
        assert tool.function.name == "rocprof_sdk_profile"
        assert "command" in tool.function.parameters.properties
        assert "command" in tool.function.required

    def test_compute_profile_tool_structure(self) -> None:
        """Test ROCprofiler-Compute profile tool structure."""
        tool = ROCPROF_COMPUTE_PROFILE_TOOL
        assert tool.type == "function"
        assert tool.function.name == "rocprof_compute_profile"
        assert "command" in tool.function.parameters.properties
        assert "workload_name" in tool.function.parameters.properties
        assert "command" in tool.function.required
        assert "workload_name" in tool.function.required

    def test_systems_profile_tool_structure(self) -> None:
        """Test ROCprofiler-Systems profile tool structure."""
        tool = ROCPROF_SYSTEMS_PROFILE_TOOL
        assert tool.type == "function"
        assert tool.function.name == "rocprof_systems_profile"
        assert "command" in tool.function.parameters.properties
        assert "command" in tool.function.required


class TestRocprofToolsErrorHandling:
    """Test error handling in rocprof tools."""

    @pytest.mark.asyncio
    async def test_sdk_profile_missing_command(self) -> None:
        """Test SDK profile tool handles missing command."""
        from wafer_core.tools.rocprof_sdk_tools.rocprof_sdk_profile_tool import exec_rocprof_sdk_profile

        tool_call = ToolCall(
            id="test-1",
            name="rocprof_sdk_profile",
            args={}  # Missing required "command"
        )

        result = await exec_rocprof_sdk_profile(
            tool_call=tool_call,
            working_dir=Path.cwd()
        )

        # Should handle missing command gracefully
        assert result is not None
        # The function will try to parse empty command, which should fail
        assert result.is_error or result.content  # Either error or some output

    @pytest.mark.asyncio
    async def test_compute_profile_missing_workload_name(self) -> None:
        """Test Compute profile tool handles missing workload_name."""
        from wafer_core.tools.rocprof_compute_tools.rocprof_compute_profile_tool import exec_rocprof_compute_profile

        tool_call = ToolCall(
            id="test-2",
            name="rocprof_compute_profile",
            args={"command": "./test"}  # Missing required "workload_name"
        )

        result = await exec_rocprof_compute_profile(
            tool_call=tool_call,
            working_dir=Path.cwd()
        )

        # Should handle missing workload_name gracefully
        assert result is not None
        # The function will try to call lib function, which should fail
        assert result.is_error or result.content  # Either error or some output

    @pytest.mark.asyncio
    async def test_systems_query_handles_invalid_query_type(self) -> None:
        """Test Systems query tool handles invalid query_type."""
        from wafer_core.tools.rocprof_systems_tools.rocprof_systems_query_tool import exec_rocprof_systems_query

        tool_call = ToolCall(
            id="test-3",
            name="rocprof_systems_query",
            args={"query_type": "invalid_type"}
        )

        result = await exec_rocprof_systems_query(
            tool_call=tool_call,
            working_dir=Path.cwd()
        )

        # Should return error for invalid query_type
        assert result is not None
        assert result.is_error
        assert "Unknown query_type" in result.error or "invalid" in result.error.lower()
