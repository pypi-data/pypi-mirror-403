"""Roofline analysis for kernel performance.

Calculates what percentage of peak hardware performance a kernel achieves.
"""

from typing import Literal

from wafer_core.tools.dispatch_baseline.dtypes import HardwareSpec, KernelInfo, RooflineAnalysis


# Hardware specifications for bare metal GPUs we have access to
# Note: TFLOPS values are theoretical peak (without sparsity for realistic comparison)
HARDWARE_SPECS: dict[str, HardwareSpec] = {
    "B200": HardwareSpec(
        name="B200",
        peak_fp16_tflops=2250.0,  # 4500 with sparsity
        peak_fp32_tflops=18.0,
        peak_memory_bw_tbps=8.0,  # HBM3e
        peak_fp8_tflops=4500.0,
        peak_int8_tops=4500.0,
        shared_memory_per_sm_kb=228.0,
    ),
    "MI300X": HardwareSpec(
        name="MI300X",
        peak_fp16_tflops=1307.4,  # 2614.9 with sparsity
        peak_fp32_tflops=163.4,
        peak_memory_bw_tbps=5.3,
        peak_fp8_tflops=2614.9,
        peak_int8_tops=2614.9,
        shared_memory_per_sm_kb=64.0,  # per CU
    ),
}


def get_hardware_spec(hardware: str) -> HardwareSpec | None:
    """Get hardware specification by name.

    Args:
        hardware: Hardware name (e.g., "H100", "MI300X")

    Returns:
        HardwareSpec if found, None otherwise
    """
    # Normalize name (uppercase, remove common suffixes)
    normalized = hardware.upper().replace("-SXM", "").replace("-PCIE", "")
    return HARDWARE_SPECS.get(normalized)


def compute_roofline(
    kernel: KernelInfo,
    hardware: str,
    flops_per_call: float,
    bytes_per_call: float,
) -> RooflineAnalysis | None:
    """Compute roofline analysis for a kernel.

    Args:
        kernel: Kernel information with duration
        hardware: Hardware name
        flops_per_call: Total floating point operations per kernel call
        bytes_per_call: Total bytes transferred per kernel call

    Returns:
        RooflineAnalysis if hardware spec found, None otherwise
    """
    hw_spec = get_hardware_spec(hardware)
    if hw_spec is None:
        return None

    if kernel.duration_us <= 0:
        return None

    # Calculate achieved throughput
    duration_sec = kernel.duration_us / 1e6
    achieved_tflops = (flops_per_call / 1e12) / duration_sec
    achieved_tbps = (bytes_per_call / 1e12) / duration_sec

    # Calculate percentage of peak
    compute_pct = (achieved_tflops / hw_spec.peak_fp16_tflops) * 100
    memory_pct = (achieved_tbps / hw_spec.peak_memory_bw_tbps) * 100

    # Calculate arithmetic intensity
    arithmetic_intensity = flops_per_call / bytes_per_call if bytes_per_call > 0 else 0

    # Determine bottleneck
    # Ridge point = peak_flops / peak_bandwidth (in FLOPS/byte)
    ridge_point = (hw_spec.peak_fp16_tflops * 1e12) / (hw_spec.peak_memory_bw_tbps * 1e12)

    if arithmetic_intensity < ridge_point * 0.8:
        bottleneck: Literal["compute", "memory", "balanced"] = "memory"
    elif arithmetic_intensity > ridge_point * 1.2:
        bottleneck = "compute"
    else:
        bottleneck = "balanced"

    return RooflineAnalysis(
        achieved_tflops=achieved_tflops,
        achieved_memory_bw_tbps=achieved_tbps,
        compute_pct_of_peak=compute_pct,
        memory_bw_pct_of_peak=memory_pct,
        bottleneck=bottleneck,
        arithmetic_intensity=arithmetic_intensity,
    )


def estimate_matmul_flops(m: int, n: int, k: int) -> float:
    """Estimate FLOPs for matrix multiplication.

    For C[M,N] = A[M,K] @ B[K,N]:
    FLOPs = 2 * M * N * K (multiply-add counted as 2 ops)
    """
    return 2.0 * m * n * k


def estimate_matmul_bytes(m: int, n: int, k: int, dtype_bytes: int = 2) -> float:
    """Estimate bytes transferred for matrix multiplication.

    Minimum bytes = read A + read B + write C
    """
    a_bytes = m * k * dtype_bytes
    b_bytes = k * n * dtype_bytes
    c_bytes = m * n * dtype_bytes
    return float(a_bytes + b_bytes + c_bytes)


def estimate_softmax_flops(elements: int) -> float:
    """Estimate FLOPs for softmax.

    Per element: exp, sum reduction, division
    Roughly 5 ops per element (conservative)
    """
    return 5.0 * elements


def estimate_softmax_bytes(elements: int, dtype_bytes: int = 2) -> float:
    """Estimate bytes for softmax.

    Read input, write output
    """
    return 2.0 * elements * dtype_bytes


def estimate_attention_flops(batch: int, heads: int, seq_len: int, head_dim: int) -> float:
    """Estimate FLOPs for attention.

    Q @ K^T: 2 * batch * heads * seq_len * seq_len * head_dim
    softmax: ~5 * batch * heads * seq_len * seq_len
    attn @ V: 2 * batch * heads * seq_len * head_dim * seq_len
    """
    qk_flops = 2.0 * batch * heads * seq_len * seq_len * head_dim
    softmax_flops = 5.0 * batch * heads * seq_len * seq_len
    av_flops = 2.0 * batch * heads * seq_len * head_dim * seq_len
    return qk_flops + softmax_flops + av_flops


def estimate_attention_bytes(
    batch: int, heads: int, seq_len: int, head_dim: int, dtype_bytes: int = 2
) -> float:
    """Estimate bytes for attention.

    Read Q, K, V, write output
    """
    qkv_bytes = 3 * batch * heads * seq_len * head_dim * dtype_bytes
    output_bytes = batch * heads * seq_len * head_dim * dtype_bytes
    return float(qkv_bytes + output_bytes)
