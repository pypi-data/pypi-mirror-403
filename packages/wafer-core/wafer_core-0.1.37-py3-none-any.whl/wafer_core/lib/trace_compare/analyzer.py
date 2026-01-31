"""Main trace comparison analysis logic.

Compares GPU traces from AMD and NVIDIA platforms, identifying performance differences
at the operation level and layer level.
"""

from collections import defaultdict
from pathlib import Path
from typing import Any

import pandas as pd

from .loader import load_trace


def analyze_traces(
    trace1_path: str | Path,
    trace2_path: str | Path,
    phase_filter: str = "all",
    max_stacks: int = 3,
) -> dict[str, Any]:
    """Analyze two traces and return comparison data.

    Args:
        trace1_path: Path to first trace file
        trace2_path: Path to second trace file
        phase_filter: Filter by phase ('all', 'prefill', or 'decode')
        max_stacks: Maximum number of Python stack traces to collect per operation (0 for unlimited)

    Returns:
        Dictionary containing:
            - metadata: trace info (GPUs, kernel counts, total times, etc.)
            - operations: per-operation comparison data
            - layers: per-layer comparison data (if layers detected)
    """
    # Load traces
    p1, gpu1, dev1, df1, patterns1, layers1 = load_trace(trace1_path)
    p2, gpu2, dev2, df2, patterns2, layers2 = load_trace(trace2_path)

    # Apply phase filter
    if phase_filter != "all":
        df1_filtered = df1[df1["phase"] == phase_filter]
        df2_filtered = df2[df2["phase"] == phase_filter]

        if len(df1_filtered) == 0 and len(df2_filtered) == 0:
            # No data in requested phase - return early with error info
            trace1_phases = {k: int(v) for k, v in df1["phase"].value_counts().items()}
            trace2_phases = {k: int(v) for k, v in df2["phase"].value_counts().items()}
            raise ValueError(
                f"No {phase_filter} phase found. "
                f"Trace1 phases: {trace1_phases}, Trace2 phases: {trace2_phases}"
            )

        df1, df2 = df1_filtered, df2_filtered

    # Pre-compute aggregations for both operations and layers in single pass
    # This is much faster than iterating through filtered dataframes multiple times

    # Group by operation for operation-level analysis
    trace1_by_op = df1.groupby("op").agg({
        "dur_us": ["sum", "mean", "count"],
        "phase": lambda x: set(x.dropna().unique()),
        "cpu_op": lambda x: x.dropna().mode()[0] if len(x.dropna()) > 0 else None,
    })
    trace1_by_op.columns = ["total_us", "avg_us", "count", "phases", "cpu_op"]

    trace2_by_op = df2.groupby("op").agg({
        "dur_us": ["sum", "mean", "count"],
        "phase": lambda x: set(x.dropna().unique()),
        "cpu_op": lambda x: x.dropna().mode()[0] if len(x.dropna()) > 0 else None,
    })
    trace2_by_op.columns = ["total_us", "avg_us", "count", "phases", "cpu_op"]

    # Group by layer for layer-level analysis (only for kernels with layer info)
    df1_layered = df1[df1["layer"].notna()]
    df2_layered = df2[df2["layer"].notna()]

    trace1_by_layer = df1_layered.groupby("layer").agg({
        "dur_us": ["sum", "count"],
    }) if len(df1_layered) > 0 else pd.DataFrame()
    if len(trace1_by_layer) > 0:
        trace1_by_layer.columns = ["total_us", "count"]

    trace2_by_layer = df2_layered.groupby("layer").agg({
        "dur_us": ["sum", "count"],
    }) if len(df2_layered) > 0 else pd.DataFrame()
    if len(trace2_by_layer) > 0:
        trace2_by_layer.columns = ["total_us", "count"]

    # Calculate per-operation statistics
    results: dict[str, Any] = {
        "metadata": {
            "trace1_name": str(trace1_path),
            "trace2_name": str(trace2_path),
            "trace1_platform": p1,
            "trace1_gpu": gpu1,
            "trace1_device": dev1,
            "trace2_platform": p2,
            "trace2_gpu": gpu2,
            "trace2_device": dev2,
            "trace1_kernels": len(df1),
            "trace2_kernels": len(df2),
            "trace1_total_ms": df1["dur_us"].sum() / 1000,
            "trace2_total_ms": df2["dur_us"].sum() / 1000,
            "phase": phase_filter,
            "trace1_layers": len(layers1),
            "trace2_layers": len(layers2),
        },
        "operations": [],
        "layers": [],
    }

    # Per-operation comparison using pre-computed aggregations
    all_ops = set(trace1_by_op.index) | set(trace2_by_op.index)

    # Track if we've already compared RMSNorm variants to avoid duplicate comparisons
    rmsnorm_compared = False

    for op in sorted(all_ops):
        # Use pre-computed aggregations instead of filtering entire dataframes
        has_trace1 = op in trace1_by_op.index
        has_trace2 = op in trace2_by_op.index

        # Handle RMSNorm fusion differences: AMD does RMSNorm+GEMM, NVIDIA does separate RMSNorm
        trace1_op_for_pattern = op  # Operation name to use for AMD pattern lookup
        trace2_op_for_pattern = op  # Operation name to use for NVIDIA pattern lookup
        skip_comparison = False

        if op == "RMSNorm+GEMM" and not has_trace2:
            # Compare AMD's fused version to NVIDIA's separate RMSNorm
            has_trace2 = "RMSNorm" in trace2_by_op.index
            trace2_op_for_pattern = "RMSNorm"  # NVIDIA kernels are stored under 'RMSNorm'
            rmsnorm_compared = True  # Mark that we've compared RMSNorm
        elif op == "RMSNorm" and not has_trace1:
            # Skip this comparison if we already handled it in RMSNorm+GEMM
            if rmsnorm_compared:
                skip_comparison = True
            else:
                # Compare NVIDIA's RMSNorm to AMD's fused version
                has_trace1 = "RMSNorm+GEMM" in trace1_by_op.index
                trace1_op_for_pattern = (
                    "RMSNorm+GEMM"  # AMD kernels are stored under 'RMSNorm+GEMM'
                )
                rmsnorm_compared = True

        if skip_comparison or not (has_trace1 and has_trace2):
            continue

        # Get pre-computed aggregations
        trace1_agg = trace1_by_op.loc[trace1_op_for_pattern]
        trace2_agg = trace2_by_op.loc[trace2_op_for_pattern]

        trace1_avg = trace1_agg["avg_us"]
        trace2_avg = trace2_agg["avg_us"]
        trace1_total = trace1_agg["total_us"] / 1000
        trace2_total = trace2_agg["total_us"] / 1000
        trace1_count = int(trace1_agg["count"])
        trace2_count = int(trace2_agg["count"])
        ratio = trace1_avg / trace2_avg if trace2_avg > 0 else 1
        gap_ms = trace1_total - trace2_total

        # Get kernel patterns using the correct operation names for each platform
        trace1_pattern = list(
            patterns1.get(
                (trace1_op_for_pattern, "decode"),
                patterns1.get((trace1_op_for_pattern, "prefill"), {"unknown"}),
            )
        )[0]
        trace2_pattern = list(
            patterns2.get(
                (trace2_op_for_pattern, "decode"),
                patterns2.get((trace2_op_for_pattern, "prefill"), {"unknown"}),
            )
        )[0]

        # Get CPU operators from pre-computed aggregations
        trace1_cpu_op = trace1_agg["cpu_op"]
        trace2_cpu_op = trace2_agg["cpu_op"]

        # For detailed kernel data and python stacks, we still need to filter (but only when needed)
        trace1_data = df1[df1["op"] == trace1_op_for_pattern]
        trace2_data = df2[df2["op"] == trace2_op_for_pattern]

        # Collect example Python stacks for this operation (for JSON output)
        trace1_python_stacks = []
        stack_limit = None if max_stacks == 0 else max_stacks
        for stack_list in trace1_data["python_stack"].head(stack_limit):
            if stack_list and len(stack_list) > 0:
                trace1_python_stacks.append(stack_list)

        trace2_python_stacks = []
        for stack_list in trace2_data["python_stack"].head(stack_limit):
            if stack_list and len(stack_list) > 0:
                trace2_python_stacks.append(stack_list)

        # Aggregate individual kernels by name for detailed view
        # Group by kernel name and calculate sum/count/avg
        trace1_kernels = trace1_data.groupby("name").agg({"dur_us": ["sum", "count", "mean"]}).reset_index()
        trace1_kernels.columns = ["name", "total_us", "count", "avg_us"]
        trace1_kernels = trace1_kernels.sort_values("total_us", ascending=False)
        trace1_kernels_list = trace1_kernels.to_dict("records")

        trace2_kernels = trace2_data.groupby("name").agg({"dur_us": ["sum", "count", "mean"]}).reset_index()
        trace2_kernels.columns = ["name", "total_us", "count", "avg_us"]
        trace2_kernels = trace2_kernels.sort_values("total_us", ascending=False)
        trace2_kernels_list = trace2_kernels.to_dict("records")

        # Determine status based on TOTAL TIME (gap), not per-call ratio
        # This handles cases where AMD runs fewer operations via fusion.
        # 5ms threshold chosen because:
        # - Filters out measurement noise and minor variations
        # - Represents meaningful performance impact (0.5% of typical 1s inference)
        # - Aligns with human perception of "noticeable" difference
        # - Too small (1ms) creates false positives from variance
        # - Too large (20ms) misses real optimization opportunities
        if gap_ms > 5.0:  # AMD spends >5ms more total time
            status = "slower"
        elif gap_ms < -5.0:  # AMD spends >5ms less total time
            status = "faster"
        else:
            status = "similar"

        # Get phases from pre-computed aggregations
        phases = trace1_agg["phases"] | trace2_agg["phases"]

        results["operations"].append(
            {
                "operation": op,
                "trace1_count": trace1_count,
                "trace2_count": trace2_count,
                "trace1_avg_us": trace1_avg,
                "trace2_avg_us": trace2_avg,
                "trace1_total_ms": trace1_total,
                "trace2_total_ms": trace2_total,
                "ratio": ratio,
                "gap_ms": gap_ms,
                "status": status,
                "trace1_kernel": trace1_pattern,
                "trace2_kernel": trace2_pattern,
                "trace1_cpu_op": trace1_cpu_op,
                "trace2_cpu_op": trace2_cpu_op,
                "trace1_python_stacks": trace1_python_stacks,  # Full stacks for JSON
                "trace2_python_stacks": trace2_python_stacks,
                "trace1_kernels": trace1_kernels_list,  # All individual kernels for JSON
                "trace2_kernels": trace2_kernels_list,  # All individual kernels for JSON
                "phases": sorted(list(phases)) if phases else ["all"],  # For client-side filtering
            }
        )

    # Sort by absolute gap
    results["operations"].sort(key=lambda x: abs(x["gap_ms"]), reverse=True)

    # Layer-wise analysis using pre-computed aggregations
    if len(trace1_by_layer) > 0 or len(trace2_by_layer) > 0:
        # Get all unique layers present in either trace
        all_layers = sorted(set(trace1_by_layer.index) | set(trace2_by_layer.index))

        for layer_num in all_layers:
            has_trace1 = layer_num in trace1_by_layer.index
            has_trace2 = layer_num in trace2_by_layer.index

            if has_trace1 and has_trace2:
                # Layer present in both traces - compare them
                trace1_agg = trace1_by_layer.loc[layer_num]
                trace2_agg = trace2_by_layer.loc[layer_num]

                trace1_total = trace1_agg["total_us"] / 1000
                trace2_total = trace2_agg["total_us"] / 1000
                trace1_count = int(trace1_agg["count"])
                trace2_count = int(trace2_agg["count"])
                ratio = trace1_total / trace2_total if trace2_total > 0 else 1
                gap_ms = trace1_total - trace2_total

                # Determine status (use smaller threshold for layers: 0.1ms or 20% difference)
                threshold_ms = 0.1
                threshold_ratio = 1.2
                if gap_ms > threshold_ms and ratio > threshold_ratio:
                    status = "slower"
                elif gap_ms < -threshold_ms and ratio < (1.0 / threshold_ratio):
                    status = "faster"
                else:
                    status = "similar"

                results["layers"].append(
                    {
                        "layer": int(layer_num),
                        "trace1_kernels": trace1_count,
                        "trace2_kernels": trace2_count,
                        "trace1_total_ms": trace1_total,
                        "trace2_total_ms": trace2_total,
                        "ratio": ratio,
                        "gap_ms": gap_ms,
                        "status": status,
                        "in_both": True,
                    }
                )
            elif has_trace1:
                # Layer only in trace1
                trace1_agg = trace1_by_layer.loc[layer_num]
                trace1_total = trace1_agg["total_us"] / 1000
                trace1_count = int(trace1_agg["count"])

                results["layers"].append(
                    {
                        "layer": int(layer_num),
                        "trace1_kernels": trace1_count,
                        "trace2_kernels": 0,
                        "trace1_total_ms": trace1_total,
                        "trace2_total_ms": 0.0,
                        "ratio": 0.0,
                        "gap_ms": trace1_total,
                        "status": "trace1_only",
                        "in_both": False,
                    }
                )
            elif has_trace2:
                # Layer only in trace2
                trace2_agg = trace2_by_layer.loc[layer_num]
                trace2_total = trace2_agg["total_us"] / 1000
                trace2_count = int(trace2_agg["count"])

                results["layers"].append(
                    {
                        "layer": int(layer_num),
                        "trace1_kernels": 0,
                        "trace2_kernels": trace2_count,
                        "trace1_total_ms": 0.0,
                        "trace2_total_ms": trace2_total,
                        "ratio": 0.0,
                        "gap_ms": -trace2_total,
                        "status": "trace2_only",
                        "in_both": False,
                    }
                )

        # Sort: comparable layers first (by absolute gap), then trace-unique layers
        results["layers"].sort(key=lambda x: (not x["in_both"], abs(x["gap_ms"])), reverse=True)

    return results
