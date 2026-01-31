"""Benchmark script for trace comparison performance.

Measures performance for:
- JSON parsing (orjson)
- Phase lookup (binary search)
- Full trace loading

Run with:
    python -m tests.trace_compare.benchmark_trace_compare
"""

import json
import time
from pathlib import Path

import orjson

from wafer_core.lib.trace_compare.loader import load_trace, _process_events_single_pass


TRACE_EXAMPLES_DIR = Path("/root/wafer/experiments/ian/vllm-trace-compare/examples")
TRACE_FILES = {
    "small": TRACE_EXAMPLES_DIR / "amd_llama.json",
    "medium": TRACE_EXAMPLES_DIR / "nvidia_llama.json",
    "large": TRACE_EXAMPLES_DIR / "amd_oss.json",
}


def benchmark_json_parsing(file_path: Path, num_runs: int = 3) -> dict[str, float]:
    """Benchmark JSON parsing: orjson vs stdlib json."""
    print(f"\n📊 Benchmarking JSON parsing: {file_path.name}")
    print(f"   File size: {file_path.stat().st_size / (1024**2):.1f} MB")
    
    with open(file_path, "rb") as f:
        content_bytes = f.read()
    content_str = content_bytes.decode("utf-8")
    
    orjson_times = []
    for _ in range(num_runs):
        start = time.perf_counter()
        _ = orjson.loads(content_bytes)
        orjson_times.append(time.perf_counter() - start)
    
    json_times = []
    for _ in range(num_runs):
        start = time.perf_counter()
        _ = json.loads(content_str)
        json_times.append(time.perf_counter() - start)
    
    orjson_avg = sum(orjson_times) / len(orjson_times)
    json_avg = sum(json_times) / len(json_times)
    speedup = json_avg / orjson_avg if orjson_avg > 0 else 0
    
    print(f"   orjson:     {orjson_avg:.2f}s (avg of {num_runs} runs)")
    print(f"   stdlib json: {json_avg:.2f}s (avg of {num_runs} runs)")
    print(f"   Speedup:    {speedup:.1f}x")
    
    return {
        "orjson_time": orjson_avg,
        "json_time": json_avg,
        "speedup": speedup,
    }


def benchmark_phase_lookup(file_path: Path, num_samples: int = 10000) -> dict[str, float]:
    """Benchmark phase lookup using binary search."""
    print(f"\n📊 Benchmarking phase lookup: {file_path.name}")
    
    with open(file_path, "rb") as f:
        trace = orjson.loads(f.read())
    
    events = trace.get("traceEvents", [])
    pass_result = _process_events_single_pass(events, include_stacks=False)
    sorted_phases = sorted(pass_result.phases, key=lambda p: p["ts_start"])
    
    import bisect
    phase_starts = [p["ts_start"] for p in sorted_phases]
    phase_types = [p["type"] for p in sorted_phases]
    phase_ends = [p["ts_end"] for p in sorted_phases]
    
    def _get_phase_binary(ts: int) -> str:
        if not phase_starts:
            return "decode"
        idx = bisect.bisect_right(phase_starts, ts) - 1
        if idx >= 0 and phase_starts[idx] <= ts <= phase_ends[idx]:
            return phase_types[idx]
        return "decode"
    
    kernel_timestamps = [
        ev["ts"] for ev in pass_result.kernel_events[:num_samples]
    ]
    
    start = time.perf_counter()
    for ts in kernel_timestamps:
        _ = _get_phase_binary(ts)
    binary_time = time.perf_counter() - start
    
    print(f"   Samples:    {len(kernel_timestamps)} kernel timestamps")
    print(f"   Binary:     {binary_time:.3f}s")
    
    return {
        "binary_time": binary_time,
        "samples": len(kernel_timestamps),
    }


def benchmark_load_trace(file_path: Path, num_runs: int = 2) -> dict[str, float]:
    """Benchmark full trace loading."""
    print(f"\n📊 Benchmarking full trace loading: {file_path.name}")
    
    opt_times = []
    for _ in range(num_runs):
        start = time.perf_counter()
        _ = load_trace(file_path, include_stacks=True)
        opt_times.append(time.perf_counter() - start)
    
    opt_avg = sum(opt_times) / len(opt_times)
    
    print(f"   Load time:  {opt_avg:.2f}s (avg of {num_runs} runs)")
    
    return {
        "load_time": opt_avg,
    }


def main() -> None:
    """Run all benchmarks."""
    print("=" * 70)
    print("Trace Compare Performance Benchmarks")
    print("=" * 70)
    
    available_files = {name: path for name, path in TRACE_FILES.items() if path.exists()}
    
    if not available_files:
        print("\n❌ No trace files found in:", TRACE_EXAMPLES_DIR)
        return
    
    print(f"\n✅ Found {len(available_files)} trace file(s)")
    
    test_file = min(available_files.values(), key=lambda p: p.stat().st_size)
    print(f"\n📁 Using test file: {test_file.name} ({test_file.stat().st_size / (1024**2):.1f} MB)")
    
    results = {}
    
    try:
        results["json_parsing"] = benchmark_json_parsing(test_file, num_runs=3)
    except Exception as e:
        print(f"   ❌ Error: {e}")
        results["json_parsing"] = None
    
    try:
        results["phase_lookup"] = benchmark_phase_lookup(test_file, num_samples=10000)
    except Exception as e:
        print(f"   ❌ Error: {e}")
        results["phase_lookup"] = None
    
    try:
        results["load_trace"] = benchmark_load_trace(test_file, num_runs=1)
    except Exception as e:
        print(f"   ❌ Error: {e}")
        results["load_trace"] = None
    
    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)
    
    json_parsing = results.get("json_parsing")
    if json_parsing is not None:
        print(f"JSON Parsing Speedup: {json_parsing['speedup']:.1f}x")
    
    phase_lookup = results.get("phase_lookup")
    if phase_lookup is not None:
        print(f"Phase Lookup: {phase_lookup['binary_time']:.3f}s ({phase_lookup['samples']} samples)")
    
    load_trace_result = results.get("load_trace")
    if load_trace_result is not None:
        print(f"Full Load Time: {load_trace_result['load_time']:.2f}s")
    
    print("\n✅ Benchmarks complete!")


if __name__ == "__main__":
    main()
