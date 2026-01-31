"""Tests for TraceLens tools integration.

Tests that TraceLens tools can be imported and have correct structure.
"""

import pytest
from pathlib import Path

from wafer_core.rollouts.dtypes import ToolCall
from wafer_core.tools import (
    TRACELENS_REPORT_TOOL,
    TRACELENS_COMPARE_TOOL,
    TRACELENS_COLLECTIVE_TOOL,
    exec_tracelens_report,
    exec_tracelens_compare,
    exec_tracelens_collective,
)


class TestTracelensToolsImport:
    """Test that TraceLens tools can be imported correctly."""

    def test_report_tool_imported(self) -> None:
        """Test TraceLens report tool is imported."""
        assert TRACELENS_REPORT_TOOL is not None
        assert callable(exec_tracelens_report)

    def test_compare_tool_imported(self) -> None:
        """Test TraceLens compare tool is imported."""
        assert TRACELENS_COMPARE_TOOL is not None
        assert callable(exec_tracelens_compare)

    def test_collective_tool_imported(self) -> None:
        """Test TraceLens collective tool is imported."""
        assert TRACELENS_COLLECTIVE_TOOL is not None
        assert callable(exec_tracelens_collective)


class TestTracelensToolsStructure:
    """Test that TraceLens tools have correct structure."""

    def test_report_tool_structure(self) -> None:
        """Test TraceLens report tool structure."""
        tool = TRACELENS_REPORT_TOOL
        assert tool.type == "function"
        assert tool.function.name == "tracelens_report"
        assert "trace_path" in tool.function.parameters.properties
        assert "trace_path" in tool.function.required

    def test_compare_tool_structure(self) -> None:
        """Test TraceLens compare tool structure."""
        tool = TRACELENS_COMPARE_TOOL
        assert tool.type == "function"
        assert tool.function.name == "tracelens_compare"
        assert "baseline_path" in tool.function.parameters.properties
        assert "candidate_path" in tool.function.parameters.properties
        assert "baseline_path" in tool.function.required
        assert "candidate_path" in tool.function.required

    def test_report_tool_optional_params(self) -> None:
        """Test TraceLens report tool has expected optional params."""
        tool = TRACELENS_REPORT_TOOL
        props = tool.function.parameters.properties
        assert "output_path" in props
        assert "format" in props
        assert "short_kernel_study" in props
        assert "kernel_details" in props

    def test_compare_tool_optional_params(self) -> None:
        """Test TraceLens compare tool has expected optional params."""
        tool = TRACELENS_COMPARE_TOOL
        props = tool.function.parameters.properties
        assert "output_path" in props
        assert "baseline_name" in props
        assert "candidate_name" in props

    def test_collective_tool_structure(self) -> None:
        """Test TraceLens collective tool structure."""
        tool = TRACELENS_COLLECTIVE_TOOL
        assert tool.type == "function"
        assert tool.function.name == "tracelens_collective"
        assert "trace_dir" in tool.function.parameters.properties
        assert "world_size" in tool.function.parameters.properties
        assert "trace_dir" in tool.function.required
        assert "world_size" in tool.function.required

    def test_collective_tool_optional_params(self) -> None:
        """Test TraceLens collective tool has expected optional params."""
        tool = TRACELENS_COLLECTIVE_TOOL
        props = tool.function.parameters.properties
        assert "output_path" in props


class TestTracelensToolsErrorHandling:
    """Test error handling in TraceLens tools."""

    @pytest.mark.asyncio
    async def test_report_missing_trace_path(self) -> None:
        """Test report tool handles missing trace_path."""
        tool_call = ToolCall(
            id="test-1",
            name="tracelens_report",
            args={}  # Missing required "trace_path"
        )

        result = await exec_tracelens_report(
            tool_call=tool_call,
            working_dir=Path.cwd()
        )

        assert result.is_error
        assert "trace_path" in result.error

    @pytest.mark.asyncio
    async def test_report_file_not_found(self) -> None:
        """Test report tool handles missing file."""
        tool_call = ToolCall(
            id="test-2",
            name="tracelens_report",
            args={"trace_path": "/nonexistent/trace.json"}
        )

        result = await exec_tracelens_report(
            tool_call=tool_call,
            working_dir=Path.cwd()
        )

        assert result.is_error
        assert "not found" in result.error.lower()

    @pytest.mark.asyncio
    async def test_compare_missing_baseline(self) -> None:
        """Test compare tool handles missing baseline_path."""
        tool_call = ToolCall(
            id="test-3",
            name="tracelens_compare",
            args={"candidate_path": "candidate.xlsx"}
        )

        result = await exec_tracelens_compare(
            tool_call=tool_call,
            working_dir=Path.cwd()
        )

        assert result.is_error
        assert "baseline_path" in result.error

    @pytest.mark.asyncio
    async def test_compare_missing_candidate(self) -> None:
        """Test compare tool handles missing candidate_path."""
        tool_call = ToolCall(
            id="test-4",
            name="tracelens_compare",
            args={"baseline_path": "baseline.xlsx"}
        )

        result = await exec_tracelens_compare(
            tool_call=tool_call,
            working_dir=Path.cwd()
        )

        assert result.is_error
        assert "candidate_path" in result.error

    @pytest.mark.asyncio
    async def test_compare_file_not_found(self) -> None:
        """Test compare tool handles missing files."""
        tool_call = ToolCall(
            id="test-5",
            name="tracelens_compare",
            args={
                "baseline_path": "/nonexistent/baseline.xlsx",
                "candidate_path": "/nonexistent/candidate.xlsx"
            }
        )

        result = await exec_tracelens_compare(
            tool_call=tool_call,
            working_dir=Path.cwd()
        )

        assert result.is_error
        assert "not found" in result.error.lower()

    @pytest.mark.asyncio
    async def test_collective_missing_trace_dir(self) -> None:
        """Test collective tool handles missing trace_dir."""
        tool_call = ToolCall(
            id="test-6",
            name="tracelens_collective",
            args={"world_size": 8}
        )

        result = await exec_tracelens_collective(
            tool_call=tool_call,
            working_dir=Path.cwd()
        )

        assert result.is_error
        assert "trace_dir" in result.error

    @pytest.mark.asyncio
    async def test_collective_missing_world_size(self) -> None:
        """Test collective tool handles missing world_size."""
        tool_call = ToolCall(
            id="test-7",
            name="tracelens_collective",
            args={"trace_dir": "/some/path"}
        )

        result = await exec_tracelens_collective(
            tool_call=tool_call,
            working_dir=Path.cwd()
        )

        assert result.is_error
        assert "world_size" in result.error

    @pytest.mark.asyncio
    async def test_collective_dir_not_found(self) -> None:
        """Test collective tool handles missing directory."""
        tool_call = ToolCall(
            id="test-8",
            name="tracelens_collective",
            args={
                "trace_dir": "/nonexistent/traces",
                "world_size": 8
            }
        )

        result = await exec_tracelens_collective(
            tool_call=tool_call,
            working_dir=Path.cwd()
        )

        assert result.is_error
        assert "not found" in result.error.lower()
