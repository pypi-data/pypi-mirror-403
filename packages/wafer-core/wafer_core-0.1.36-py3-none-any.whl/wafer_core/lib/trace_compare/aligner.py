"""Kernel alignment system for comparing AMD and NVIDIA traces.

Aligns kernels at the layer level using positional matching (same model = same layer structure).
Provides kernel-to-kernel mapping for exact performance comparison.
"""

import bisect
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from .classifier import Op, classify


@dataclass
class KernelPair:
    """A pair of aligned kernels from AMD and NVIDIA traces."""

    position: int
    operation: str
    operation_detail: str | None

    amd_kernel: str
    amd_avg_us: float
    amd_count: int
    amd_total_us: float

    nvidia_kernel: str | None
    nvidia_avg_us: float
    nvidia_count: int
    nvidia_total_us: float

    ratio: float
    gap_us: float
    fusion_note: str | None = None
    is_same_kernel: bool = False


@dataclass
class LayerAlignment:
    """Alignment data for a single layer."""

    layer: int
    amd_total_us: float
    nvidia_total_us: float
    ratio: float
    gap_us: float
    kernel_pairs: list[KernelPair] = field(default_factory=list)


@dataclass
class TraceAlignment:
    """Complete alignment result for two traces."""

    layer_alignments: list[LayerAlignment]
    num_layers: int
    num_forward_passes: int
    phase_breakdown: dict[str, int]


def split_by_forward_pass(
    kernels: list[dict[str, Any]], phases: list[dict[str, Any]]
) -> list[list[dict[str, Any]]]:
    """Split kernels into forward passes using phase annotation timestamps.

    Args:
        kernels: List of kernel events with 'ts' field
        phases: List of phase annotations with 'ts_start' and 'ts_end'

    Returns:
        List of forward passes, each containing kernels for that pass
    """
    if not phases:
        return [kernels]

    sorted_phases = sorted(phases, key=lambda p: p["ts_start"])
    sorted_kernels = sorted(kernels, key=lambda k: k.get("ts", 0))
    kernel_timestamps = [k.get("ts", 0) for k in sorted_kernels]

    forward_passes: list[list[dict[str, Any]]] = []

    for phase in sorted_phases:
        ts_start = phase["ts_start"]
        ts_end = phase["ts_end"]

        start_idx = bisect.bisect_left(kernel_timestamps, ts_start)
        end_idx = bisect.bisect_right(kernel_timestamps, ts_end)

        pass_kernels = sorted_kernels[start_idx:end_idx]
        if pass_kernels:
            forward_passes.append(pass_kernels)

    return forward_passes


def split_into_layers(
    forward_pass: list[dict[str, Any]], platform: str
) -> list[list[dict[str, Any]]]:
    """Split a forward pass into layers using attention kernels as boundaries.

    Args:
        forward_pass: Kernels from a single forward pass
        platform: 'AMD' or 'NVIDIA'

    Returns:
        List of layers, each containing kernels for that layer
    """
    if not forward_pass:
        return []

    sorted_kernels = sorted(forward_pass, key=lambda k: k.get("ts", 0))

    layer_markers: list[int] = []
    for i, kernel in enumerate(sorted_kernels):
        name_lower = kernel.get("name", "").lower()
        is_attention = False

        if platform == "AMD":
            is_attention = "attention" in name_lower and ("2d" in name_lower or "3d" in name_lower)
        else:
            is_attention = "fmha" in name_lower or "attention" in name_lower

        if is_attention:
            layer_markers.append(i)

    if not layer_markers:
        return [sorted_kernels]

    layers: list[list[dict[str, Any]]] = []
    for i, marker_idx in enumerate(layer_markers):
        start_idx = marker_idx
        end_idx = layer_markers[i + 1] if i + 1 < len(layer_markers) else len(sorted_kernels)
        layer_kernels = sorted_kernels[start_idx:end_idx]
        if layer_kernels:
            layers.append(layer_kernels)

    return layers


def align_kernels_within_layer(
    amd_layer_instances: list[list[dict[str, Any]]],
    nvidia_layer_instances: list[list[dict[str, Any]]],
    platform_amd: str = "AMD",
    platform_nvidia: str = "NVIDIA",
) -> list[KernelPair]:
    """Align kernels within a layer across multiple forward pass instances.

    Args:
        amd_layer_instances: List of layer kernels from each AMD forward pass
        nvidia_layer_instances: List of layer kernels from each NVIDIA forward pass
        platform_amd: Platform name for AMD
        platform_nvidia: Platform name for NVIDIA

    Returns:
        List of aligned kernel pairs
    """
    if not amd_layer_instances and not nvidia_layer_instances:
        return []

    amd_by_op_pos: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
    nvidia_by_op_pos: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)

    for instance in amd_layer_instances:
        sorted_kernels = sorted(instance, key=lambda k: k.get("ts", 0))
        for pos, kernel in enumerate(sorted_kernels):
            op, pattern = classify(kernel.get("name", ""), platform_amd)
            # For FUSED_UNKNOWN, use the pattern (e.g., "RMSNorm+GEMM") as the operation
            # so fusion detection works correctly
            op_str = pattern if op.value == "Fused (Unknown)" else op.value
            amd_by_op_pos[(op_str, pos)].append(kernel)

    for instance in nvidia_layer_instances:
        sorted_kernels = sorted(instance, key=lambda k: k.get("ts", 0))
        for pos, kernel in enumerate(sorted_kernels):
            op, pattern = classify(kernel.get("name", ""), platform_nvidia)
            # For FUSED_UNKNOWN, use the pattern (e.g., "RMSNorm+GEMM") as the operation
            op_str = pattern if op.value == "Fused (Unknown)" else op.value
            nvidia_by_op_pos[(op_str, pos)].append(kernel)

    all_keys = set(amd_by_op_pos.keys()) | set(nvidia_by_op_pos.keys())
    kernel_pairs: list[KernelPair] = []

    for op_str, pos in sorted(all_keys):
        amd_kernels = amd_by_op_pos.get((op_str, pos), [])
        nvidia_kernels = nvidia_by_op_pos.get((op_str, pos), [])

        amd_total_us = sum(k.get("dur", 0) for k in amd_kernels)
        amd_count = len(amd_kernels)
        amd_avg_us = amd_total_us / amd_count if amd_count > 0 else 0.0

        amd_kernel_name = ""
        if amd_kernels:
            name_counts = defaultdict(int)
            for k in amd_kernels:
                name_counts[k.get("name", "")] += 1
            amd_kernel_name = max(name_counts.items(), key=lambda x: x[1])[0]

        nvidia_total_us = sum(k.get("dur", 0) for k in nvidia_kernels)
        nvidia_count = len(nvidia_kernels)
        nvidia_avg_us = nvidia_total_us / nvidia_count if nvidia_count > 0 else 0.0

        nvidia_kernel_name: str | None = None
        if nvidia_kernels:
            name_counts = defaultdict(int)
            for k in nvidia_kernels:
                name_counts[k.get("name", "")] += 1
            nvidia_kernel_name = max(name_counts.items(), key=lambda x: x[1])[0]

        ratio = amd_avg_us / nvidia_avg_us if nvidia_avg_us > 0 else float("inf")
        gap_us = amd_avg_us - nvidia_avg_us

        # Detect fusion notes
        # Key insight: If operation has '+' (e.g., "RMSNorm+GEMM"), it's already a fused operation
        # The platform that HAS the kernel IS fusing; the other runs components separately
        is_fused_op = "+" in op_str
        
        # Operations that can't be "fused away" - absence means alignment issue, not fusion
        non_fusable_ops = {
            "Attention (Prefill)", "Attention (Decode)", "Dense GEMM", 
            "KV Cache", "MoE GEMM", "MoE Routing"
        }
        is_non_fusable = op_str in non_fusable_ops
        
        fusion_note = None
        if amd_count > 0 and nvidia_count == 0:
            if is_fused_op:
                # AMD has a fused kernel like "RMSNorm+GEMM" → AMD IS fusing
                fusion_note = f"AMD fuses {op_str} into {amd_kernel_name}"
            elif not is_non_fusable:
                # Only mark as fusion for ops that can legitimately be fused
                fusion_note = f"AMD runs {amd_kernel_name}, NVIDIA may fuse into another kernel"
        elif amd_count == 0 and nvidia_count > 0:
            if is_fused_op:
                # NVIDIA has a fused kernel → NVIDIA IS fusing
                fusion_note = f"NVIDIA fuses {op_str} into {nvidia_kernel_name}"
            elif not is_non_fusable:
                # Only mark as fusion for ops that can legitimately be fused
                fusion_note = f"NVIDIA runs {nvidia_kernel_name}, AMD may fuse into another kernel"
        elif amd_count > nvidia_count * 1.5 and nvidia_count > 0:
            # AMD runs more kernels = NVIDIA is fusing some
            fusion_note = f"AMD runs {amd_kernel_name} {amd_count / nvidia_count:.1f}x more → NVIDIA fuses"
        elif nvidia_count > amd_count * 1.5 and amd_count > 0:
            # NVIDIA runs more kernels = AMD is fusing some
            fusion_note = f"NVIDIA runs {nvidia_kernel_name} {nvidia_count / amd_count:.1f}x more → AMD fuses"

        is_same = (
            amd_kernel_name != ""
            and nvidia_kernel_name is not None
            and amd_kernel_name == nvidia_kernel_name
        )

        operation_detail = None
        if op_str == "Dense GEMM":
            if "qkv" in amd_kernel_name.lower() or "qkv" in (nvidia_kernel_name or "").lower():
                operation_detail = "QKV"
            elif "out" in amd_kernel_name.lower() or "out" in (nvidia_kernel_name or "").lower():
                operation_detail = "O"
            elif "up" in amd_kernel_name.lower() or "up" in (nvidia_kernel_name or "").lower():
                operation_detail = "FFN_up"
            elif "down" in amd_kernel_name.lower() or "down" in (nvidia_kernel_name or "").lower():
                operation_detail = "FFN_down"

        kernel_pairs.append(
            KernelPair(
                position=pos,
                operation=op_str,
                operation_detail=operation_detail,
                amd_kernel=amd_kernel_name,
                amd_avg_us=amd_avg_us,
                amd_count=amd_count,
                amd_total_us=amd_total_us,
                nvidia_kernel=nvidia_kernel_name,
                nvidia_avg_us=nvidia_avg_us,
                nvidia_count=nvidia_count,
                nvidia_total_us=nvidia_total_us,
                ratio=ratio,
                gap_us=gap_us,
                fusion_note=fusion_note,
                is_same_kernel=is_same,
            )
        )

    return kernel_pairs


def align_traces(
    amd_kernels: list[dict[str, Any]],
    nvidia_kernels: list[dict[str, Any]],
    amd_phases: list[dict[str, Any]],
    nvidia_phases: list[dict[str, Any]],
    platform_amd: str = "AMD",
    platform_nvidia: str = "NVIDIA",
) -> TraceAlignment:
    """Align two traces at the layer level.

    Args:
        amd_kernels: Kernel events from AMD trace
        nvidia_kernels: Kernel events from NVIDIA trace
        amd_phases: Phase annotations from AMD trace
        nvidia_phases: Phase annotations from NVIDIA trace
        platform_amd: Platform name for AMD (default: "AMD")
        platform_nvidia: Platform name for NVIDIA (default: "NVIDIA")

    Returns:
        TraceAlignment with layer-by-layer kernel pairs
    """
    amd_passes = split_by_forward_pass(amd_kernels, amd_phases)
    nvidia_passes = split_by_forward_pass(nvidia_kernels, nvidia_phases)

    if not amd_passes or not nvidia_passes:
        return TraceAlignment(
            layer_alignments=[],
            num_layers=0,
            num_forward_passes=0,
            phase_breakdown={"prefill": 0, "decode": 0},
        )

    amd_layers_by_pass: list[list[list[dict[str, Any]]]] = [
        split_into_layers(pass_kernels, platform_amd) for pass_kernels in amd_passes
    ]
    nvidia_layers_by_pass: list[list[list[dict[str, Any]]]] = [
        split_into_layers(pass_kernels, platform_nvidia) for pass_kernels in nvidia_passes
    ]

    num_layers = max(
        max((len(layers) for layers in amd_layers_by_pass), default=0),
        max((len(layers) for layers in nvidia_layers_by_pass), default=0),
    )

    if num_layers == 0:
        return TraceAlignment(
            layer_alignments=[],
            num_layers=0,
            num_forward_passes=len(amd_passes),
            phase_breakdown={"prefill": 0, "decode": 0},
        )

    layer_alignments: list[LayerAlignment] = []

    for layer_idx in range(num_layers):
        amd_layer_instances = [
            layers[layer_idx] for layers in amd_layers_by_pass if layer_idx < len(layers)
        ]
        nvidia_layer_instances = [
            layers[layer_idx] for layers in nvidia_layers_by_pass if layer_idx < len(layers)
        ]

        kernel_pairs = align_kernels_within_layer(
            amd_layer_instances, nvidia_layer_instances, platform_amd, platform_nvidia
        )

        amd_total_us = sum(pair.amd_total_us for pair in kernel_pairs)
        nvidia_total_us = sum(pair.nvidia_total_us for pair in kernel_pairs)
        ratio = amd_total_us / nvidia_total_us if nvidia_total_us > 0 else float("inf")
        gap_us = amd_total_us - nvidia_total_us

        layer_alignments.append(
            LayerAlignment(
                layer=layer_idx,
                amd_total_us=amd_total_us,
                nvidia_total_us=nvidia_total_us,
                ratio=ratio,
                gap_us=gap_us,
                kernel_pairs=kernel_pairs,
            )
        )

    prefill_count = sum(1 for p in amd_phases if p.get("type") == "prefill")
    decode_count = sum(1 for p in amd_phases if p.get("type") == "decode")

    return TraceAlignment(
        layer_alignments=layer_alignments,
        num_layers=num_layers,
        num_forward_passes=len(amd_passes),
        phase_breakdown={"prefill": prefill_count, "decode": decode_count},
    )
