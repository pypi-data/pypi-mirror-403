"""Data types for kernel trace tool."""

from dataclasses import dataclass, field
from typing import Literal


@dataclass(frozen=True)
class TensorSpec:
    """Specification for a tensor operand."""

    name: str
    shape: tuple[int, ...]
    dtype: str = "float16"  # e.g., "float16", "float32", "bfloat16", "int8"
    device: str = "cuda"

    def __str__(self) -> str:
        shape_str = "x".join(str(d) for d in self.shape)
        return f"{self.name}[{shape_str}] ({self.dtype})"


@dataclass(frozen=True)
class OpSpec:
    """Specification for a PyTorch operation to trace.

    Example:
        OpSpec(
            op="torch.matmul",
            inputs=[
                TensorSpec("A", (4096, 4096), "float16"),
                TensorSpec("B", (4096, 4096), "float16"),
            ],
        )
    """

    op: str  # e.g., "torch.matmul", "torch.nn.functional.softmax", "torch.conv2d"
    inputs: list[TensorSpec]
    kwargs: dict[str, str] = field(default_factory=dict)  # e.g., {"dim": "-1"}

    def __str__(self) -> str:
        inputs_str = ", ".join(t.name for t in self.inputs)
        kwargs_str = ", ".join(f"{k}={v}" for k, v in self.kwargs.items())
        if kwargs_str:
            return f"{self.op}({inputs_str}, {kwargs_str})"
        return f"{self.op}({inputs_str})"


@dataclass(frozen=True)
class KernelInfo:
    """Information about a dispatched kernel."""

    name: str  # e.g., "sm90_xmma_gemm_f16f16f16_f32..."
    duration_us: float = 0.0  # Duration in microseconds
    grid_size: tuple[int, int, int] | None = None  # (X, Y, Z)
    block_size: tuple[int, int, int] | None = None  # (X, Y, Z)
    registers_per_thread: int | None = None
    shared_memory_bytes: int | None = None
    # Performance metrics (from NCU, if available)
    compute_throughput_tflops: float | None = None
    memory_throughput_tbps: float | None = None  # TB/s
    achieved_occupancy_pct: float | None = None

    def __str__(self) -> str:
        return f"{self.name} {self.duration_us:.1f} µs"


@dataclass(frozen=True)
class HardwareSpec:
    """Hardware specifications for roofline analysis."""

    name: str  # e.g., "H100", "MI300X"
    peak_fp16_tflops: float
    peak_fp32_tflops: float
    peak_memory_bw_tbps: float  # TB/s
    # Optional extras
    peak_fp8_tflops: float | None = None
    peak_int8_tops: float | None = None
    shared_memory_per_sm_kb: float | None = None


@dataclass(frozen=True)
class RooflineAnalysis:
    """Roofline analysis result."""

    # Raw metrics
    achieved_tflops: float
    achieved_memory_bw_tbps: float
    # Percentages of peak
    compute_pct_of_peak: float
    memory_bw_pct_of_peak: float
    # Bottleneck identification
    bottleneck: Literal["compute", "memory", "balanced"]
    arithmetic_intensity: float  # FLOPS per byte


@dataclass(frozen=True)
class KernelTraceConfig:
    """Configuration for kernel tracing."""

    op_spec: OpSpec
    hardware: str  # e.g., "H100", "MI300X"
    num_warmup: int = 10
    num_runs: int = 100
    use_ncu: bool = False  # Use NCU for detailed metrics (slower)
    timeout_seconds: int = 120


@dataclass(frozen=True)
class KernelTraceResult:
    """Result of tracing a PyTorch operation."""

    op_spec: OpSpec
    hardware: str
    # Kernels dispatched (may be multiple for fused ops)
    kernels: list[KernelInfo]
    # Primary kernel (typically the longest-running one)
    primary_kernel: KernelInfo | None
    # Roofline analysis (if metrics available)
    roofline: RooflineAnalysis | None = None
    # Raw profiler output (for debugging)
    raw_output: str | None = None
    # Error, if any
    error: str | None = None

    @property
    def total_duration_us(self) -> float:
        """Total duration of all kernels."""
        return sum(k.duration_us for k in self.kernels)

    def summary(self) -> str:
        """Generate human-readable summary."""
        if self.error:
            return f"Error: {self.error}"

        # Build operation description with shapes
        op_desc = self._format_op_description()

        lines = [
            "═" * 65,
            f" BASELINE: {op_desc}",
            "═" * 65,
            "",
        ]

        # Primary kernel section
        if self.primary_kernel:
            lines.append(" Primary Kernel:")
            kernel_name = self._truncate_kernel_name(self.primary_kernel.name, 55)
            lines.append(f"   → {kernel_name}")
            lines.append(f"     Duration: {self._format_duration(self.primary_kernel.duration_us)}")
            lines.append("")

        # Roofline section
        if self.roofline:
            lines.append(" Roofline Analysis:")
            
            # Format TFLOPS with commas for readability
            tflops_str = f"{self.roofline.achieved_tflops:,.1f}"
            bw_str = f"{self.roofline.achieved_memory_bw_tbps:.2f}"
            
            lines.append(f"   Achieved:    {tflops_str} TFLOPS  ({self.roofline.compute_pct_of_peak:.1f}% of {self.hardware} peak)")
            lines.append(f"   Memory BW:   {bw_str} TB/s     ({self.roofline.memory_bw_pct_of_peak:.1f}% of peak)")
            lines.append(f"   Bottleneck:  {self.roofline.bottleneck.upper()}")
            lines.append("")

        # All kernels section (if more than one)
        if len(self.kernels) > 1:
            lines.append(" All Kernels:")
            total_dur = self.total_duration_us
            for i, k in enumerate(self.kernels[:5]):  # Show top 5
                pct = (k.duration_us / total_dur * 100) if total_dur > 0 else 0
                name = self._truncate_kernel_name(k.name, 45)
                dur_str = self._format_duration(k.duration_us)
                marker = "→" if k == self.primary_kernel else " "
                lines.append(f"   {marker} {i+1}. {name:<45}  {dur_str:>10}  ({pct:>4.1f}%)")
            if len(self.kernels) > 5:
                lines.append(f"      ... and {len(self.kernels) - 5} more kernels")
            lines.append("")

        lines.append("─" * 65)

        return "\n".join(lines)

    def _format_op_description(self) -> str:
        """Format operation with shape info."""
        op_name = self.op_spec.op.split(".")[-1]  # e.g., "matmul" from "torch.matmul"
        
        # Format input shapes
        shape_strs = []
        for t in self.op_spec.inputs:
            shape_str = "×".join(str(d) for d in t.shape)
            shape_strs.append(shape_str)
        
        # Get dtype from first input
        dtype = self.op_spec.inputs[0].dtype if self.op_spec.inputs else "float16"
        dtype_upper = dtype.upper().replace("FLOAT", "FP").replace("BFLOAT", "BF")
        
        if len(shape_strs) == 2:
            return f"{op_name} ({shape_strs[0]} @ {shape_strs[1]}) {dtype_upper}"
        elif len(shape_strs) == 1:
            return f"{op_name} ({shape_strs[0]}) {dtype_upper}"
        else:
            return f"{op_name} {dtype_upper}"

    def _truncate_kernel_name(self, name: str, max_len: int) -> str:
        """Truncate long kernel names."""
        if len(name) <= max_len:
            return name
        return name[:max_len - 3] + "..."

    def _format_duration(self, us: float) -> str:
        """Format duration nicely."""
        if us >= 1000:
            return f"{us / 1000:.2f} ms"
        elif us >= 1:
            return f"{us:.1f} µs"
        else:
            return f"{us * 1000:.1f} ns"
