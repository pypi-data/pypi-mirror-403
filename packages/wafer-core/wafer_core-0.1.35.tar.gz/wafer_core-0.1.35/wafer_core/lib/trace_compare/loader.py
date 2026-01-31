"""Trace loading and parsing logic.

Loads JSON trace files from AMD/NVIDIA profilers and extracts kernel execution data,
Python call stacks, CPU operator mappings, and layer correlations.
"""

import bisect
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import orjson
import pandas as pd

from .classifier import classify


@dataclass
class SinglePassResult:
    """Collected data from single-pass event processing."""
    cpu_op_mapping: dict[int, str] = field(default_factory=dict)
    python_intervals: list[tuple[int, int, int, int | None, str]] = field(default_factory=list)
    # Raw python events for lazy python_by_id construction (built on-demand)
    python_events_raw: list[dict[str, Any]] = field(default_factory=list)
    phases: list[dict[str, Any]] = field(default_factory=list)
    correlation_groups: dict[int, dict[str, Any]] = field(default_factory=lambda: defaultdict(
        lambda: {"count": 0, "has_attention": False, "has_ffn": False}
    ))
    kernel_events: list[dict[str, Any]] = field(default_factory=list)
    # Lazily built when needed for stack resolution
    _python_by_id: dict[int, dict[str, Any]] | None = field(default=None)

    @property
    def python_by_id(self) -> dict[int, dict[str, Any]]:
        """Lazily build python_by_id from raw events on first access."""
        if self._python_by_id is None:
            self._python_by_id = {}
            for ev in self.python_events_raw:
                args = ev.get("args")
                py_id = args.get("Python id") if args else None
                if py_id is not None:
                    self._python_by_id[py_id] = {
                        "name": ev["name"],
                        "parent_id": args.get("Python parent id") if args else None,
                    }
        return self._python_by_id


def extract_layer_mapping(events: list[dict[str, Any]], platform: str) -> dict[int, int]:
    """Extract correlation ID to layer number mapping.

    vLLM's execution graph creates large correlation groups for full transformer layers.
    Each layer's forward pass (norm + attention + FFN) gets grouped under one correlation ID,
    containing 200-400 kernels depending on batch size and sequence length.

    We identify layers as correlation groups with many kernels (70+), which filters out
    individual operations like sampling, logit processing, etc.

    Args:
        events: List of trace events
        platform: 'AMD' or 'NVIDIA'

    Returns:
        Dict mapping correlation ID to layer number
    """
    # Group kernels by correlation ID
    correlation_groups = defaultdict(
        lambda: {"count": 0, "has_attention": False, "has_ffn": False}
    )

    for ev in events:
        if ev.get("cat") != "kernel":
            continue

        corr_id = ev.get("args", {}).get("correlation")
        if corr_id is None:
            continue

        kernel_name = ev.get("name", "").lower()

        # Track what operations this correlation contains
        correlation_groups[corr_id]["count"] += 1
        if "attention" in kernel_name or "fmha" in kernel_name:
            correlation_groups[corr_id]["has_attention"] = True
        if any(x in kernel_name for x in ["cijk_", "nvjet", "wvsplitk", "gemm"]):
            correlation_groups[corr_id]["has_ffn"] = True

    # Map correlation IDs to layer numbers
    # Transformer layers have many kernels AND contain both attention and FFN ops
    correlation_to_layer = {}
    layer_num = 0

    for corr_id in sorted(correlation_groups.keys()):
        group = correlation_groups[corr_id]

        # Identify complete transformer layers by their characteristics:
        # - Has attention operations (self-attention or cross-attention)
        # - Has FFN operations (feed-forward network)
        # - Has sufficient kernel count (70+): typical transformer block has ~80-100 kernels
        #   including attention QKV projections, softmax, output projection, FFN layers,
        #   normalization, and elementwise ops. This threshold filters out:
        #   - Individual operations (1-10 kernels)
        #   - Sampling/generation steps (20-40 kernels)
        #   - Partial layer executions
        is_layer = (
            group["count"] >= 70 and group["has_attention"] and group["has_ffn"]
        )

        if is_layer:
            correlation_to_layer[corr_id] = layer_num
            layer_num += 1

    return correlation_to_layer


def _process_events_single_pass(
    events: list[dict[str, Any]],
) -> SinglePassResult:
    """Process all events in a single iteration.

    Optimizations applied:
    - Cache list.append methods for 2-3x speedup on hot paths
    - Store raw python events, build python_by_id lazily (only ~48 lookups due to caching)
    - Local variable caching for frequently accessed attributes

    Args:
        events: List of trace events
    """
    result = SinglePassResult()
    correlation_groups: dict[int, dict[str, Any]] = defaultdict(
        lambda: {"count": 0, "has_attention": False, "has_ffn": False}
    )

    # Cache list.append methods for faster appending (measured 2-3x speedup)
    kernel_append = result.kernel_events.append
    python_interval_append = result.python_intervals.append
    python_raw_append = result.python_events_raw.append
    phase_append = result.phases.append
    cpu_op_mapping = result.cpu_op_mapping

    for ev in events:
        cat = ev.get("cat")

        if cat == "kernel":
            args = ev.get("args")
            corr_id = args.get("correlation") if args else None
            if corr_id is not None:
                kernel_name = ev.get("name", "").lower()
                grp = correlation_groups[corr_id]
                grp["count"] += 1
                if "attention" in kernel_name or "fmha" in kernel_name:
                    grp["has_attention"] = True
                if "cijk_" in kernel_name or "nvjet" in kernel_name or "wvsplitk" in kernel_name or "gemm" in kernel_name:
                    grp["has_ffn"] = True
            kernel_append(ev)

        elif cat == "cpu_op":
            args = ev.get("args")
            ext_id = args.get("External id") if args else None
            if ext_id is not None:
                cpu_op_mapping[ext_id] = ev.get("name", "")

        elif cat == "python_function":
            # Store raw event for lazy python_by_id construction
            python_raw_append(ev)
            # Build interval tuple for binary search
            args = ev.get("args")
            py_id = args.get("Python id") if args else None
            ts = ev["ts"]
            dur = ev.get("dur", 0)
            python_interval_append((ts, ts + dur, dur, py_id, ev["name"]))

        elif cat == "user_annotation":
            name = ev.get("name", "")
            if name.startswith("execute_context"):
                tokens = 0
                parts = name.split("_")
                for i, p in enumerate(parts):
                    if i > 0 and parts[i-1] == "context" and "(" in p and ")" in p:
                        try:
                            tokens = int(p.split("(")[1].split(")")[0])
                            break
                        except Exception:
                            pass
                is_prefill = tokens >= 1024 and "generation_0" in name
                phase_append({
                    "type": "prefill" if is_prefill else "decode",
                    "ts_start": ev["ts"],
                    "ts_end": ev["ts"] + ev["dur"],
                })

    if result.python_intervals:
        result.python_intervals.sort()

    result.correlation_groups = dict(correlation_groups)

    return result


def _build_python_stack_index(
    events: list[dict[str, Any]],
) -> tuple[list[tuple[int, int, int, int | None, str]], dict[int, dict[str, Any]]]:
    """Build Python call stack index for kernels.

    Args:
        events: List of trace events

    Returns:
        Tuple of (python_intervals, python_by_id)
    """
    python_by_id: dict[int, dict[str, Any]] = {}
    python_intervals: list[tuple[int, int, int, int | None, str]] = []

    for ev in events:
        if ev.get("cat") == "python_function":
            py_id = ev.get("args", {}).get("Python id")
            name = ev["name"]
            ts_start = ev["ts"]
            ts_end = ts_start + ev.get("dur", 0)
            duration = ev.get("dur", 0)
            parent_id = ev.get("args", {}).get("Python parent id")

            python_intervals.append((ts_start, ts_end, duration, py_id, name))

            if py_id is not None:
                python_by_id[py_id] = {
                    "name": name,
                    "parent_id": parent_id,
                    "ts_start": ts_start,
                    "ts_end": ts_end,
                    "duration": duration,
                }

    # Sort by start time for efficient binary search
    python_intervals.sort()

    return python_intervals, python_by_id


def _get_python_stack_full(
    timestamp: int,
    python_intervals: list[tuple[int, int, int, int | None, str]],
    python_by_id: dict[int, dict[str, Any]],
) -> tuple[str | None, list[str]]:
    """Get full Python call stack for a kernel launch.

    Args:
        timestamp: Kernel launch timestamp
        python_intervals: Sorted list of Python function intervals
        python_by_id: Mapping of Python ID to function info

    Returns:
        Tuple of (summary_string, full_stack_list)
    """
    # Binary search for Python functions active at this timestamp
    idx = bisect.bisect_right(
        python_intervals, (timestamp, float("inf"), float("inf"), None, "")
    )

    # Find active functions
    active_funcs = []
    for i in range(idx - 1, max(0, idx - 1000), -1):
        ts_start, ts_end, duration, py_id, name = python_intervals[i]
        if ts_start <= timestamp <= ts_end:
            active_funcs.append((duration, py_id, name))
        if ts_end < timestamp - 1000000:  # 1 second before
            break

    if not active_funcs:
        return None, []

    # Get the innermost (most specific) function
    active_funcs.sort()
    leaf_duration, leaf_id, leaf_name = active_funcs[0]

    # Walk up parent chain to get FULL stack
    full_stack = []
    current_id = leaf_id
    visited = set()

    while (
        current_id is not None
        and current_id not in visited
        and current_id in python_by_id
    ):
        func = python_by_id[current_id]
        name = func["name"]
        full_stack.append(name)

        visited.add(current_id)
        current_id = func["parent_id"]

        # Safety limit: prevent infinite loops from circular parent references
        # and bound memory usage. 50 frames is deeper than typical Python stacks.
        if len(full_stack) >= 50:
            break

    # Reverse so it's outermost -> innermost
    full_stack.reverse()

    # Create summary for text output: show the most informative vLLM/model function
    summary = None
    vllm_funcs = [
        f
        for f in full_stack
        if any(x in f.lower() for x in ["vllm/", "model", "<eval_with_key>"])
    ]

    if vllm_funcs:
        # Get innermost vLLM function (most specific)
        summary = vllm_funcs[-1]

        # Check if it's a CUDA graph - add annotation
        if any("torch/cuda/graphs" in f for f in full_stack):
            # Shorten if too long
            if len(summary) > 45:
                parts = summary.split("/")[-1]
                summary = "vllm/..." + parts
            summary = f"{summary} [CUDA graph]"
        elif len(summary) > 53:
            parts = summary.split("/")[-1]
            summary = "vllm/..." + parts
    else:
        # Fallback to innermost function
        summary = leaf_name

    return summary, full_stack


def load_trace(
    file_path: str | Path,
) -> tuple[str, str, dict[str, Any], pd.DataFrame, dict[tuple[str, str], set[str]], dict[int, int]]:
    """Load trace and return platform info, device properties, kernels, patterns, and layer mapping.

    Args:
        file_path: Path to JSON trace file

    Returns:
        Tuple of (platform, gpu_name, device_props, kernel_df, kernel_patterns, layer_mapping)
    """
    with open(file_path, "rb") as f:
        raw = f.read()

    trace = orjson.loads(raw)

    props = trace.get("deviceProperties", [{}])[0]
    is_amd = trace.get("roctracer_version") or props.get("warpSize") == 64
    platform = "AMD" if is_amd else "NVIDIA"
    gpu_name = props.get("name", "MI300X" if is_amd else "Unknown GPU")

    # Extract relevant device properties
    device_props = {
        "name": gpu_name,
        "compute_capability": f"{props.get('computeMajor', 0)}.{props.get('computeMinor', 0)}",
        "total_memory_gb": props.get("totalGlobalMem", 0) / (1024**3),
        "sm_count": props.get("numSms", 0),
        "warp_size": props.get("warpSize", 32),
        "max_threads_per_block": props.get("maxThreadsPerBlock", 0),
        "shared_mem_per_block_kb": props.get("sharedMemPerBlock", 0) / 1024,
    }

    events = trace.get("traceEvents", [])

    # Single-pass event processing for all metadata
    pass_result = _process_events_single_pass(events)

    # Extract layer mapping from correlation groups
    layer_mapping = {
        corr_id: layer_num
        for layer_num, (corr_id, grp) in enumerate(
            (cid, g) for cid, g in sorted(pass_result.correlation_groups.items())
            if g["count"] >= 70 and g["has_attention"] and g["has_ffn"]
        )
    }

    kernel_data = []
    kernel_patterns: dict[tuple[str, str], set[str]] = defaultdict(set)

    # Pre-sort phases for binary search
    sorted_phases = sorted(pass_result.phases, key=lambda p: p["ts_start"])
    phase_starts = [p["ts_start"] for p in sorted_phases]
    phase_types = [p["type"] for p in sorted_phases]
    phase_ends = [p["ts_end"] for p in sorted_phases]

    def _get_phase_for_timestamp(ts: int) -> str:
        """Get phase for a timestamp using binary search. O(log n)."""
        if not phase_starts:
            return "decode"
        idx = bisect.bisect_right(phase_starts, ts) - 1
        if idx >= 0 and phase_starts[idx] <= ts <= phase_ends[idx]:
            return phase_types[idx]
        return "decode"

    # Cache CPU op lookups by kernel name (reduces 779k lookups to ~48)
    cpu_op_cache: dict[str, str | None] = {}

    for ev in pass_result.kernel_events:
        name_raw = ev["name"]
        name = sys.intern(name_raw)  # String interning for memory efficiency
        dur, ts = ev.get("dur", 0), ev["ts"]
        corr_id = ev.get("args", {}).get("correlation")
        ext_id = ev.get("args", {}).get("External id")

        phase = _get_phase_for_timestamp(ts)

        op, pattern = classify(name, platform)
        kernel_patterns[(op.value, phase)].add(pattern)

        # Assign layer number from correlation ID
        layer = layer_mapping.get(corr_id) if corr_id is not None else None

        # Get CPU operator name from external ID, or fallback to Python stack
        cpu_op = pass_result.cpu_op_mapping.get(ext_id) if ext_id is not None else None
        python_stack: list[str] = []

        # If no CPU op via External ID, try Python stack trace with caching
        if cpu_op is None:
            if name in cpu_op_cache:
                cpu_op = cpu_op_cache[name]
            else:
                cpu_op, python_stack = _get_python_stack_full(
                    ts, pass_result.python_intervals, pass_result.python_by_id
                )
                cpu_op_cache[name] = cpu_op

        kernel_data.append(
            {
                "name": name,
                "dur_us": dur,
                "phase": phase,
                "op": op.value,
                "pattern": pattern,
                "layer": layer,
                "correlation": corr_id,
                "cpu_op": cpu_op,
                "python_stack": python_stack,  # Full stack for JSON output
            }
        )

    return platform, gpu_name, device_props, pd.DataFrame(kernel_data), dict(kernel_patterns), layer_mapping
