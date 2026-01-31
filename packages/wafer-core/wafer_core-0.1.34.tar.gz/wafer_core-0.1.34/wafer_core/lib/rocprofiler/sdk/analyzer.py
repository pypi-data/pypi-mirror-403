"""High-level analysis API for rocprofiler output files.

Provides unified interface for analyzing any rocprofiler output format.
Follows Wafer-391: ROCprofiler Tools Architecture.
"""

from pathlib import Path

from wafer_core.lib.rocprofiler.sdk import parser
from wafer_core.lib.rocprofiler.sdk.types import AnalysisResult


def analyze_file(file_path: Path) -> AnalysisResult:
    """Analyze a rocprofiler output file (auto-detect format).

    Supports:
    - CSV stats files (stats_*.csv, *.csv)
    - JSON trace files (*.json)
    - rocpd databases (*_results.db, *.rocpd, *.db)

    Args:
        file_path: Path to rocprofiler output file

    Returns:
        AnalysisResult with kernels, summary, and format info

    Example:
        >>> result = analyze_file(Path("stats_kernel.csv"))
        >>> if result.success:
        ...     print(f"Found {len(result.kernels)} kernels")
        ...     print(f"Total duration: {result.summary['total_duration_ns']} ns")
    """
    try:
        # Auto-detect format based on file extension
        suffix = file_path.suffix.lower()

        if suffix == ".csv":
            kernels = parser.parse_csv(file_path)
            file_format = "csv"
        elif suffix == ".json":
            kernels = parser.parse_json(file_path)
            file_format = "json"
        elif suffix in [".db", ".rocpd"]:
            kernels = parser.parse_rocpd(file_path)
            file_format = "rocpd"
        else:
            return AnalysisResult(
                success=False,
                file_format="unknown",
                error=f"Unsupported file format: {suffix}",
            )

        # Generate summary statistics
        total_duration = sum(k.duration_ns or 0 for k in kernels)
        avg_duration = total_duration / len(kernels) if kernels else 0

        # Find min and max duration
        durations = [k.duration_ns for k in kernels if k.duration_ns is not None]
        min_duration = min(durations) if durations else 0
        max_duration = max(durations) if durations else 0

        summary = {
            "total_kernels": len(kernels),
            "total_duration_ns": total_duration,
            "avg_duration_ns": avg_duration,
            "min_duration_ns": min_duration,
            "max_duration_ns": max_duration,
            "total_duration_ms": total_duration / 1_000_000,
            "avg_duration_ms": avg_duration / 1_000_000,
        }

        return AnalysisResult(
            success=True, file_format=file_format, kernels=kernels, summary=summary
        )

    except FileNotFoundError:
        return AnalysisResult(
            success=False, file_format="unknown", error=f"File not found: {file_path}"
        )
    except Exception as e:
        return AnalysisResult(
            success=False, file_format="unknown", error=f"Analysis failed: {str(e)}"
        )


def analyze_csv(file_path: Path) -> AnalysisResult:
    """Directly analyze a CSV file (skip auto-detection).

    Args:
        file_path: Path to CSV stats file

    Returns:
        AnalysisResult with kernels and summary
    """
    try:
        kernels = parser.parse_csv(file_path)

        total_duration = sum(k.duration_ns or 0 for k in kernels)
        avg_duration = total_duration / len(kernels) if kernels else 0

        durations = [k.duration_ns for k in kernels if k.duration_ns is not None]
        min_duration = min(durations) if durations else 0
        max_duration = max(durations) if durations else 0

        summary = {
            "total_kernels": len(kernels),
            "total_duration_ns": total_duration,
            "avg_duration_ns": avg_duration,
            "min_duration_ns": min_duration,
            "max_duration_ns": max_duration,
            "total_duration_ms": total_duration / 1_000_000,
            "avg_duration_ms": avg_duration / 1_000_000,
        }

        return AnalysisResult(
            success=True, file_format="csv", kernels=kernels, summary=summary
        )

    except Exception as e:
        return AnalysisResult(
            success=False, file_format="csv", error=f"CSV analysis failed: {str(e)}"
        )


def analyze_json(file_path: Path) -> AnalysisResult:
    """Directly analyze a JSON trace file.

    Args:
        file_path: Path to JSON trace file

    Returns:
        AnalysisResult with kernels and summary
    """
    try:
        kernels = parser.parse_json(file_path)

        total_duration = sum(k.duration_ns or 0 for k in kernels)
        avg_duration = total_duration / len(kernels) if kernels else 0

        durations = [k.duration_ns for k in kernels if k.duration_ns is not None]
        min_duration = min(durations) if durations else 0
        max_duration = max(durations) if durations else 0

        summary = {
            "total_kernels": len(kernels),
            "total_duration_ns": total_duration,
            "avg_duration_ns": avg_duration,
            "min_duration_ns": min_duration,
            "max_duration_ns": max_duration,
            "total_duration_ms": total_duration / 1_000_000,
            "avg_duration_ms": avg_duration / 1_000_000,
        }

        return AnalysisResult(
            success=True, file_format="json", kernels=kernels, summary=summary
        )

    except Exception as e:
        return AnalysisResult(
            success=False, file_format="json", error=f"JSON analysis failed: {str(e)}"
        )


def analyze_rocpd(file_path: Path) -> AnalysisResult:
    """Directly analyze a rocpd database.

    Args:
        file_path: Path to rocpd database file

    Returns:
        AnalysisResult with kernels and summary
    """
    try:
        kernels = parser.parse_rocpd(file_path)

        total_duration = sum(k.duration_ns or 0 for k in kernels)
        avg_duration = total_duration / len(kernels) if kernels else 0

        durations = [k.duration_ns for k in kernels if k.duration_ns is not None]
        min_duration = min(durations) if durations else 0
        max_duration = max(durations) if durations else 0

        summary = {
            "total_kernels": len(kernels),
            "total_duration_ns": total_duration,
            "avg_duration_ns": avg_duration,
            "min_duration_ns": min_duration,
            "max_duration_ns": max_duration,
            "total_duration_ms": total_duration / 1_000_000,
            "avg_duration_ms": avg_duration / 1_000_000,
        }

        return AnalysisResult(
            success=True, file_format="rocpd", kernels=kernels, summary=summary
        )

    except Exception as e:
        return AnalysisResult(
            success=False, file_format="rocpd", error=f"rocpd analysis failed: {str(e)}"
        )
