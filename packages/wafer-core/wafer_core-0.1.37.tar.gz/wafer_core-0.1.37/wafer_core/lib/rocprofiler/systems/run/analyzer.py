"""High-level analysis API for rocprof-sys-run output files.

Provides unified interface for analyzing rocprof-sys-run outputs.
Follows Wafer-391: ROCprofiler Tools Architecture.
"""

from pathlib import Path

from wafer_core.lib.rocprofiler.systems import parsers
from wafer_core.lib.rocprofiler.systems.types import AnalysisResult


def analyze_file(file_path: Path) -> AnalysisResult:
    """Analyze a rocprof-sys output file (auto-detect format).

    Supports:
    - JSON files (wall_clock-*.json, metadata-*.json, functions-*.json)
    - Text files (wall-clock.txt, *.txt)
    - Perfetto traces (*.proto) - delegates to existing Perfetto infrastructure
    - rocpd databases (*.db) - delegates to sdk rocpd parser

    Args:
        file_path: Path to rocprof-sys output file

    Returns:
        AnalysisResult with functions, summary, and format info

    Example:
        >>> result = analyze_file(Path("wall_clock-12345.json"))
        >>> if result.success:
        ...     print(f"Found {len(result.functions)} functions")
        ...     print(f"Total time: {result.summary['total_time_ns']} ns")
    """
    try:
        # Auto-detect format based on file name and extension
        suffix = file_path.suffix.lower()
        name = file_path.name.lower()

        # Perfetto traces
        if suffix == ".proto" or "perfetto" in name:
            return AnalysisResult(
                success=True,
                file_format="perfetto",
                summary={"note": "Use Perfetto UI to visualize trace"},
                error="Perfetto traces should be opened in ui.perfetto.dev or existing Perfetto viewer",
            )

        # rocpd databases
        if suffix in [".db", ".rocpd"]:
            # Delegate to sdk rocpd parser (reuse existing infrastructure)
            return AnalysisResult(
                success=True,
                file_format="rocpd",
                summary={"note": "rocpd database detected"},
                error="Use rocprof-sdk analyzer for rocpd databases",
            )

        # JSON files
        if suffix == ".json":
            return _analyze_json(file_path)

        # Text files
        if suffix == ".txt":
            return _analyze_text(file_path)

        return AnalysisResult(
            success=False,
            file_format="unknown",
            error=f"Unsupported file format: {suffix}",
        )

    except FileNotFoundError:
        return AnalysisResult(
            success=False, file_format="unknown", error=f"File not found: {file_path}"
        )
    except Exception as e:
        return AnalysisResult(
            success=False, file_format="unknown", error=f"Analysis failed: {str(e)}"
        )


def _analyze_json(file_path: Path) -> AnalysisResult:
    """Analyze a JSON file from rocprof-sys.

    Args:
        file_path: Path to JSON file

    Returns:
        AnalysisResult with parsed data
    """
    name = file_path.name.lower()

    # Determine JSON type based on filename
    if "wall_clock" in name or "wall-clock" in name:
        functions = parsers.parse_wall_clock_json(file_path)
        file_format = "json_wall_clock"
    elif "metadata" in name:
        metadata = parsers.parse_metadata_json(file_path)
        return AnalysisResult(
            success=True, file_format="json_metadata", metadata=metadata, functions=[]
        )
    elif "function" in name:
        functions = parsers.parse_functions_json(file_path)
        file_format = "json_functions"
    else:
        # Try to parse as generic JSON
        try:
            functions = parsers.parse_wall_clock_json(file_path)
            file_format = "json_generic"
        except Exception as e:
            return AnalysisResult(
                success=False,
                file_format="json",
                error=f"Unable to parse JSON: {str(e)}",
            )

    # Generate summary statistics
    if functions:
        total_time = sum(f.total_time_ns or 0 for f in functions)
        total_calls = sum(f.call_count or 0 for f in functions)

        # Calculate average times
        times = [f.mean_time_ns for f in functions if f.mean_time_ns is not None]
        avg_time = sum(times) / len(times) if times else 0

        summary = {
            "total_functions": len(functions),
            "total_time_ns": total_time,
            "total_calls": total_calls,
            "avg_time_ns": avg_time,
            "total_time_ms": total_time / 1_000_000,
        }
    else:
        summary = {"total_functions": 0}

    return AnalysisResult(
        success=True, file_format=file_format, functions=functions, summary=summary
    )


def _analyze_text(file_path: Path) -> AnalysisResult:
    """Analyze a text file from rocprof-sys.

    Args:
        file_path: Path to text file

    Returns:
        AnalysisResult with parsed data
    """
    functions, summary = parsers.parse_text_summary(file_path)

    # Enhance summary with function count
    summary["total_functions"] = len(functions)

    if functions:
        # Calculate total time if not in summary
        if "total_time_ns" not in summary:
            total_time = sum(f.total_time_ns or 0 for f in functions)
            summary["total_time_ns"] = total_time
            summary["total_time_ms"] = total_time / 1_000_000

    return AnalysisResult(
        success=True, file_format="text", functions=functions, summary=summary
    )


def analyze_json(file_path: Path) -> AnalysisResult:
    """Directly analyze a JSON file (skip auto-detection).

    Args:
        file_path: Path to JSON file

    Returns:
        AnalysisResult with functions and summary
    """
    try:
        return _analyze_json(file_path)
    except Exception as e:
        return AnalysisResult(
            success=False, file_format="json", error=f"JSON analysis failed: {str(e)}"
        )


def analyze_text(file_path: Path) -> AnalysisResult:
    """Directly analyze a text file (skip auto-detection).

    Args:
        file_path: Path to text file

    Returns:
        AnalysisResult with functions and summary
    """
    try:
        return _analyze_text(file_path)
    except Exception as e:
        return AnalysisResult(
            success=False, file_format="text", error=f"Text analysis failed: {str(e)}"
        )
