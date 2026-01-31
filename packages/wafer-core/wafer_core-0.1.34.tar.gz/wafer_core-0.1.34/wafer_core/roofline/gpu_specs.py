"""GPU specifications for roofline analysis.

Peak bandwidth and FLOPS numbers from vendor specs and benchmarks.
These are theoretical peaks - real-world achievable is typically 80-90% for bandwidth,
and varies widely for compute depending on operation.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class GpuSpec:
    name: str
    # Memory bandwidth in GB/s
    peak_bandwidth_gbps: float
    # Peak FLOPS by dtype (in TFLOPS)
    # Tensor core / matrix unit peaks where applicable
    peak_tflops_fp64: float
    peak_tflops_fp32: float
    peak_tflops_fp16: float  # Tensor core for NVIDIA
    peak_tflops_bf16: float
    peak_tflops_fp8: float
    peak_tflops_int8: float


# Sources:
# - NVIDIA: https://www.nvidia.com/en-us/data-center/ specs pages
# - AMD: https://www.amd.com/en/products/accelerators/instinct.html
# - Empirical validation from microbenchmarks where available

GPU_SPECS: dict[str, GpuSpec] = {
    # NVIDIA Blackwell
    "B200": GpuSpec(
        name="NVIDIA B200",
        peak_bandwidth_gbps=8000,  # HBM3e
        peak_tflops_fp64=40,  # 40 TFLOPS FP64
        peak_tflops_fp32=80,  # 80 TFLOPS FP32
        peak_tflops_fp16=2250,  # 4th gen tensor cores
        peak_tflops_bf16=2250,
        peak_tflops_fp8=4500,
        peak_tflops_int8=4500,
    ),
    "GB200": GpuSpec(
        name="NVIDIA GB200",
        peak_bandwidth_gbps=8000,
        peak_tflops_fp64=40,
        peak_tflops_fp32=80,
        peak_tflops_fp16=2250,
        peak_tflops_bf16=2250,
        peak_tflops_fp8=4500,
        peak_tflops_int8=4500,
    ),
    # NVIDIA Hopper
    "H100": GpuSpec(
        name="NVIDIA H100 SXM",
        peak_bandwidth_gbps=3350,  # HBM3
        peak_tflops_fp64=67,  # FP64 tensor core
        peak_tflops_fp32=989,  # TF32 tensor core (not true FP32)
        peak_tflops_fp16=1979,  # FP16 tensor core
        peak_tflops_bf16=1979,
        peak_tflops_fp8=3958,
        peak_tflops_int8=3958,
    ),
    "H100_PCIe": GpuSpec(
        name="NVIDIA H100 PCIe",
        peak_bandwidth_gbps=2000,  # HBM2e 80GB
        peak_tflops_fp64=48,
        peak_tflops_fp32=756,
        peak_tflops_fp16=1513,
        peak_tflops_bf16=1513,
        peak_tflops_fp8=3026,
        peak_tflops_int8=3026,
    ),
    # NVIDIA Ada Lovelace (consumer)
    "RTX_4090": GpuSpec(
        name="NVIDIA RTX 4090",
        peak_bandwidth_gbps=1008,  # GDDR6X
        peak_tflops_fp64=1.29,  # No FP64 tensor
        peak_tflops_fp32=82.6,
        peak_tflops_fp16=330,  # FP16 tensor (with sparsity: 661)
        peak_tflops_bf16=330,
        peak_tflops_fp8=660,
        peak_tflops_int8=660,
    ),
    "RTX_5090": GpuSpec(
        name="NVIDIA RTX 5090",
        peak_bandwidth_gbps=1792,  # GDDR7
        peak_tflops_fp64=1.5,  # Estimated
        peak_tflops_fp32=105,  # Estimated
        peak_tflops_fp16=420,  # Estimated
        peak_tflops_bf16=420,
        peak_tflops_fp8=840,
        peak_tflops_int8=840,
    ),
    # NVIDIA Ampere
    "A100": GpuSpec(
        name="NVIDIA A100 SXM",
        peak_bandwidth_gbps=2039,  # HBM2e 80GB
        peak_tflops_fp64=19.5,
        peak_tflops_fp32=312,  # TF32 tensor
        peak_tflops_fp16=624,
        peak_tflops_bf16=624,
        peak_tflops_fp8=0,  # No FP8 on Ampere
        peak_tflops_int8=1248,
    ),
    # AMD Instinct
    "MI300X": GpuSpec(
        name="AMD MI300X",
        peak_bandwidth_gbps=5300,  # HBM3
        peak_tflops_fp64=163.4,  # MFMA
        peak_tflops_fp32=163.4,  # FP32 MFMA (same as FP64 for MI300)
        peak_tflops_fp16=1307.4,  # FP16 MFMA
        peak_tflops_bf16=1307.4,
        peak_tflops_fp8=2614.9,
        peak_tflops_int8=2614.9,
    ),
    "MI250X": GpuSpec(
        name="AMD MI250X",
        peak_bandwidth_gbps=3276,  # HBM2e (per GCD, 2x GCDs)
        peak_tflops_fp64=95.7,  # Per GCD
        peak_tflops_fp32=95.7,
        peak_tflops_fp16=383,
        peak_tflops_bf16=383,
        peak_tflops_fp8=0,  # No FP8
        peak_tflops_int8=383,
    ),
}


def get_gpu_spec(name: str) -> GpuSpec:
    """Get GPU spec by name (case-insensitive, with common aliases)."""
    normalized = name.upper().replace(" ", "_").replace("-", "_")

    # Direct lookup
    if normalized in GPU_SPECS:
        return GPU_SPECS[normalized]

    # Common aliases
    aliases = {
        "H100_SXM": "H100",
        "H100SXM": "H100",
        "H100_PCIE": "H100_PCIe",
        "H100PCIE": "H100_PCIe",
        "A100_SXM": "A100",
        "A100_80GB": "A100",
        "4090": "RTX_4090",
        "RTX4090": "RTX_4090",
        "5090": "RTX_5090",
        "RTX5090": "RTX_5090",
        "MI300": "MI300X",
        "MI250": "MI250X",
    }

    if normalized in aliases:
        return GPU_SPECS[aliases[normalized]]

    available = ", ".join(sorted(GPU_SPECS.keys()))
    raise ValueError(f"Unknown GPU: {name}. Available: {available}")


def list_gpus() -> list[str]:
    """List all available GPU names."""
    return sorted(GPU_SPECS.keys())
