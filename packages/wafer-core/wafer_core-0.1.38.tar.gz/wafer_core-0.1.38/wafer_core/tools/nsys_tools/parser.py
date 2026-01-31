"""NSYS Parser - Parse nsys stats CSV output into structured data.

Uses `nsys stats` commands to extract data from .nsys-rep files.
CSV format is used for cross-version compatibility.
"""

import subprocess
from pathlib import Path

from .discovery import find_nsys
from .models import (
    KernelInfo,
    MemoryTransfer,
    NSYSParseResult,
    NSYSSummary,
)


def run_nsys_stats(
    nsys_path: str,
    report_path: str | Path,
    report_type: str,
    timeout: int = 120,
) -> tuple[bool, str, str]:
    """Run nsys stats command.

    Args:
        nsys_path: Path to nsys executable
        report_path: Path to .nsys-rep file
        report_type: Report type (gpukernsum, gpumemtimesum, etc.)
        timeout: Command timeout in seconds

    Returns:
        Tuple of (success, stdout, stderr)
    """
    cmd = [
        nsys_path,
        "stats",
        "--report", report_type,
        "--format", "csv",
        "--force-export", "true",
        str(report_path),
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", f"Command timed out after {timeout}s"
    except OSError as e:
        return False, "", str(e)


def parse_kernel_csv(csv_content: str) -> list[KernelInfo]:
    """Parse kernel summary CSV from nsys stats.

    Args:
        csv_content: CSV content from nsys stats --report cuda_gpu_kern_sum

    Returns:
        List of KernelInfo objects
    """
    kernels = []
    lines = csv_content.strip().split("\n")

    # Find header line - look for a line with known CSV header columns
    # The nsys output includes informational lines before the actual CSV
    # Header line should contain "Time" and "Name" columns
    header_idx = -1
    for i, line in enumerate(lines):
        line_lower = line.lower()
        # Skip comment lines and non-CSV lines
        if line.startswith("#"):
            continue
        # Check if this looks like a CSV header with expected columns
        if ("time" in line_lower and "name" in line_lower) or \
           ("time (%)" in line_lower) or \
           ("total time" in line_lower and "instances" in line_lower):
            header_idx = i
            break

    if header_idx < 0 or header_idx >= len(lines) - 1:
        return kernels

    headers = [h.strip().strip('"') for h in lines[header_idx].split(",")]

    for line in lines[header_idx + 1:]:
        if not line.strip() or line.startswith("#"):
            continue

        values = [v.strip().strip('"') for v in line.split(",")]
        if len(values) < len(headers):
            continue

        row = dict(zip(headers, values))

        # Parse duration
        duration_ns = 0
        duration_str = row.get("Total Time (ns)", row.get("Total (ns)", "0"))
        try:
            duration_ns = int(float(duration_str.replace(",", "")))
        except (ValueError, TypeError):
            pass

        # Parse average
        avg_ns = 0.0
        avg_str = row.get("Avg (ns)", row.get("Average (ns)", "0"))
        try:
            avg_ns = float(avg_str.replace(",", ""))
        except (ValueError, TypeError):
            pass

        # Parse instances
        instances = 1
        instances_str = row.get("Instances", row.get("Count", "1"))
        try:
            instances = int(instances_str.replace(",", ""))
        except (ValueError, TypeError):
            pass

        kernel = KernelInfo(
            name=row.get("Name", row.get("Kernel Name", "Unknown")),
            duration_ns=duration_ns,
            duration_ms=duration_ns / 1_000_000,
            avg_time_ns=avg_ns,
            instances=instances,
        )
        kernels.append(kernel)

    return kernels


def parse_memory_csv(csv_content: str) -> list[MemoryTransfer]:
    """Parse memory summary CSV from nsys stats.

    Args:
        csv_content: CSV content from nsys stats --report cuda_gpu_mem_time_sum

    Returns:
        List of MemoryTransfer objects
    """
    transfers = []
    lines = csv_content.strip().split("\n")

    # Find header line - look for a line with known CSV header columns
    # The nsys output includes informational lines before the actual CSV
    header_idx = -1
    for i, line in enumerate(lines):
        line_lower = line.lower()
        # Skip comment lines
        if line.startswith("#"):
            continue
        # Check if this looks like a CSV header with expected columns
        if ("time" in line_lower and ("operation" in line_lower or "total" in line_lower)) or \
           ("time (%)" in line_lower) or \
           ("count" in line_lower and "total" in line_lower):
            header_idx = i
            break

    if header_idx < 0 or header_idx >= len(lines) - 1:
        return transfers

    headers = [h.strip().strip('"') for h in lines[header_idx].split(",")]

    for line in lines[header_idx + 1:]:
        if not line.strip() or line.startswith("#"):
            continue

        values = [v.strip().strip('"') for v in line.split(",")]
        if len(values) < len(headers):
            continue

        row = dict(zip(headers, values))

        # Parse duration
        duration_ms = 0.0
        duration_str = row.get("Total Time (ns)", row.get("Total (ns)", "0"))
        try:
            duration_ns = float(duration_str.replace(",", ""))
            duration_ms = duration_ns / 1_000_000
        except (ValueError, TypeError):
            pass

        # Parse size
        size_bytes = 0
        size_str = row.get("Total (bytes)", row.get("Size (bytes)", "0"))
        try:
            size_bytes = int(float(size_str.replace(",", "")))
        except (ValueError, TypeError):
            pass

        # Parse instances
        instances = 1
        instances_str = row.get("Instances", row.get("Count", "1"))
        try:
            instances = int(instances_str.replace(",", ""))
        except (ValueError, TypeError):
            pass

        # Compute throughput
        throughput_gb_s = 0.0
        if duration_ms > 0 and size_bytes > 0:
            duration_s = duration_ms / 1000
            throughput_gb_s = (size_bytes / 1e9) / duration_s

        transfer = MemoryTransfer(
            operation=row.get("Operation", row.get("Name", "Unknown")),
            duration_ms=duration_ms,
            size_bytes=size_bytes,
            throughput_gb_s=throughput_gb_s,
            instances=instances,
        )
        transfers.append(transfer)

    return transfers


def analyze_report(
    report_path: str | Path,
    nsys_path: str | None = None,
) -> NSYSParseResult:
    """Analyze NSYS report file.

    Args:
        report_path: Path to .nsys-rep file
        nsys_path: Optional path to nsys executable (auto-detected if not provided)

    Returns:
        NSYSParseResult with analysis results
    """
    # Find nsys
    if nsys_path is None:
        nsys_path = find_nsys()

    if nsys_path is None:
        return NSYSParseResult(
            success=False,
            error="NSYS not installed. Cannot analyze locally.",
        )

    # Validate report exists
    report_path = Path(report_path)
    if not report_path.exists():
        return NSYSParseResult(
            success=False,
            error=f"Report file not found: {report_path}",
        )

    if not str(report_path).endswith(".nsys-rep"):
        return NSYSParseResult(
            success=False,
            error=f"Invalid file extension. Expected .nsys-rep, got: {report_path.suffix}",
        )

    # Get kernel stats - try new report name first, fall back to legacy
    # Note: Report names changed in nsys 2024.x: gpukernsum -> cuda_gpu_kern_sum
    success, kernel_csv, kernel_err = run_nsys_stats(
        nsys_path, report_path, "cuda_gpu_kern_sum"
    )
    if not success:
        success, kernel_csv, kernel_err = run_nsys_stats(
            nsys_path, report_path, "gpukernsum"
        )
    kernels = parse_kernel_csv(kernel_csv) if success else []

    # Get memory stats - try new report name first, fall back to legacy
    # Note: Report names changed in nsys 2024.x: gpumemtimesum -> cuda_gpu_mem_time_sum
    success, mem_csv, mem_err = run_nsys_stats(
        nsys_path, report_path, "cuda_gpu_mem_time_sum"
    )
    if not success:
        success, mem_csv, mem_err = run_nsys_stats(
            nsys_path, report_path, "gpumemtimesum"
        )
    memory_transfers = parse_memory_csv(mem_csv) if success else []

    # Build summary
    total_kernel_time_ms = sum(k.duration_ms for k in kernels)
    total_mem_time_ms = sum(m.duration_ms for m in memory_transfers)

    summary = NSYSSummary(
        gpu="Unknown",  # Would need to parse report metadata for this
        duration_ms=total_kernel_time_ms + total_mem_time_ms,
        kernel_count=len(kernels),
        memory_transfers=len(memory_transfers),
        total_kernel_time_ms=total_kernel_time_ms,
        total_memory_time_ms=total_mem_time_ms,
    )

    return NSYSParseResult(
        success=True,
        summary=summary,
        kernels=tuple(kernels),
        memory_transfers=tuple(memory_transfers),
    )
