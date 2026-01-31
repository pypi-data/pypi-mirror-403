"""Roofline analysis core logic."""

from dataclasses import dataclass
from enum import Enum

from wafer_core.roofline.gpu_specs import GpuSpec, get_gpu_spec


class Bottleneck(Enum):
    MEMORY = "memory"
    COMPUTE = "compute"


class Dtype(Enum):
    FP64 = "fp64"
    FP32 = "fp32"
    FP16 = "fp16"
    BF16 = "bf16"
    FP8 = "fp8"
    INT8 = "int8"


@dataclass(frozen=True)
class RooflineResult:
    # Inputs
    gpu: GpuSpec
    dtype: Dtype
    bytes_moved: float  # bytes
    flops: float
    actual_time_s: float

    # Derived - arithmetic intensity
    arithmetic_intensity: float  # FLOP/byte

    # Derived - theoretical limits
    peak_bandwidth_bytes_per_s: float
    peak_flops_per_s: float
    ridge_point: float  # FLOP/byte where compute = memory

    # Derived - bottleneck
    bottleneck: Bottleneck

    # Derived - theoretical time (based on bottleneck)
    memory_bound_time_s: float  # time if perfectly memory bound
    compute_bound_time_s: float  # time if perfectly compute bound
    theoretical_time_s: float  # max of the two (the actual limit)

    # Derived - efficiency
    efficiency_pct: float  # theoretical_time / actual_time * 100

    def format_report(self) -> str:
        """Format a human-readable roofline report."""
        lines = []

        lines.append(f"GPU: {self.gpu.name}")
        lines.append(f"Dtype: {self.dtype.value.upper()}")
        lines.append("")

        # Workload
        lines.append("Workload:")
        lines.append(f"  Bytes moved: {_fmt_bytes(self.bytes_moved)}")
        lines.append(f"  FLOPs: {_fmt_flops(self.flops)}")
        lines.append(f"  Arithmetic intensity: {self.arithmetic_intensity:.2f} FLOP/byte")
        lines.append(f"  Ridge point: {self.ridge_point:.2f} FLOP/byte")
        lines.append("")

        # Bottleneck
        if self.bottleneck == Bottleneck.MEMORY:
            lines.append(
                f"Bottleneck: MEMORY BOUND (intensity {self.arithmetic_intensity:.1f} < ridge {self.ridge_point:.1f})"
            )
        else:
            lines.append(
                f"Bottleneck: COMPUTE BOUND (intensity {self.arithmetic_intensity:.1f} > ridge {self.ridge_point:.1f})"
            )
        lines.append("")

        # Theoretical limits
        lines.append("Theoretical limits:")
        lines.append(f"  Peak bandwidth: {self.peak_bandwidth_bytes_per_s / 1e9:.0f} GB/s")
        lines.append(f"  Peak compute: {self.peak_flops_per_s / 1e12:.1f} TFLOPS")
        lines.append(f"  Memory-bound time: {_fmt_time(self.memory_bound_time_s)}")
        lines.append(f"  Compute-bound time: {_fmt_time(self.compute_bound_time_s)}")
        lines.append(f"  Theoretical minimum: {_fmt_time(self.theoretical_time_s)}")
        lines.append("")

        # Actual performance
        lines.append("Your performance:")
        lines.append(f"  Actual time: {_fmt_time(self.actual_time_s)}")
        lines.append(f"  Efficiency: {self.efficiency_pct:.1f}% of SOL")
        lines.append("")

        # Interpretation
        if self.efficiency_pct >= 80:
            lines.append("You're close to the roof. Major gains require algorithmic changes.")
        elif self.efficiency_pct >= 50:
            lines.append("Moderate efficiency. Room for optimization exists.")
            if self.bottleneck == Bottleneck.MEMORY:
                lines.append("  -> Check memory coalescing, reduce redundant loads")
            else:
                lines.append("  -> Check occupancy, reduce register pressure")
        else:
            lines.append("Significant optimization opportunity.")
            if self.bottleneck == Bottleneck.MEMORY:
                lines.append("  -> Memory bound but far from bandwidth limit")
                lines.append("  -> Check: coalescing, shared memory usage, cache hit rate")
            else:
                lines.append("  -> Compute bound but far from compute limit")
                lines.append("  -> Check: occupancy, warp divergence, instruction mix")

        return "\n".join(lines)


def _fmt_bytes(b: float) -> str:
    if b >= 1e12:
        return f"{b / 1e12:.2f} TB"
    if b >= 1e9:
        return f"{b / 1e9:.2f} GB"
    if b >= 1e6:
        return f"{b / 1e6:.2f} MB"
    if b >= 1e3:
        return f"{b / 1e3:.2f} KB"
    return f"{b:.0f} B"


def _fmt_flops(f: float) -> str:
    if f >= 1e15:
        return f"{f / 1e15:.2f} PFLOP"
    if f >= 1e12:
        return f"{f / 1e12:.2f} TFLOP"
    if f >= 1e9:
        return f"{f / 1e9:.2f} GFLOP"
    if f >= 1e6:
        return f"{f / 1e6:.2f} MFLOP"
    return f"{f:.0f} FLOP"


def _fmt_time(t: float) -> str:
    if t >= 1:
        return f"{t:.3f} s"
    if t >= 1e-3:
        return f"{t * 1e3:.3f} ms"
    if t >= 1e-6:
        return f"{t * 1e6:.3f} us"
    return f"{t * 1e9:.3f} ns"


def get_peak_flops(gpu: GpuSpec, dtype: Dtype) -> float:
    """Get peak FLOPS for a GPU and dtype, in FLOPS (not TFLOPS)."""
    tflops = {
        Dtype.FP64: gpu.peak_tflops_fp64,
        Dtype.FP32: gpu.peak_tflops_fp32,
        Dtype.FP16: gpu.peak_tflops_fp16,
        Dtype.BF16: gpu.peak_tflops_bf16,
        Dtype.FP8: gpu.peak_tflops_fp8,
        Dtype.INT8: gpu.peak_tflops_int8,
    }[dtype]
    return tflops * 1e12  # Convert TFLOPS to FLOPS


def roofline_analysis(
    *,
    gpu: str | GpuSpec,
    dtype: str | Dtype,
    bytes_moved: float,
    flops: float,
    time_s: float | None = None,
    time_ms: float | None = None,
) -> RooflineResult:
    """
    Perform roofline analysis.

    Args:
        gpu: GPU name (e.g., "H100") or GpuSpec
        dtype: Data type (e.g., "fp16") or Dtype enum
        bytes_moved: Total bytes moved to/from global memory
        flops: Total floating point operations
        time_s: Actual kernel time in seconds (provide this OR time_ms)
        time_ms: Actual kernel time in milliseconds (provide this OR time_s)

    Returns:
        RooflineResult with analysis
    """
    # Normalize inputs
    if isinstance(gpu, str):
        gpu = get_gpu_spec(gpu)

    if isinstance(dtype, str):
        dtype = Dtype(dtype.lower())

    if time_s is None and time_ms is None:
        raise ValueError("Must provide either time_s or time_ms")
    if time_s is not None and time_ms is not None:
        raise ValueError("Provide only one of time_s or time_ms")

    actual_time_s = time_s if time_s is not None else time_ms / 1000.0

    # Calculate derived values
    arithmetic_intensity = flops / bytes_moved if bytes_moved > 0 else float("inf")

    peak_bandwidth = gpu.peak_bandwidth_gbps * 1e9  # GB/s -> B/s
    peak_flops = get_peak_flops(gpu, dtype)

    ridge_point = peak_flops / peak_bandwidth  # FLOP/byte

    # Determine bottleneck
    bottleneck = Bottleneck.MEMORY if arithmetic_intensity < ridge_point else Bottleneck.COMPUTE

    # Calculate theoretical times
    memory_bound_time = bytes_moved / peak_bandwidth
    compute_bound_time = flops / peak_flops
    theoretical_time = max(memory_bound_time, compute_bound_time)

    # Calculate efficiency
    efficiency_pct = (theoretical_time / actual_time_s) * 100 if actual_time_s > 0 else 0

    return RooflineResult(
        gpu=gpu,
        dtype=dtype,
        bytes_moved=bytes_moved,
        flops=flops,
        actual_time_s=actual_time_s,
        arithmetic_intensity=arithmetic_intensity,
        peak_bandwidth_bytes_per_s=peak_bandwidth,
        peak_flops_per_s=peak_flops,
        ridge_point=ridge_point,
        bottleneck=bottleneck,
        memory_bound_time_s=memory_bound_time,
        compute_bound_time_s=compute_bound_time,
        theoretical_time_s=theoretical_time,
        efficiency_pct=efficiency_pct,
    )
