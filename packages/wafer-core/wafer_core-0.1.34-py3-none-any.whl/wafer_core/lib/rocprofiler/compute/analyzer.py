"""Analysis and parsing for ROCprofiler-Compute output files.

Follows Wafer-391: ROCprofiler Tools Architecture.
"""

import pandas as pd
import yaml
from pathlib import Path
from typing import Optional, Any
from wafer_core.lib.rocprofiler.compute.types import (
    AnalysisResult,
    KernelStats,
    RooflineData,
)


def parse_workload(workload_path: str) -> AnalysisResult:
    """Parse a complete rocprof-compute workload directory.

    Reads all relevant files:
    - sysinfo.csv: System and GPU info
    - pmc_kernel_top.csv: Top kernel statistics
    - roofline_*.csv: Roofline data (if available)
    - Analysis YAML files

    Args:
        workload_path: Path to workload directory

    Returns:
        AnalysisResult with parsed data

    Example:
        >>> result = parse_workload("./workloads/vcopy_test")
        >>> if result.success:
        ...     for kernel in result.kernels:
        ...         print(f"{kernel.kernel_name}: {kernel.duration_ns}ns")
    """
    wl_path = Path(workload_path)
    if not wl_path.exists():
        return AnalysisResult(
            success=False,
            error=f"Workload path not found: {workload_path}"
        )

    try:
        # rocprof-compute may create subdirectories by GPU (e.g., MI300X_A1/)
        # Try to find sysinfo.csv in subdirectories if not at top level
        sysinfo_path = wl_path / "sysinfo.csv"
        architecture = None
        data_dir = wl_path

        if not sysinfo_path.exists():
            # Look in subdirectories
            for subdir in wl_path.iterdir():
                if subdir.is_dir():
                    potential_sysinfo = subdir / "sysinfo.csv"
                    if potential_sysinfo.exists():
                        sysinfo_path = potential_sysinfo
                        data_dir = subdir
                        break

        if sysinfo_path.exists():
            sysinfo = pd.read_csv(sysinfo_path)
            if "gpu_arch" in sysinfo.columns:
                architecture = sysinfo["gpu_arch"].iloc[0]

        # Parse kernel stats - try multiple sources in order:
        # 1. pmc_kernel_top.csv (if rocprof-compute analyze was run)
        # 2. SQ_*.csv files with timing data (always available from profile)
        kernels = []
        kernel_top_paths = [
            wl_path / "pmc_kernel_top.csv",
            data_dir / "pmc_kernel_top.csv",
        ]

        # Try pmc_kernel_top.csv first (summarized data)
        for kernel_top_path in kernel_top_paths:
            if kernel_top_path.exists():
                kernel_df = pd.read_csv(kernel_top_path)
                for idx, row in kernel_df.iterrows():
                    # rocprof-compute format uses different column names
                    kernel_name = row.get("Kernel_Name", row.get("KernelName", "unknown"))

                    # Count or Dispatches
                    dispatches = int(row.get("Count", row.get("Dispatches", 0)))

                    # Duration can be Sum(ns), Mean(ns), or Duration(ns)
                    duration_ns = None
                    if "Sum(ns)" in row:
                        duration_ns = float(row["Sum(ns)"])
                    elif "Duration(ns)" in row:
                        duration_ns = float(row["Duration(ns)"])
                    elif "Mean(ns)" in row:
                        # Use mean * count to get total
                        duration_ns = float(row["Mean(ns)"]) * dispatches

                    kernels.append(KernelStats(
                        kernel_id=int(row.get("Index", idx)),
                        kernel_name=kernel_name,
                        dispatches=dispatches,
                        duration_ns=duration_ns,
                        gpu_util=float(row.get("GPU_Util(%)", 0)) if "GPU_Util(%)" in row else None,
                        memory_bw=float(row.get("Memory_BW(GB/s)", 0)) if "Memory_BW(GB/s)" in row else None,
                        metrics={k: v for k, v in row.items() if k not in ["Index", "Kernel_Name", "KernelName", "Dispatches", "Count"]}
                    ))
                break  # Found kernels, don't check other locations

        # Fallback: Parse SQ_*.csv files with timing data (if pmc_kernel_top.csv not found)
        if not kernels:
            # Try SQ_LEVEL_WAVES.csv or other SQ files with Start/End timestamps
            timing_file_patterns = [
                "SQ_LEVEL_WAVES.csv",
                "SQ_IFETCH_LEVEL.csv",
                "SQ_INST_LEVEL_SMEM.csv",
            ]

            for pattern in timing_file_patterns:
                for potential_path in [wl_path / pattern, data_dir / pattern]:
                    if potential_path.exists():
                        try:
                            timing_df = pd.read_csv(potential_path)
                            # Check if this file has timing columns
                            if "Start_Timestamp" not in timing_df.columns or "End_Timestamp" not in timing_df.columns:
                                continue

                            # Aggregate by kernel name
                            kernel_groups = timing_df.groupby("Kernel_Name", dropna=False)
                            for kernel_idx, (kernel_name, group) in enumerate(kernel_groups):
                                # Calculate duration for each dispatch and sum
                                durations = (group["End_Timestamp"] - group["Start_Timestamp"])
                                total_duration_ns = durations.sum()
                                dispatches = len(group)

                                kernels.append(KernelStats(
                                    kernel_id=kernel_idx,
                                    kernel_name=str(kernel_name),
                                    dispatches=dispatches,
                                    duration_ns=float(total_duration_ns),
                                    gpu_util=None,
                                    memory_bw=None,
                                    metrics={}
                                ))

                            if kernels:
                                break  # Found timing data, stop searching
                        except Exception:
                            continue  # Try next file

                if kernels:
                    break  # Found timing data, stop searching patterns

        # Parse roofline data (check both locations)
        # Note: roofline.csv contains device capabilities (bandwidth/compute peaks),
        # not per-kernel AI/performance points. Per-kernel roofline data is only
        # generated by running rocprof-compute analyze (not available in CSV form).
        # We skip parsing this file as it doesn't contain kernel-specific data.
        roofline = []
        for roof_file in list(wl_path.glob("roofline*.csv")) + list(data_dir.glob("roofline*.csv")):
            if roof_file.exists():
                try:
                    roof_df = pd.read_csv(roof_file)
                    # Check if this has per-kernel data (Kernel_Name column)
                    if "Kernel_Name" in roof_df.columns or "KernelName" in roof_df.columns:
                        for _, row in roof_df.iterrows():
                            roofline.append(RooflineData(
                                kernel_name=row.get("Kernel_Name", row.get("KernelName", "unknown")),
                                ai=float(row.get("AI", row.get("Avg AI", 0))),
                                perf=float(row.get("Perf(GFLOPS)", row.get("Avg Perf", 0))),
                                roof_type=roof_file.stem.replace("roofline_", "").replace("roofline", "")
                            ))
                    # Otherwise, it's device capabilities - skip for now
                    # (could add DeviceCapabilities type in future if needed)
                except Exception:
                    # Skip malformed roofline files
                    continue

        # Generate summary
        summary = {
            "total_kernels": len(kernels),
            "total_duration_ns": sum(k.duration_ns or 0 for k in kernels),
            "architecture": architecture,
            "has_roofline": len(roofline) > 0,
        }

        return AnalysisResult(
            success=True,
            workload_path=str(wl_path),
            architecture=architecture,
            kernels=kernels if kernels else None,
            roofline=roofline if roofline else None,
            summary=summary
        )

    except Exception as e:
        return AnalysisResult(
            success=False,
            workload_path=str(wl_path),
            error=str(e)
        )


def parse_csv(csv_path: str) -> pd.DataFrame:
    """Parse a rocprof-compute CSV file.

    Args:
        csv_path: Path to CSV file

    Returns:
        DataFrame with parsed data

    Raises:
        FileNotFoundError: If CSV file doesn't exist
        pd.errors.ParserError: If CSV parsing fails
    """
    return pd.read_csv(csv_path)


def parse_yaml(yaml_path: str) -> dict[str, Any]:
    """Parse a rocprof-compute YAML config file.

    Args:
        yaml_path: Path to YAML file

    Returns:
        Dictionary with parsed YAML data

    Raises:
        FileNotFoundError: If YAML file doesn't exist
        yaml.YAMLError: If YAML parsing fails
    """
    with open(yaml_path, 'r') as f:
        return yaml.safe_load(f)
