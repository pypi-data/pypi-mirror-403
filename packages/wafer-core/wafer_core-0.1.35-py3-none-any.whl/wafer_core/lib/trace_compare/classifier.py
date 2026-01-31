"""Kernel classification logic for trace comparison.

Classifies GPU kernels into operation categories (attention, GEMM, normalization, etc.)
based on kernel name patterns and platform-specific conventions.
"""

from enum import Enum


class Op(Enum):
    """Kernel operation categories."""

    ATTN_PREFILL = "Attention (Prefill)"
    ATTN_DECODE = "Attention (Decode)"
    KV_CACHE = "KV Cache"
    MOE_ROUTING = "MoE Routing"
    MOE_GEMM = "MoE GEMM"
    MOE_GEMM_SWIGLU = "MoE GEMM+SwiGLU"
    MOE_FINALIZE = "MoE Finalize"
    DENSE_GEMM = "Dense GEMM"
    RMSNORM = "RMSNorm"
    RMSNORM_GEMM = "RMSNorm+GEMM"
    TRITON_FUSED = "Triton Fused"
    ELEMENTWISE = "Elementwise"
    SORTING = "Sorting"
    REDUCE = "Reduce"
    COPY_MEMORY = "Copy/Memory"
    OTHER = "Other"


def classify(name: str, platform: str) -> tuple[Op, str]:
    """Classify kernel by operation type.

    Args:
        name: Kernel name from trace
        platform: 'AMD' or 'NVIDIA'

    Returns:
        Tuple of (operation type, pattern name)
    """
    nl = name.lower()

    # Attention
    if "attention" in nl or "fmha" in nl:
        if platform == "AMD":
            if "2d" in nl:
                return Op.ATTN_PREFILL, "kernel_unified_attention_2d"
            if "3d" in nl:
                return Op.ATTN_DECODE, "kernel_unified_attention_3d"
        else:
            # NVIDIA uses fmhaSm100 with 'a' (prefill/context) and 'f' (decode/forgen)
            if "fmhasm100a" in nl or "context" in nl:
                return Op.ATTN_PREFILL, "fmhaSm100a*_Context"
            if "fmhasm100f" in nl or "forgen" in nl:
                return Op.ATTN_DECODE, "fmhaSm100f*_ForGen"
        return Op.ATTN_PREFILL, name[:40]

    if "reshape_and_cache" in nl:
        return Op.KV_CACHE, "reshape_and_cache_*"

    # MoE
    if "_matmul_ogs_" in nl:
        if "swiglu" in nl:
            return Op.MOE_GEMM_SWIGLU, "_matmul_ogs_*_swiglu"
        return Op.MOE_GEMM, "_matmul_ogs_*"

    if name.startswith("bmm_") and "dynbatch" in nl:
        if "swiglu" in nl:
            return Op.MOE_GEMM_SWIGLU, "bmm_*_swiGlu_dynBatch"
        return Op.MOE_GEMM, "bmm_*_dynBatch"

    if any(x in nl for x in ["topk", "routing", "bitmatrix", "moe_forward", "_combined_routing"]):
        return Op.MOE_ROUTING, "moe_routing_*"
    if "finalize" in nl or ("scatter" in nl and "moe" in nl):
        return Op.MOE_FINALIZE, "moe_finalize_*"

    # RMSNorm - match actual patterns from traces
    if "triton" in nl and ("rsqrt" in nl or ("mean" in nl and "mul" in nl and "pow" in nl)):
        if "gemm" in nl or "addmm" in nl:
            return Op.RMSNORM_GEMM, "triton_*_rmsnorm_gemm"
        return Op.RMSNORM, "triton_*_rsqrt"

    # Dense GEMM - these are the most common kernels
    if name.startswith("Cijk_") or name.startswith("Custom_Cijk_"):
        return Op.DENSE_GEMM, "Cijk_* (Tensile)"
    if name.startswith("nvjet_") or "cublaslt" in nl:
        return Op.DENSE_GEMM, "nvjet_* (cuBLASLt)"
    if "wvsplitk" in nl or name.startswith("void wvSplitK"):
        return Op.DENSE_GEMM, "wvSplitK_* (hipBLASLt)"

    # Triton fused operations - very common
    if "triton_poi" in nl or "triton_red" in nl or "triton_per" in nl:
        # Distinguish between different fusion patterns
        if "silu" in nl or "swiglu" in nl:
            return Op.TRITON_FUSED, "triton_*_silu"
        return Op.TRITON_FUSED, "triton_*"

    # PyTorch native operations
    if "at::native::" in name:
        return Op.ELEMENTWISE, "at::native::*"

    # Sorting operations (common in sampling/topk)
    if "sort" in nl or "radixsort" in nl or "merge" in nl:
        if platform == "AMD":
            return Op.SORTING, "rocprim::sort/merge_*"
        else:
            return Op.SORTING, "cub::DeviceRadixSort*"

    # Reduce operations
    if "reduce" in nl and ("reduce_segments" in nl or "devicereduce" in nl or "devicescan" in nl):
        if platform == "AMD":
            return Op.REDUCE, "reduce_segments"
        else:
            return Op.REDUCE, "cub::DeviceReduce*"

    # Memory copy operations
    if "copy" in nl or "memcpy" in nl or "_copy_page_indices" in nl:
        return Op.COPY_MEMORY, "copy_*"

    # ROCm/CUDA library kernels (other)
    if "rocprim::" in name or "cub::" in name:
        return Op.OTHER, "rocprim/cub_*"

    return Op.OTHER, name[:40]


def classify_kernel(name: str) -> str:
    """Simplified kernel classification for fusion analysis.

    Args:
        name: Kernel name from trace

    Returns:
        Simple category name consistent across platforms
    """
    nl = name.lower()

    # GEMM operations (matrix multiplication)
    if any(x in nl for x in ["cijk_", "nvjet", "wvsplitk", "cublas", "hipblas", "tensile"]):
        return "GEMM"

    # Attention
    if "attention" in nl or "fmha" in nl:
        return "Attention"

    # KV Cache
    if "reshape_and_cache" in nl:
        return "KV_Cache"

    # RMSNorm / LayerNorm
    if "triton" in nl and "rsqrt" in nl:
        return "RMSNorm"
    if "layernorm" in nl or "rmsnorm" in nl:
        return "RMSNorm"

    # SwiGLU / Activations
    if "silu" in nl or "swiglu" in nl:
        return "SwiGLU"
    if "gelu" in nl:
        return "GELU"
    if "relu" in nl and "gelu" not in nl:
        return "ReLU"

    # Triton fused operations (generic)
    if "triton_poi" in nl:
        return "Triton_Pointwise"
    if "triton_red" in nl:
        return "Triton_Reduce"
    if "triton_per" in nl:
        return "Triton_Persistent"

    # Reduce operations
    if "reduce_segments" in nl or "devicereduce" in nl:
        return "Reduce"

    # Sort operations
    if "sort" in nl or "radixsort" in nl or "merge" in nl:
        return "Sort"

    # Softmax
    if "softmax" in nl:
        return "Softmax"

    # Elementwise operations
    if any(x in nl for x in ["elementwise", "unrolled_elementwise"]):
        return "Elementwise"

    # Copy/Memory operations
    if "copy" in nl or "memcpy" in nl:
        return "MemCopy"

    return "Other"
