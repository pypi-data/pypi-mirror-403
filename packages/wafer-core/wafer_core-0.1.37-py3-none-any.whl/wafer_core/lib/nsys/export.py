"""NSYS data export via subprocess calls."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path


def export_kernels(nsys_path: str, report_path: Path, output_path: Path) -> Path:
    """Export kernel summary from NSYS report."""
    kernel_json_path = output_path / "kernels.json"

    # Try new report name first (nsys 2024.x+), fall back to legacy
    # Report names changed in nsys 2024.x: gpukernsum -> cuda_gpu_kern_sum
    report_names = ["cuda_gpu_kern_sum", "gpukernsum"]

    for report_name in report_names:
        result = subprocess.run(
            [
                nsys_path, "stats",
                "--report", report_name,
                "--format", "json",
                "--output", str(kernel_json_path),
                str(report_path)
            ],
            capture_output=True,
            text=True,
            timeout=300,
            check=False
        )

        stderr_lower = (result.stderr or "").lower()
        # If report name is not found, try the next one
        if "report" in stderr_lower and "could not be found" in stderr_lower:
            continue
        if result.returncode != 0:
            raise subprocess.CalledProcessError(result.returncode, result.args, result.stdout, result.stderr)
        break

    return kernel_json_path


def export_timeline(nsys_path: str, report_path: Path, output_path: Path) -> Path:
    """Export timeline from NSYS report."""
    timeline_json_path = output_path / "timeline.json"
    subprocess.run(
        [
            nsys_path, "export",
            "--type", "json",
            "--output", str(timeline_json_path),
            str(report_path)
        ],
        capture_output=True,
        text=True,
        timeout=600,
        check=True
    )
    return timeline_json_path


def export_memory(nsys_path: str, report_path: Path, output_path: Path) -> Path:
    """Export memory usage from NSYS report."""
    memory_json_path = output_path / "memory.json"

    # Try new report names first (nsys 2024.x+), fall back to legacy
    report_names = ["cuda_gpu_mem_time_series", "gpumemtimeseries"]

    for report_name in report_names:
        result = subprocess.run(
            [
                nsys_path, "stats",
                "--report", report_name,
                "--format", "json",
                "--output", str(memory_json_path),
                str(report_path)
            ],
            capture_output=True,
            text=True,
            timeout=300,
            check=False
        )

        stderr_lower = (result.stderr or "").lower()
        # If report name is not found, try the next one
        if "report" in stderr_lower and "could not be found" in stderr_lower:
            continue
        if result.returncode != 0:
            raise subprocess.CalledProcessError(result.returncode, result.args, result.stdout, result.stderr)
        break

    return memory_json_path


def load_exported_data(kernel_path: Path, timeline_path: Path, memory_path: Path) -> tuple[dict, dict, dict]:
    """Load exported JSON data from NSYS exports."""
    if not kernel_path.exists():
        raise FileNotFoundError(f"Kernel JSON file not found: {kernel_path}")
    if not timeline_path.exists():
        raise FileNotFoundError(f"Timeline JSON file not found: {timeline_path}")
    if not memory_path.exists():
        raise FileNotFoundError(f"Memory JSON file not found: {memory_path}")
    
    kernels_data = json.loads(kernel_path.read_text())
    from .parsing import parse_ndjson
    timeline_data = parse_ndjson(timeline_path)
    memory_data = json.loads(memory_path.read_text())
    
    return kernels_data, timeline_data, memory_data
