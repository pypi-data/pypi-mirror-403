"""Fusion analysis for detecting kernel fusion differences between platforms.

Detects fusion differences between AMD and NVIDIA by analyzing how many kernels
each platform launches for the same logical operations.
"""

import json
from collections import Counter, defaultdict
from functools import lru_cache
from pathlib import Path
from typing import Any

from .classifier import classify_kernel


@lru_cache(maxsize=10000)
def _classify_kernel_cached(name: str) -> str:
    """Classify kernel with caching to avoid redundant regex matching."""
    return classify_kernel(name)


def _load_trace_for_fusion(
    file_path: str | Path,
) -> tuple[str, str, list[dict[str, Any]], dict[int, list[dict[str, Any]]]]:
    """Load trace and group kernels by correlation ID.

    Args:
        file_path: Path to trace file

    Returns:
        Tuple of (platform, gpu_name, all_kernels, corr_groups)
    """
    with open(file_path, "rb") as f:
        trace = json.load(f)

    # Detect platform
    props = trace.get("deviceProperties", [{}])[0]
    is_amd = trace.get("roctracer_version") or props.get("warpSize") == 64
    platform = "AMD" if is_amd else "NVIDIA"
    gpu_name = props.get("name", "MI300X" if is_amd else "Unknown GPU")

    # Get all kernel events
    events = trace.get("traceEvents", [])
    kernels = [e for e in events if e.get("cat") == "kernel"]

    # Group by correlation ID
    corr_groups: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for k in kernels:
        corr_id = k.get("args", {}).get("correlation")
        if corr_id is not None:
            corr_groups[corr_id].append(k)

    return platform, gpu_name, kernels, dict(corr_groups)


def _compute_group_signature(kernels: list[dict[str, Any]]) -> tuple:
    """Compute a hashable signature for a correlation group for O(1) lookups.

    This enables signature-based matching which is O(n) average instead of O(n²).

    Args:
        kernels: List of kernel events in the group

    Returns:
        Tuple of (size_bucket, has_attention, has_ffn, dominant_type)
    """
    counts = Counter(_classify_kernel_cached(k.get("name", "")) for k in kernels)
    dominant = counts.most_common(1)[0][0] if counts else "Other"
    size_bucket = len(kernels) // 10 * 10  # Round to nearest 10
    has_attn = any("attention" in k.get("name", "").lower() or "fmha" in k.get("name", "").lower() for k in kernels)
    has_ffn = any(
        any(x in k.get("name", "").lower() for x in ["cijk", "nvjet", "gemm"])
        for k in kernels
    )
    return (size_bucket, has_attn, has_ffn, dominant)


def _analyze_correlation_group(
    kernels: list[dict[str, Any]],
) -> tuple[dict[str, int], dict[str, float]]:
    """Analyze kernel composition within a correlation group.

    Args:
        kernels: List of kernel events in the group

    Returns:
        Tuple of (counts, timings) where counts maps kernel types to counts
        and timings maps kernel types to total duration in microseconds
    """
    counts: Counter[str] = Counter()
    timings: dict[str, float] = defaultdict(float)

    for k in kernels:
        kernel_type = _classify_kernel_cached(k.get("name", ""))
        counts[kernel_type] += 1
        timings[kernel_type] += k.get("dur", 0)

    return dict(counts), dict(timings)


def _match_correlation_groups(
    trace1_groups: dict[int, list[dict[str, Any]]],
    trace2_groups: dict[int, list[dict[str, Any]]],
    size_tolerance: float = 0.25,
) -> list[tuple[int, int]]:
    """Match correlation groups using hybrid signature + composition approach.

    Uses signature-based lookup for speed (O(n) average) but falls back to
    composition-based scoring for accuracy when multiple candidates exist.

    Args:
        trace1_groups: Trace 1 correlation groups
        trace2_groups: Trace 2 correlation groups
        size_tolerance: Groups match if sizes are within this fraction

    Returns:
        List of (trace1_corr_id, trace2_corr_id) pairs
    """
    matches = []
    used_trace2_ids: set[int] = set()

    # Pre-compute compositions for scoring (keeps original O(n) cost)
    trace1_comps = {id: _analyze_correlation_group(kernels)[0] for id, kernels in trace1_groups.items()}
    trace2_comps = {id: _analyze_correlation_group(kernels)[0] for id, kernels in trace2_groups.items()}

    # Build signature-based lookup for fast filtering (O(n))
    trace2_by_sig: dict[tuple, list[tuple[int, int]]] = defaultdict(list)
    for gid, kernels in trace2_groups.items():
        sig = _compute_group_signature(kernels)
        trace2_by_sig[sig].append((gid, len(kernels)))

    # Sort trace1 groups by size (largest first)
    trace1_sorted = sorted(trace1_groups.items(), key=lambda x: len(x[1]), reverse=True)

    # Match each trace1 group
    for trace1_id, trace1_kernels in trace1_sorted:
        trace1_size = len(trace1_kernels)
        trace1_comp = trace1_comps[trace1_id]
        sig = _compute_group_signature(trace1_kernels)

        # Fast lookup: get candidates with matching signature
        candidates = [
            (gid, size) for gid, size in trace2_by_sig.get(sig, [])
            if gid not in used_trace2_ids
        ]

        # Expand search to adjacent size buckets if needed
        if not candidates:
            for adj_size in [sig[0] - 10, sig[0] + 10]:
                adj_sig = (adj_size, sig[1], sig[2], sig[3])
                for gid, size in trace2_by_sig.get(adj_sig, []):
                    if gid not in used_trace2_ids:
                        candidates.append((gid, size))

        # Apply size tolerance filter
        min_size = trace1_size / (1 + size_tolerance)
        max_size = trace1_size * (1 + size_tolerance)
        candidates = [(gid, size) for gid, size in candidates if min_size <= size <= max_size]

        # Score by composition similarity (only for filtered candidates)
        if candidates:
            best_id = None
            best_score = float("inf")
            for gid, size in candidates:
                trace2_comp = trace2_comps[gid]
                shared_types = len(set(trace1_comp.keys()) & set(trace2_comp.keys()))
                score = abs(trace1_size - size) - (shared_types * 10)
                if score < best_score:
                    best_score = score
                    best_id = gid

            if best_id is not None:
                matches.append((trace1_id, best_id))
                used_trace2_ids.add(best_id)

    return matches


def _find_fusion_mappings(
    trace1_kernels: list[dict],
    trace2_kernels: list[dict],
    trace1_name: str = "Trace1",
    trace2_name: str = "Trace2",
) -> list[dict]:
    """Find fusion mappings by analyzing kernel execution sequence patterns.

    This function identifies when one platform runs multiple kernels separately
    while the other platform fuses them into a single kernel.

    Args:
        trace1_kernels: List of kernel events from first trace
        trace2_kernels: List of kernel events from second trace
        trace1_name: Name of first platform (e.g., "AMD")
        trace2_name: Name of second platform (e.g., "NVIDIA")

    Returns:
        List of mapping dictionaries, each containing:
            - fused_platform: Which platform fuses the operations
            - fused_kernel_type: The single fused kernel type
            - unfused_platform: Which platform runs them separately
            - unfused_sequence: List of kernel types run separately
            - pattern_count: How many times this pattern appears
            - pattern_confidence: Fraction of occurrences following this pattern
            - evidence: Human-readable description
    """
    from collections import defaultdict
    from wafer_core.lib.trace_compare.classifier import classify_kernel
    
    mappings = []

    # Sort kernels by timestamp
    trace1_sorted = sorted(trace1_kernels, key=lambda k: k.get('ts', 0))
    trace2_sorted = sorted(trace2_kernels, key=lambda k: k.get('ts', 0))

    # Classify all kernels
    trace1_types = [_classify_kernel_cached(k.get('name', '')) for k in trace1_sorted]
    trace2_types = [_classify_kernel_cached(k.get('name', '')) for k in trace2_sorted]

    # Find kernel types unique to each trace
    trace1_type_set = set(trace1_types)
    trace2_type_set = set(trace2_types)

    trace1_only = trace1_type_set - trace2_type_set
    trace2_only = trace2_type_set - trace1_type_set

    # For each unique type in trace1, find common sequence patterns
    for unique_type in trace1_only:
        # Find all occurrences of this type
        indices = [i for i, t in enumerate(trace1_types) if t == unique_type]

        if len(indices) < 5:  # Need enough samples to be meaningful
            continue

        # Analyze what comes before/after each occurrence
        before_types = defaultdict(int)

        for idx in indices:
            if idx > 0:
                before_types[trace1_types[idx - 1]] += 1

        # Find the most common pattern (e.g., "Attention → Reduce")
        most_common_before = max(before_types.items(), key=lambda x: x[1]) if before_types else (None, 0)

        # If there's a strong pattern (>80% of occurrences)
        if most_common_before[1] / len(indices) > 0.8:
            # This suggests: Trace2 likely fuses [before_type + unique_type] into [before_type]
            fusion_candidate = most_common_before[0]

            # Verify trace2 has this type
            if fusion_candidate in trace2_type_set:
                # Count occurrences to compare
                trace1_fusion_count = trace1_types.count(fusion_candidate)
                trace2_fusion_count = trace2_types.count(fusion_candidate)

                mappings.append({
                    "fused_platform": trace2_name,
                    "fused_kernel_type": fusion_candidate,
                    "fused_count": trace2_fusion_count,
                    "unfused_platform": trace1_name,
                    "unfused_sequence": [fusion_candidate, unique_type],
                    "unfused_count_per_type": {
                        fusion_candidate: trace1_fusion_count,
                        unique_type: len(indices)
                    },
                    "pattern_count": len(indices),
                    "pattern_confidence": most_common_before[1] / len(indices),
                    "evidence": f"{trace1_name} runs {fusion_candidate}+{unique_type} separately, {trace2_name} fuses into {fusion_candidate}"
                })

    # Also check trace2-only types
    for unique_type in trace2_only:
        indices = [i for i, t in enumerate(trace2_types) if t == unique_type]

        if len(indices) < 5:
            continue

        before_types = defaultdict(int)

        for idx in indices:
            if idx > 0:
                before_types[trace2_types[idx - 1]] += 1

        most_common_before = max(before_types.items(), key=lambda x: x[1]) if before_types else (None, 0)

        if most_common_before[1] / len(indices) > 0.8:
            fusion_candidate = most_common_before[0]

            if fusion_candidate in trace1_type_set:
                trace1_fusion_count = trace1_types.count(fusion_candidate)
                trace2_fusion_count = trace2_types.count(fusion_candidate)

                mappings.append({
                    "fused_platform": trace1_name,
                    "fused_kernel_type": fusion_candidate,
                    "fused_count": trace1_fusion_count,
                    "unfused_platform": trace2_name,
                    "unfused_sequence": [fusion_candidate, unique_type],
                    "unfused_count_per_type": {
                        fusion_candidate: trace2_fusion_count,
                        unique_type: len(indices)
                    },
                    "pattern_count": len(indices),
                    "pattern_confidence": most_common_before[1] / len(indices),
                    "evidence": f"{trace2_name} runs {fusion_candidate}+{unique_type} separately, {trace1_name} fuses into {fusion_candidate}"
                })

    # NEW: Check for partial fusion patterns (kernel exists on both platforms but with different counts)
    # If one platform has significantly fewer calls (>1.3x ratio), look for fusion patterns
    common_types = trace1_type_set & trace2_type_set

    for ktype in common_types:
        trace1_count = trace1_types.count(ktype)
        trace2_count = trace2_types.count(ktype)

        # Check if there's a significant imbalance (one has >1.3x more)
        if trace1_count == 0 or trace2_count == 0:
            continue

        ratio = max(trace1_count, trace2_count) / min(trace1_count, trace2_count)

        if ratio < 1.3 or trace1_count + trace2_count < 100:
            continue

        # Determine which platform has more (unfused) and which has fewer (fused)
        if trace1_count > trace2_count:
            # Trace1 has more separate calls, Trace2 likely fuses
            unfused_platform = trace1_name
            fused_platform = trace2_name
            unfused_count = trace1_count
            fused_count = trace2_count

            # Find what Trace2 might be fusing this into
            # Use the most common kernel type in Trace2 as a likely fusion target
            trace2_type_counts = defaultdict(int)
            for t in trace2_types:
                if t != ktype and t != "Other":  # Skip the imbalanced type itself and "Other"
                    trace2_type_counts[t] += 1

            if trace2_type_counts:
                # Use the most common type as the fusion target
                fusion_target = max(trace2_type_counts.items(), key=lambda x: x[1])[0]

                mappings.append({
                    "fused_platform": fused_platform,
                    "fused_kernel_type": fusion_target,
                    "fused_count": fused_count,
                    "unfused_platform": unfused_platform,
                    "unfused_sequence": [ktype],
                    "unfused_count_per_type": {
                        ktype: unfused_count
                    },
                    "pattern_count": unfused_count - fused_count,
                    "pattern_confidence": (unfused_count - fused_count) / unfused_count,
                    "evidence": f"{unfused_platform} calls {ktype} {ratio:.1f}x more ({unfused_count} vs {fused_count}), {fused_platform} likely fuses into {fusion_target}"
                })
        else:
            # Trace2 has more separate calls, Trace1 likely fuses
            unfused_platform = trace2_name
            fused_platform = trace1_name
            unfused_count = trace2_count
            fused_count = trace1_count

            # Find what Trace1 might be fusing this into
            # Use the most common kernel type in Trace1 as a likely fusion target
            trace1_type_counts = defaultdict(int)
            for t in trace1_types:
                if t != ktype and t != "Other":  # Skip the imbalanced type itself and "Other"
                    trace1_type_counts[t] += 1

            if trace1_type_counts:
                fusion_target = max(trace1_type_counts.items(), key=lambda x: x[1])[0]

                mappings.append({
                    "fused_platform": fused_platform,
                    "fused_kernel_type": fusion_target,
                    "fused_count": fused_count,
                    "unfused_platform": unfused_platform,
                    "unfused_sequence": [ktype],
                    "unfused_count_per_type": {
                        ktype: unfused_count
                    },
                    "pattern_count": unfused_count - fused_count,
                    "pattern_confidence": (unfused_count - fused_count) / unfused_count,
                    "evidence": f"{unfused_platform} calls {ktype} {ratio:.1f}x more ({unfused_count} vs {fused_count}), {fused_platform} likely fuses into {fusion_target}"
                })

    return mappings


def _detect_intra_type_fusion(
    trace1_kernels: list[dict],
    trace2_kernels: list[dict],
    trace1_name: str,
    trace2_name: str,
) -> list[dict]:
    """Detect intra-type fusion where consecutive same-type kernels are fused.

    Example: AMD runs Sort→Sort→Sort (42 calls) while NVIDIA runs Sort→Sort (10 calls)
    This indicates NVIDIA has a more efficient Sort implementation that fuses operations.
    """
    from wafer_core.lib.trace_compare.classifier import classify_kernel

    def analyze_chains(kernels):
        """Find chains of consecutive same-type kernels"""
        sorted_kernels = sorted(kernels, key=lambda k: k.get('ts', 0))
        types = [_classify_kernel_cached(k['name']) for k in sorted_kernels]

        chains = defaultdict(list)
        i = 0
        while i < len(types):
            ktype = types[i]
            count = 0
            while i < len(types) and types[i] == ktype:
                count += 1
                i += 1
            chains[ktype].append(count)

        return chains

    trace1_chains = analyze_chains(trace1_kernels)
    trace2_chains = analyze_chains(trace2_kernels)

    mappings = []
    all_types = set(trace1_chains.keys()) | set(trace2_chains.keys())

    for ktype in all_types:
        t1_lengths = trace1_chains.get(ktype, [])
        t2_lengths = trace2_chains.get(ktype, [])

        # Skip if not enough data
        if len(t1_lengths) < 5 and len(t2_lengths) < 5:
            continue

        # Filter to chains with multiple kernels
        t1_multi = [l for l in t1_lengths if l > 1]
        t2_multi = [l for l in t2_lengths if l > 1]

        if not t1_multi and not t2_multi:
            continue

        t1_total = sum(t1_lengths)
        t2_total = sum(t2_lengths)
        t1_chains = len(t1_multi) if t1_multi else len(t1_lengths)
        t2_chains = len(t2_multi) if t2_multi else len(t2_lengths)

        if t1_chains == 0 or t2_chains == 0:
            continue

        t1_avg_chain = sum(t1_multi) / len(t1_multi) if t1_multi else 1.0
        t2_avg_chain = sum(t2_multi) / len(t2_multi) if t2_multi else 1.0

        chain_ratio = max(t1_avg_chain, t2_avg_chain) / min(t1_avg_chain, t2_avg_chain)

        # Significant intra-fusion if chains are 2x+ different
        if chain_ratio > 2.0 and abs(t1_total - t2_total) > 100:
            if t1_avg_chain > t2_avg_chain:
                unfused_platform = trace1_name
                fused_platform = trace2_name
                unfused_chains = t1_chains
                fused_chains = t2_chains
                unfused_avg = t1_avg_chain
                fused_avg = t2_avg_chain
                unfused_total = t1_total
                fused_total = t2_total
            else:
                unfused_platform = trace2_name
                fused_platform = trace1_name
                unfused_chains = t2_chains
                fused_chains = t1_chains
                unfused_avg = t2_avg_chain
                fused_avg = t1_avg_chain
                unfused_total = t2_total
                fused_total = t1_total

            mappings.append({
                "fused_platform": fused_platform,
                "fused_kernel_type": ktype,
                "fused_count": fused_total,
                "unfused_platform": unfused_platform,
                "unfused_sequence": [ktype, ktype],  # Same type repeated
                "unfused_count_per_type": {ktype: unfused_total},
                "pattern_count": unfused_total - fused_total,
                "pattern_confidence": min(unfused_chains, fused_chains) / max(unfused_chains, fused_chains),
                "evidence": f"{unfused_platform} runs {ktype} in chains of {unfused_avg:.0f} calls ({unfused_chains} chains, {unfused_total:,} total), {fused_platform} fuses to {fused_avg:.0f} calls ({fused_chains} chains, {fused_total:,} total) - {chain_ratio:.1f}x more efficient"
            })

    return mappings


def _find_partial_fusion_via_groups(
    trace1_large: dict[int, list[dict]],
    trace2_large: dict[int, list[dict]],
    matches: list[tuple[int, int]],
    trace1_name: str,
    trace2_name: str,
) -> list[dict]:
    """Find partial fusion patterns by analyzing correlation group differences.

    When one platform has fewer of a kernel type, check what kernel types the
    other platform has MORE of in those same groups - those are likely fusion targets.
    """
    from collections import Counter
    from wafer_core.lib.trace_compare.classifier import classify_kernel

    mappings = []

    # For each matched pair, track kernel type counts
    trace1_all_types = []
    trace2_all_types = []

    for trace1_cid, trace2_cid in matches:
        trace1_ktypes = [_classify_kernel_cached(k.get("name", "")) for k in trace1_large[trace1_cid]]
        trace2_ktypes = [_classify_kernel_cached(k.get("name", "")) for k in trace2_large[trace2_cid]]
        trace1_all_types.extend(trace1_ktypes)
        trace2_all_types.extend(trace2_ktypes)

    # Find kernel types with significant imbalances
    trace1_counts = Counter(trace1_all_types)
    trace2_counts = Counter(trace2_all_types)
    all_types = set(trace1_counts.keys()) | set(trace2_counts.keys())

    for ktype in all_types:
        trace1_count = trace1_counts.get(ktype, 0)
        trace2_count = trace2_counts.get(ktype, 0)

        if trace1_count == 0 or trace2_count == 0:
            continue  # Handled by sequence-based detection

        ratio = max(trace1_count, trace2_count) / min(trace1_count, trace2_count)

        if ratio < 1.3 or trace1_count + trace2_count < 100:
            continue  # Not significant

        # Determine which platform has fewer (fuses more)
        if trace1_count > trace2_count:
            unfused_platform = trace1_name
            fused_platform = trace2_name
            unfused_count = trace1_count
            fused_count = trace2_count

            # Find groups where trace1 has this kernel but trace2 doesn't
            fusion_targets = Counter()
            groups_analyzed = 0

            for trace1_cid, trace2_cid in matches:
                trace1_ktypes = [_classify_kernel_cached(k.get("name", "")) for k in trace1_large[trace1_cid]]
                trace2_ktypes = [_classify_kernel_cached(k.get("name", "")) for k in trace2_large[trace2_cid]]

                trace1_has = ktype in trace1_ktypes
                trace2_has = ktype in trace2_ktypes

                if trace1_has and not trace2_has:
                    # What does trace2 have MORE of in this group?
                    trace1_kcounts = Counter(trace1_ktypes)
                    trace2_kcounts = Counter(trace2_ktypes)

                    for other_type in set(trace2_kcounts.keys()):
                        if other_type == ktype or other_type == "Other":
                            continue
                        diff = trace2_kcounts[other_type] - trace1_kcounts.get(other_type, 0)
                        if diff > 0:
                            fusion_targets[other_type] += diff

                    groups_analyzed += 1

            if fusion_targets and groups_analyzed >= 5:
                # Report top fusion targets
                top_targets = fusion_targets.most_common(3)
                target_str = ", ".join(f"{t[0]} (+{t[1]})" for t in top_targets)

                mappings.append({
                    "fused_platform": fused_platform,
                    "fused_kernel_type": top_targets[0][0],
                    "fused_count": fused_count,
                    "unfused_platform": unfused_platform,
                    "unfused_sequence": [ktype],
                    "unfused_count_per_type": {ktype: unfused_count},
                    "pattern_count": unfused_count - fused_count,
                    "pattern_confidence": groups_analyzed / len(matches) if matches else 0,
                    "evidence": f"{unfused_platform} calls {ktype} {ratio:.1f}x more ({unfused_count} vs {fused_count}). In {groups_analyzed} groups where {unfused_platform} has {ktype}, {fused_platform} has more: {target_str}"
                })
        else:
            # Symmetric case for trace2 > trace1
            unfused_platform = trace2_name
            fused_platform = trace1_name
            unfused_count = trace2_count
            fused_count = trace1_count

            fusion_targets = Counter()
            groups_analyzed = 0

            for trace1_cid, trace2_cid in matches:
                trace1_ktypes = [_classify_kernel_cached(k.get("name", "")) for k in trace1_large[trace1_cid]]
                trace2_ktypes = [_classify_kernel_cached(k.get("name", "")) for k in trace2_large[trace2_cid]]

                trace1_has = ktype in trace1_ktypes
                trace2_has = ktype in trace2_ktypes

                if trace2_has and not trace1_has:
                    trace1_kcounts = Counter(trace1_ktypes)
                    trace2_kcounts = Counter(trace2_ktypes)

                    for other_type in set(trace1_kcounts.keys()):
                        if other_type == ktype or other_type == "Other":
                            continue
                        diff = trace1_kcounts[other_type] - trace2_kcounts.get(other_type, 0)
                        if diff > 0:
                            fusion_targets[other_type] += diff

                    groups_analyzed += 1

            if fusion_targets and groups_analyzed >= 5:
                top_targets = fusion_targets.most_common(3)
                target_str = ", ".join(f"{t[0]} (+{t[1]})" for t in top_targets)

                mappings.append({
                    "fused_platform": fused_platform,
                    "fused_kernel_type": top_targets[0][0],
                    "fused_count": fused_count,
                    "unfused_platform": unfused_platform,
                    "unfused_sequence": [ktype],
                    "unfused_count_per_type": {ktype: unfused_count},
                    "pattern_count": unfused_count - fused_count,
                    "pattern_confidence": groups_analyzed / len(matches) if matches else 0,
                    "evidence": f"{unfused_platform} calls {ktype} {ratio:.1f}x more ({unfused_count} vs {fused_count}). In {groups_analyzed} groups where {unfused_platform} has {ktype}, {fused_platform} has more: {target_str}"
                })

    return mappings


def analyze_fusion_differences(
    amd_trace_path: str | Path,
    nv_trace_path: str | Path,
    min_group_size: int = 50,
) -> dict[str, Any]:
    """Main fusion analysis function.

    Args:
        amd_trace_path: Path to AMD trace
        nv_trace_path: Path to NVIDIA trace
        min_group_size: Only analyze correlation groups with at least this many kernels

    Returns:
        Dictionary with analysis results containing:
            - metadata: trace info
            - global_counts: kernel type distribution across entire trace
            - fusion_opportunities: significant fusion differences
            - fusion_mappings: actual kernel-to-kernel mappings (NEW)
    """
    # Load traces (maintain order - don't swap)
    trace1_platform, trace1_gpu, trace1_kernels, trace1_corr_groups = _load_trace_for_fusion(
        amd_trace_path
    )
    trace2_platform, trace2_gpu, trace2_kernels, trace2_corr_groups = _load_trace_for_fusion(
        nv_trace_path
    )

    # Override platform names with generic "Trace 1" and "Trace 2" for UI consistency
    trace1_platform = "Trace 1"
    trace2_platform = "Trace 2"

    # Filter to "significant" correlation groups
    trace1_large = {
        cid: kernels
        for cid, kernels in trace1_corr_groups.items()
        if len(kernels) >= min_group_size
    }
    trace2_large = {
        cid: kernels
        for cid, kernels in trace2_corr_groups.items()
        if len(kernels) >= min_group_size
    }

    # Match correlation groups between platforms
    matches = _match_correlation_groups(trace1_large, trace2_large)

    # Analyze differences in matched groups
    fusion_diffs: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "trace1_count": 0,
            "trace2_count": 0,
            "trace1_time_us": 0,
            "trace2_time_us": 0,
            "groups_with_diff": 0,
            "total_groups": 0,
        }
    )

    # NEW: Collect actual fusion mappings
    all_fusion_mappings = []

    for trace1_cid, trace2_cid in matches:
        trace1_comp, trace1_times = _analyze_correlation_group(trace1_large[trace1_cid])
        trace2_comp, trace2_times = _analyze_correlation_group(trace2_large[trace2_cid])

        # Find all kernel types in either platform
        all_types = set(trace1_comp.keys()) | set(trace2_comp.keys())

        for ktype in all_types:
            trace1_count = trace1_comp.get(ktype, 0)
            trace2_count = trace2_comp.get(ktype, 0)
            trace1_time = trace1_times.get(ktype, 0)
            trace2_time = trace2_times.get(ktype, 0)

            fusion_diffs[ktype]["trace1_count"] += trace1_count
            fusion_diffs[ktype]["trace2_count"] += trace2_count
            fusion_diffs[ktype]["trace1_time_us"] += trace1_time
            fusion_diffs[ktype]["trace2_time_us"] += trace2_time
            fusion_diffs[ktype]["total_groups"] += 1

            if trace1_count != trace2_count:
                fusion_diffs[ktype]["groups_with_diff"] += 1

        # NEW: Find actual kernel mappings in this correlation group
        group_mappings = _find_fusion_mappings(
            trace1_large[trace1_cid],
            trace2_large[trace2_cid],
            trace1_name=trace1_platform,
            trace2_name=trace2_platform
        )
        # Add correlation ID context to each mapping
        for mapping in group_mappings:
            mapping["correlation_group_trace1"] = trace1_cid
            mapping["correlation_group_trace2"] = trace2_cid
        all_fusion_mappings.extend(group_mappings)

    # Also get global counts for context
    global_trace1_counts: Counter[str] = Counter(
        [_classify_kernel_cached(k.get("name", "")) for k in trace1_kernels]
    )
    global_trace2_counts: Counter[str] = Counter(
        [_classify_kernel_cached(k.get("name", "")) for k in trace2_kernels]
    )

    # Build results
    results: dict[str, Any] = {
        "metadata": {
            "trace1_gpu": trace1_gpu,
            "trace2_gpu": trace2_gpu,
            "trace1_total_kernels": len(trace1_kernels),
            "trace2_total_kernels": len(trace2_kernels),
            "trace1_correlation_groups": len(trace1_large),
            "trace2_correlation_groups": len(trace2_large),
            "matched_groups": len(matches),
        },
        "global_counts": {},
        "fusion_opportunities": [],
        "fusion_mappings": all_fusion_mappings,  # NEW: Include actual mappings
    }

    # Global counts for all kernel types
    all_ktypes = set(global_trace1_counts.keys()) | set(global_trace2_counts.keys())
    for ktype in all_ktypes:
        trace1_total = global_trace1_counts.get(ktype, 0)
        trace2_total = global_trace2_counts.get(ktype, 0)

        if trace1_total > 0 or trace2_total > 0:
            results["global_counts"][ktype] = {
                "trace1_count": trace1_total,
                "trace2_count": trace2_total,
                "ratio": trace1_total / trace2_total if trace2_total > 0 else float("inf"),
            }

    # Fusion opportunities from matched correlation groups
    for ktype, stats in fusion_diffs.items():
        trace1_avg = (
            stats["trace1_count"] / stats["total_groups"]
            if stats["total_groups"] > 0
            else 0
        )
        trace2_avg = (
            stats["trace2_count"] / stats["total_groups"]
            if stats["total_groups"] > 0
            else 0
        )
        trace1_time_ms = stats["trace1_time_us"] / 1000
        trace2_time_ms = stats["trace2_time_us"] / 1000

        # Calculate significance
        diff_ratio = trace1_avg / trace2_avg if trace2_avg > 0 else float("inf")
        reverse_ratio = trace2_avg / trace1_avg if trace1_avg > 0 else float("inf")

        # Only report if there's a significant difference
        # Either: one platform has it and the other doesn't (ratio > 10)
        # Or: one platform has significantly more (ratio > 2.0)
        is_significant = (
            (diff_ratio > 10.0 or reverse_ratio > 10.0)
            or (  # One platform doesn't have it
                (diff_ratio > 2.0 or reverse_ratio > 2.0)
                and stats["trace1_count"] + stats["trace2_count"] > 20  # Significant difference  # Not trivial counts
            )
        )

        if is_significant:
            # Determine who fuses (who has FEWER calls = more fusion)
            if diff_ratio > 1.5:
                fused_by = "Trace 2"  # Trace 2 has fewer calls, so it fuses more
                ratio = diff_ratio
            else:
                fused_by = "Trace 1"  # Trace 1 has fewer calls, so it fuses more
                ratio = reverse_ratio

            # Calculate time ratio (who's faster for this operation)
            time_ratio = trace1_time_ms / trace2_time_ms if trace2_time_ms > 0 else float("inf")

            results["fusion_opportunities"].append(
                {
                    "kernel_type": ktype,
                    "trace1_total": stats["trace1_count"],
                    "trace2_total": stats["trace2_count"],
                    "trace1_avg_per_group": trace1_avg,
                    "trace2_avg_per_group": trace2_avg,
                    "trace1_time_ms": trace1_time_ms,
                    "trace2_time_ms": trace2_time_ms,
                    "time_ratio": time_ratio,
                    "ratio": ratio,
                    "fused_by": fused_by,
                    "groups_affected": stats["groups_with_diff"],
                    "total_groups": stats["total_groups"],
                }
            )

    # ADDITIONAL: Check global counts for significant differences not captured above
    # This catches patterns like Sort that may be in small groups or distributed differently
    for ktype in all_ktypes:
        # Skip if already added from correlation group analysis
        if any(opp["kernel_type"] == ktype for opp in results["fusion_opportunities"]):
            continue

        trace1_total = global_trace1_counts.get(ktype, 0)
        trace2_total = global_trace2_counts.get(ktype, 0)

        # Skip trivial counts
        if trace1_total + trace2_total < 100:
            continue

        # Calculate global ratio
        global_ratio = trace1_total / trace2_total if trace2_total > 0 else float("inf")
        global_reverse_ratio = trace2_total / trace1_total if trace1_total > 0 else float("inf")

        # Check if globally significant (more aggressive threshold for comprehensive detection)
        is_globally_significant = (
            (global_ratio > 2.0 or global_reverse_ratio > 2.0)
            and (trace1_total + trace2_total > 100)
        )

        if is_globally_significant:
            # Get timing info from all kernels (not just matched groups)
            trace1_time = sum(
                k.get("dur", 0) for k in trace1_kernels
                if _classify_kernel_cached(k.get("name", "")) == ktype
            ) / 1000  # Convert to ms
            trace2_time = sum(
                k.get("dur", 0) for k in trace2_kernels
                if _classify_kernel_cached(k.get("name", "")) == ktype
            ) / 1000

            # Determine who fuses (who has FEWER calls = more fusion)
            if global_ratio > 1.5:
                fused_by = "Trace 2"  # Trace 2 has fewer calls
                ratio = global_ratio
            else:
                fused_by = "Trace 1"  # Trace 1 has fewer calls
                ratio = global_reverse_ratio

            time_ratio = trace1_time / trace2_time if trace2_time > 0 else float("inf")

            results["fusion_opportunities"].append(
                {
                    "kernel_type": ktype,
                    "trace1_total": trace1_total,
                    "trace2_total": trace2_total,
                    "trace1_avg_per_group": trace1_total / len(matches) if matches else 0,
                    "trace2_avg_per_group": trace2_total / len(matches) if matches else 0,
                    "trace1_time_ms": trace1_time,
                    "trace2_time_ms": trace2_time,
                    "time_ratio": time_ratio,
                    "ratio": ratio,
                    "fused_by": fused_by,
                    "groups_affected": 0,  # Unknown for global analysis
                    "total_groups": len(matches),
                }
            )

    # Sort by impact (ratio * total count)
    results["fusion_opportunities"].sort(
        key=lambda x: x["ratio"] * (x["trace1_total"] + x["trace2_total"]), reverse=True
    )

    # ADD PARTIAL FUSION MAPPINGS using correlation group differential analysis
    # This catches patterns like Sort that exist on both platforms but with different frequencies
    partial_mappings = _find_partial_fusion_via_groups(
        trace1_large,
        trace2_large,
        matches,
        trace1_name=trace1_platform,
        trace2_name=trace2_platform
    )
    all_fusion_mappings.extend(partial_mappings)

    # DETECT INTRA-TYPE FUSION (same kernel type fused with itself, like Sort chains)
    # Do this FIRST since it's more accurate than the fallback global analysis
    intra_mappings = _detect_intra_type_fusion(
        trace1_kernels,
        trace2_kernels,
        trace1_name=trace1_platform,
        trace2_name=trace2_platform
    )
    all_fusion_mappings.extend(intra_mappings)

    # Collect kernel types already handled by intra-type fusion
    intra_handled_types = set(m["fused_kernel_type"] for m in intra_mappings)

    # ALSO ADD GLOBAL FUSION MAPPINGS for kernels not in large correlation groups
    # Skip types already handled by intra-type fusion (more accurate)
    global_mappings = _find_fusion_mappings(
        trace1_kernels,
        trace2_kernels,
        trace1_name=trace1_platform,
        trace2_name=trace2_platform
    )
    # Filter: skip if already handled or if evidence is duplicate
    existing_evidence = set(m["evidence"] for m in all_fusion_mappings)
    for mapping in global_mappings:
        ktype = mapping["unfused_sequence"][0] if mapping["unfused_sequence"] else None
        if ktype not in intra_handled_types and mapping["evidence"] not in existing_evidence:
            all_fusion_mappings.append(mapping)

    return results
