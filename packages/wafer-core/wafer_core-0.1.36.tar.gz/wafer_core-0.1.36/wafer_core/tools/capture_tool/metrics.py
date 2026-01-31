"""Metrics extraction functions for capture tool."""

import logging
import os
import platform
import re
import subprocess
from pathlib import Path

import trio

from wafer_core.tools.capture_tool.dtypes import MetricsResult

logger = logging.getLogger(__name__)

METRIC_PATTERNS = [
    (r"latency[:\s]+(\d+\.?\d*)\s*(us|μs|microseconds?)", "latency_us", 1.0),
    (r"latency[:\s]+(\d+\.?\d*)\s*(ms|milliseconds?)", "latency_us", 1000.0),
    (r"latency[:\s]+(\d+\.?\d*)\s*(s|seconds?)", "latency_us", 1_000_000.0),
    (r"throughput[:\s]+(\d+\.?\d*)\s*(gb/s|gbps)", "throughput_gb_s", 1.0),
    (r"throughput[:\s]+(\d+\.?\d*)\s*(mb/s|mbps)", "throughput_gb_s", 0.001),
    (r"throughput[:\s]+(\d+\.?\d*)\s*(tb/s|tbps)", "throughput_gb_s", 1000.0),
    (r"bandwidth[:\s]+(\d+\.?\d*)\s*(gb/s|gbps)", "bandwidth_gb_s", 1.0),
    (r"bandwidth[:\s]+(\d+\.?\d*)\s*(mb/s|mbps)", "bandwidth_gb_s", 0.001),
    (r"bandwidth[:\s]+(\d+\.?\d*)\s*(tb/s|tbps)", "bandwidth_gb_s", 1000.0),
    (r"speedup[:\s]+(\d+\.?\d*)x?", "speedup", 1.0),
    (r"(\d+\.?\d*)\s*(tflops|tflop/s)", "tflops", 1.0),
    (r"(\d+\.?\d*)\s*(gflops|gflop/s)", "tflops", 0.001),
    (r"time[:\s]+(\d+\.?\d*)\s*(ms|milliseconds?)", "time_ms", 1.0),
    (r"time[:\s]+(\d+\.?\d*)\s*(s|seconds?)", "time_ms", 1000.0),
    (r"time[:\s]+(\d+\.?\d*)\s*(us|μs|microseconds?)", "time_ms", 0.001),
    (r"kernel\s+time[:\s]+(\d+\.?\d*)\s*(ms|milliseconds?)", "kernel_time_ms", 1.0),
    (r"kernel\s+time[:\s]+(\d+\.?\d*)\s*(us|μs|microseconds?)", "kernel_time_ms", 0.001),
    (r"memory[:\s]+(\d+\.?\d*)\s*(gb|gigabytes?)", "memory_gb", 1.0),
    (r"memory[:\s]+(\d+\.?\d*)\s*(mb|megabytes?)", "memory_gb", 0.001),
    (r"efficiency[:\s]+(\d+\.?\d*)%?", "efficiency_percent", 1.0),
    (r"error[:\s]+(\d+\.?\d*)%?", "error_percent", 1.0),
    (r"(mse|rmse|mae)[:\s]+(\d+\.?\d*)", lambda m: m.group(1).lower(), 1.0),
]


def extract_metrics_from_stdout(stdout: str) -> dict[str, float]:
    """Extract metrics from command stdout using regex patterns."""
    logger.debug("Extracting metrics from stdout")

    metrics: dict[str, float] = {}
    stdout_lower = stdout.lower()

    for pattern_tuple in METRIC_PATTERNS:
        if len(pattern_tuple) == 3:
            pattern, metric_name, multiplier = pattern_tuple
        else:
            continue

        regex = re.compile(pattern, re.IGNORECASE | re.MULTILINE)

        for match in regex.finditer(stdout_lower):
            try:
                value_str = match.group(1)
                value = float(value_str)

                if callable(metric_name):
                    name = metric_name(match)
                else:
                    name = metric_name

                if callable(multiplier):
                    value = multiplier(value)
                else:
                    value *= multiplier

                metrics[name] = value
                logger.debug(f"Extracted metric: {name} = {value}")

            except (ValueError, IndexError) as e:
                logger.debug(f"Failed to parse metric from match: {e}")
                continue

    logger.info(f"Extracted {len(metrics)} metrics from stdout")
    return metrics


async def detect_ncu_files(working_dir: Path) -> list[Path]:
    """Detect NCU profile files in working directory."""
    logger.debug(f"Detecting NCU files in: {working_dir}")

    def _scan() -> list[Path]:
        ncu_files: list[Path] = []
        for file in working_dir.rglob("*.ncu-rep"):
            try:
                rel_path = file.relative_to(working_dir)
                ncu_files.append(rel_path)
            except ValueError:
                continue
        return ncu_files

    ncu_files = await trio.to_thread.run_sync(_scan)
    logger.info(f"Found {len(ncu_files)} NCU profile files")
    return ncu_files


async def parse_ncu_file(ncu_file: Path) -> dict[str, float]:
    """Parse NCU profile file and extract metrics."""
    logger.debug(f"Parsing NCU file: {ncu_file}")

    def _parse_ncu_file_sync(file_path: Path) -> dict[str, float]:
        import shutil

        def find_ncu() -> str | None:
            ncu = shutil.which("ncu")
            if ncu:
                return ncu

            system = platform.system().lower()
            ncu_paths = {
                "linux": [
                    "/usr/local/cuda/bin/ncu",
                    "/opt/nvidia/nsight-compute/ncu",
                    "/usr/bin/ncu",
                    "/usr/local/bin/ncu",
                ],
                "darwin": [
                    "/Applications/NVIDIA Nsight Compute.app/Contents/MacOS/ncu",
                    "/usr/local/cuda/bin/ncu",
                ],
                "windows": [
                    r"C:\Program Files\NVIDIA Corporation\Nsight Compute\ncu.exe",
                    r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.0\bin\ncu.exe",
                ],
            }

            plat = "linux" if system == "linux" else "darwin" if system == "darwin" else "windows"
            for path_str in ncu_paths.get(plat, []):
                if os.path.isfile(path_str) and os.access(path_str, os.X_OK):
                    return path_str

            return None

        ncu_path = find_ncu()
        if not ncu_path:
            logger.warning(
                "NCU not installed - skipping NCU metric extraction. "
                "Install from: https://developer.nvidia.com/nsight-compute"
            )
            return {}

        try:
            session_result = subprocess.run(
                [ncu_path, "--import", str(file_path), "--page", "session"],
                capture_output=True,
                text=True,
                timeout=300,
            )

            details_result = subprocess.run(
                [ncu_path, "--import", str(file_path), "--page", "details"],
                capture_output=True,
                text=True,
                timeout=300,
            )

            metrics = {}
            details_lines = details_result.stdout.split("\n")
            current_kernel_metrics: dict[str, float] = {}

            for i, line in enumerate(details_lines):
                stripped = line.strip()

                if (
                    line.startswith("  ")
                    and not line.startswith("    ")
                    and "Context" in line
                    and "Device" in line
                ):
                    if current_kernel_metrics:
                        metrics = current_kernel_metrics
                        break
                    current_kernel_metrics = {}

                if "          " in line:
                    parts = line.split()
                    if len(parts) < 2:
                        continue

                    if "Duration" in stripped and "us" in stripped:
                        try:
                            value = float(parts[-1].replace(",", ""))
                            current_kernel_metrics["ncu_duration_us"] = value
                            current_kernel_metrics["ncu_duration_ms"] = value / 1000.0
                        except (ValueError, IndexError):
                            pass

                    elif "Memory Throughput" in stripped and "%" in stripped:
                        try:
                            value = float(parts[-1].replace(",", ""))
                            current_kernel_metrics["ncu_memory_throughput_pct"] = value
                        except (ValueError, IndexError):
                            pass

                    elif (
                        "Compute (SM) Throughput" in stripped or "Compute Throughput" in stripped
                    ):
                        try:
                            value = float(parts[-1].replace(",", ""))
                            current_kernel_metrics["ncu_compute_throughput_pct"] = value
                        except (ValueError, IndexError):
                            pass

                    elif "Achieved Occupancy" in stripped and "%" in stripped:
                        try:
                            value = float(parts[-1].replace(",", ""))
                            current_kernel_metrics["ncu_occupancy_pct"] = value
                        except (ValueError, IndexError):
                            pass

                if "Est. Speedup:" in stripped or "Est. Local Speedup:" in stripped:
                    speedup_match = re.search(r"Speedup:\s*([\d.]+)%", stripped)
                    if speedup_match:
                        try:
                            speedup = float(speedup_match.group(1))
                            if "ncu_estimated_speedup_pct" not in current_kernel_metrics:
                                current_kernel_metrics["ncu_estimated_speedup_pct"] = speedup
                            else:
                                current_kernel_metrics["ncu_estimated_speedup_pct"] = max(
                                    current_kernel_metrics["ncu_estimated_speedup_pct"], speedup
                                )
                        except (ValueError, IndexError):
                            pass

            if current_kernel_metrics and not metrics:
                metrics = current_kernel_metrics

            if metrics:
                logger.info(
                    f"Extracted {len(metrics)} NCU metrics: "
                    f"duration={metrics.get('ncu_duration_us', 0):.1f}us, "
                    f"occupancy={metrics.get('ncu_occupancy_pct', 0):.1f}%"
                )
            else:
                logger.warning("No metrics extracted from NCU output")

            return metrics

        except subprocess.TimeoutExpired:
            logger.error("NCU parsing timed out (300s limit)")
            return {}
        except Exception as e:
            logger.error(f"Failed to parse NCU file: {e}")
            return {}

    try:
        metrics = await trio.to_thread.run_sync(_parse_ncu_file_sync, ncu_file)
        return metrics
    except Exception as e:
        logger.error(f"NCU parsing failed: {e}")
        return {}


async def collect_all_metrics(
    stdout: str, working_dir: Path
) -> MetricsResult:
    """Collect all available metrics from stdout and NCU profiles."""
    logger.info("Collecting all metrics")

    stdout_metrics = extract_metrics_from_stdout(stdout)
    ncu_files = await detect_ncu_files(working_dir)

    ncu_metrics = None
    ncu_file_path = None

    if ncu_files:
        ncu_file_path = working_dir / ncu_files[0]
        logger.info(f"Parsing NCU file: {ncu_file_path}")

        try:
            ncu_metrics = await parse_ncu_file(ncu_file_path)
        except Exception as e:
            logger.error(f"Failed to parse NCU file: {e}")
            ncu_metrics = None

    return MetricsResult(
        stdout_metrics=stdout_metrics,
        ncu_metrics=ncu_metrics,
        ncu_file_path=ncu_file_path,
    )
