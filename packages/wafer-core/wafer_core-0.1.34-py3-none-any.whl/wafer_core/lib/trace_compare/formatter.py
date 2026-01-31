"""Report formatting for trace comparison results.

Provides text, CSV, and JSON output formatters for comparison and fusion analysis.
"""

import json
from typing import Any


def format_text(results: dict[str, Any], show_layers: bool = False, show_all: bool = False, show_stack_traces: bool = False) -> str:
    """Format comparison results as human-readable text report.

    Args:
        results: Analysis results from analyze_traces()
        show_layers: Whether to include layer-wise breakdown
        show_all: Whether to show all items without truncation
        show_stack_traces: Whether to show Python stack traces

    Returns:
        Formatted text report
    """
    lines = []
    meta = results["metadata"]

    lines.append("=" * 80)
    lines.append("VLLM TRACE COMPARISON REPORT")
    if "phase" in meta and meta["phase"] != "all":
        lines.append(f"Phase: {meta['phase'].upper()}")
    lines.append("=" * 80)
    lines.append("")

    # Determine which trace is AMD and which is NVIDIA
    is_trace1_amd = meta['trace1_platform'] == 'AMD'
    if is_trace1_amd:
        amd_gpu, nvidia_gpu = meta['trace1_gpu'], meta['trace2_gpu']
        amd_kernels, nvidia_kernels = meta['trace1_kernels'], meta['trace2_kernels']
        amd_total_ms, nvidia_total_ms = meta['trace1_total_ms'], meta['trace2_total_ms']
    else:
        amd_gpu, nvidia_gpu = meta['trace2_gpu'], meta['trace1_gpu']
        amd_kernels, nvidia_kernels = meta['trace2_kernels'], meta['trace1_kernels']
        amd_total_ms, nvidia_total_ms = meta['trace2_total_ms'], meta['trace1_total_ms']

    # Get device properties
    amd_dev = meta['trace1_device'] if is_trace1_amd else meta['trace2_device']
    nvidia_dev = meta['trace2_device'] if is_trace1_amd else meta['trace1_device']

    lines.append(f"AMD GPU:      {amd_gpu}")
    lines.append(f"  Compute:    {amd_dev['compute_capability']}")
    lines.append(f"  Memory:     {amd_dev['total_memory_gb']:.1f} GB")
    lines.append(f"  SMs:        {amd_dev['sm_count']}")
    lines.append(f"  Warp Size:  {amd_dev['warp_size']}")
    lines.append("")
    lines.append(f"NVIDIA GPU:   {nvidia_gpu}")
    lines.append(f"  Compute:    {nvidia_dev['compute_capability']}")
    lines.append(f"  Memory:     {nvidia_dev['total_memory_gb']:.1f} GB")
    lines.append(f"  SMs:        {nvidia_dev['sm_count']}")
    lines.append(f"  Warp Size:  {nvidia_dev['warp_size']}")
    lines.append("")
    lines.append(f"AMD Kernels:  {amd_kernels:,}")
    lines.append(f"NVIDIA Kernels: {nvidia_kernels:,}")
    lines.append(f"AMD Total:    {amd_total_ms:.1f} ms")
    lines.append(f"NVIDIA Total: {nvidia_total_ms:.1f} ms")

    # Handle division by zero for ratio
    if nvidia_total_ms > 0:
        ratio_str = f"{amd_total_ms / nvidia_total_ms:.2f}x"
    elif amd_total_ms > 0:
        ratio_str = "∞ (NVIDIA has no data)"
    else:
        ratio_str = "N/A (both traces empty)"

    lines.append(f"Ratio:        {ratio_str}")
    lines.append("")

    # Convert operations from trace1/trace2 keys to amd/nvidia keys for easier formatting
    ops = results["operations"]
    for op in ops:
        if is_trace1_amd:
            op['amd_count'] = op['trace1_count']
            op['nvidia_count'] = op['trace2_count']
            op['amd_avg_us'] = op['trace1_avg_us']
            op['nvidia_avg_us'] = op['trace2_avg_us']
            op['amd_total_ms'] = op['trace1_total_ms']
            op['nvidia_total_ms'] = op['trace2_total_ms']
            op['amd_cpu_op'] = op.get('trace1_cpu_op')
            op['nvidia_cpu_op'] = op.get('trace2_cpu_op')
            op['amd_pattern'] = op.get('trace1_pattern')
            op['nvidia_pattern'] = op.get('trace2_pattern')
            op['amd_kernels'] = op.get('trace1_kernels', [])
            op['nvidia_kernels'] = op.get('trace2_kernels', [])
        else:
            op['amd_count'] = op['trace2_count']
            op['nvidia_count'] = op['trace1_count']
            op['amd_avg_us'] = op['trace2_avg_us']
            op['nvidia_avg_us'] = op['trace1_avg_us']
            op['amd_total_ms'] = op['trace2_total_ms']
            op['nvidia_total_ms'] = op['trace1_total_ms']
            op['amd_cpu_op'] = op.get('trace2_cpu_op')
            op['nvidia_cpu_op'] = op.get('trace1_cpu_op')
            op['amd_pattern'] = op.get('trace2_pattern')
            op['nvidia_pattern'] = op.get('trace1_pattern')
            op['amd_kernels'] = op.get('trace2_kernels', [])
            op['nvidia_kernels'] = op.get('trace1_kernels', [])

    # Convert layers from trace1/trace2 keys to amd/nvidia keys
    layers = results.get("layers", [])
    for layer in layers:
        if is_trace1_amd:
            layer['amd_kernels'] = layer['trace1_kernels']
            layer['nvidia_kernels'] = layer['trace2_kernels']
            layer['amd_total_ms'] = layer['trace1_total_ms']
            layer['nvidia_total_ms'] = layer['trace2_total_ms']
        else:
            layer['amd_kernels'] = layer['trace2_kernels']
            layer['nvidia_kernels'] = layer['trace1_kernels']
            layer['amd_total_ms'] = layer['trace2_total_ms']
            layer['nvidia_total_ms'] = layer['trace1_total_ms']

    # Update metadata layer counts
    if is_trace1_amd:
        meta['amd_layers'] = meta.get('trace1_layers', 0)
        meta['nvidia_layers'] = meta.get('trace2_layers', 0)
    else:
        meta['amd_layers'] = meta.get('trace2_layers', 0)
        meta['nvidia_layers'] = meta.get('trace1_layers', 0)

    # Summary stats
    slower = [o for o in ops if o["status"] == "slower"]
    faster = [o for o in ops if o["status"] == "faster"]
    similar = [o for o in ops if o["status"] == "similar"]

    lines.append("SUMMARY")
    lines.append("-" * 80)
    lines.append(f"Operations where AMD is slower:  {len(slower)}")
    lines.append(f"Operations where AMD is faster:  {len(faster)}")
    lines.append(f"Operations with similar perf:    {len(similar)}")
    lines.append("")

    # AMD Slower
    if slower:
        slower_to_show = slower if show_all else slower[:10]
        lines.append(f"🔴 AMD SLOWER THAN NVIDIA (Optimization Targets) - Showing {len(slower_to_show)}/{len(slower)}")
        lines.append("=" * 140)
        lines.append(
            f"{'Operation':<22} {'AMD Count':>11} {'NV Count':>10} {'AMD Avg':>10} "
            f"{'NV Avg':>10} {'Ratio':>8} {'AMD Total':>11} {'NV Total':>11} {'AMD Slower By':>14}"
        )
        lines.append("-" * 140)

        for op in slower_to_show:
            diff_abs = abs(op["gap_ms"])
            lines.append(
                f"{op['operation']:<22} "
                f"{op['amd_count']:>11,} "
                f"{op['nvidia_count']:>10,} "
                f"{op['amd_avg_us']:>8.1f}µs "
                f"{op['nvidia_avg_us']:>8.1f}µs "
                f"{op['ratio']:>7.2f}x "
                f"{op['amd_total_ms']:>9.1f}ms "
                f"{op['nvidia_total_ms']:>9.1f}ms "
                f"{diff_abs:>13.1f}ms"
            )

        lines.append("")

    # AMD Faster
    if faster:
        faster_to_show = faster if show_all else faster[:10]
        lines.append(f"🟢 AMD FASTER THAN NVIDIA (Wins) - Showing {len(faster_to_show)}/{len(faster)}")
        lines.append("=" * 140)
        lines.append(
            f"{'Operation':<22} {'AMD Count':>11} {'NV Count':>10} {'AMD Avg':>10} "
            f"{'NV Avg':>10} {'Ratio':>8} {'AMD Total':>11} {'NV Total':>11} {'AMD Faster By':>14}"
        )
        lines.append("-" * 140)

        for op in faster_to_show:
            diff_abs = abs(op["gap_ms"])
            lines.append(
                f"{op['operation']:<22} "
                f"{op['amd_count']:>11,} "
                f"{op['nvidia_count']:>10,} "
                f"{op['amd_avg_us']:>8.1f}µs "
                f"{op['nvidia_avg_us']:>8.1f}µs "
                f"{op['ratio']:>7.2f}x "
                f"{op['amd_total_ms']:>9.1f}ms "
                f"{op['nvidia_total_ms']:>9.1f}ms "
                f"{diff_abs:>13.1f}ms"
            )

        lines.append("")

    # Similar Performance
    if similar:
        lines.append("⚪ SIMILAR PERFORMANCE (Within 10% difference)")
        lines.append("=" * 140)
        lines.append(
            f"{'Operation':<22} {'AMD Count':>11} {'NV Count':>10} {'AMD Avg':>10} "
            f"{'NV Avg':>10} {'Ratio':>8} {'AMD Total':>11} {'NV Total':>11} {'Winner':>14}"
        )
        lines.append("-" * 140)

        for op in similar:
            if op["gap_ms"] < 0:
                winner = f"AMD by {abs(op['gap_ms']):.1f}ms"
            elif op["gap_ms"] > 0:
                winner = f"NV by {op['gap_ms']:.1f}ms"
            else:
                winner = "Tie"
            lines.append(
                f"{op['operation']:<22} "
                f"{op['amd_count']:>11,} "
                f"{op['nvidia_count']:>10,} "
                f"{op['amd_avg_us']:>8.1f}µs "
                f"{op['nvidia_avg_us']:>8.1f}µs "
                f"{op['ratio']:>7.2f}x "
                f"{op['amd_total_ms']:>9.1f}ms "
                f"{op['nvidia_total_ms']:>9.1f}ms "
                f"{winner:>14}"
            )

        lines.append("")

    # CPU operator mapping with stack trace info
    if not show_stack_traces:
        cpu_ops_to_show = ops if show_all else ops[:15]
        lines.append(f"CPU OPERATOR MAPPING - Showing {len(cpu_ops_to_show)}/{len(ops)}")
        lines.append("=" * 80)
        lines.append("Shows the most common PyTorch/vLLM call path for each GPU operation.")
        lines.append("Use --stack-traces to see full call stacks and all variants.")
        lines.append("")
        lines.append(f"{'Operation':<25} {'CPU Operator (most common)':<45} {'Variants':<10}")
        lines.append("-" * 80)

        # Track if any operations have multiple stack traces
        has_multiple_stacks = False
        for op in cpu_ops_to_show:
            cpu_op = op.get("amd_cpu_op") or op.get("nvidia_cpu_op", "N/A")
            if cpu_op and cpu_op != "N/A":
                # Shorten long operator names
                if len(cpu_op) > 43:
                    cpu_op = cpu_op[:40] + "..."

                # Count unique stack traces across both traces
                amd_stacks = op.get("trace1_python_stacks", []) if is_trace1_amd else op.get("trace2_python_stacks", [])
                nv_stacks = op.get("trace2_python_stacks", []) if is_trace1_amd else op.get("trace1_python_stacks", [])
                total_stacks = len(amd_stacks) + len(nv_stacks)

                stack_info = ""
                if total_stacks > 1:
                    stack_info = f"{total_stacks} paths"
                    has_multiple_stacks = True
                elif total_stacks == 1:
                    stack_info = "1 path"
                else:
                    stack_info = "-"

                lines.append(f"{op['operation']:<25} {cpu_op:<45} {stack_info:<10}")

        lines.append("")
        if has_multiple_stacks:
            lines.append("⚠️  Multiple call paths detected. Use --stack-traces to see all variants.")
        lines.append("")

    # Kernel-level details for top 3 operations with biggest gaps
    non_similar_ops = [op for op in ops if op["status"] != "similar"]
    top_ops = non_similar_ops if show_all else non_similar_ops[:3]

    lines.append("KERNEL-LEVEL DETAILS (Top Individual Kernels)")
    lines.append("=" * 80)
    lines.append("")
    if show_all:
        lines.append(f"Showing all kernels for {len(top_ops)} operations with performance gaps:")
    else:
        lines.append(f"Showing top 10 kernels for the 3 operations with largest performance gaps:")
    lines.append("")

    for op in top_ops:
        lines.append(f"Operation: {op['operation']}")
        lines.append("-" * 80)

        # AMD kernels
        all_amd_kernels = op.get("amd_kernels", [])
        amd_kernels = all_amd_kernels if show_all else all_amd_kernels[:10]
        if amd_kernels:
            kernel_label = f"All {len(amd_kernels)}" if show_all else "Top 10"
            lines.append(f"\n  AMD {kernel_label} Kernels (Total: {op['amd_count']} invocations):")
            lines.append(f"  {'Kernel Name':<50} {'Total (µs)':>12} {'Count':>8} {'Avg (µs)':>10}")
            lines.append("  " + "-" * 80)
            for k in amd_kernels:
                name = k["name"][:47] + "..." if len(k["name"]) > 50 else k["name"]
                lines.append(
                    f"  {name:<50} {k['total_us']:>12.0f} {k['count']:>8,} {k['avg_us']:>10.1f}"
                )

        # NVIDIA kernels
        all_nv_kernels = op.get("nvidia_kernels", [])
        nv_kernels = all_nv_kernels if show_all else all_nv_kernels[:10]
        if nv_kernels:
            kernel_label = f"All {len(nv_kernels)}" if show_all else "Top 10"
            lines.append(f"\n  NVIDIA {kernel_label} Kernels (Total: {op['nvidia_count']} invocations):")
            lines.append(f"  {'Kernel Name':<50} {'Total (µs)':>12} {'Count':>8} {'Avg (µs)':>10}")
            lines.append("  " + "-" * 80)
            for k in nv_kernels:
                name = k["name"][:47] + "..." if len(k["name"]) > 50 else k["name"]
                lines.append(
                    f"  {name:<50} {k['total_us']:>12.0f} {k['count']:>8,} {k['avg_us']:>10.1f}"
                )

        lines.append("")

    lines.append("=" * 80)

    # Python stack traces if requested
    if show_stack_traces:
        stack_trace_report = _format_stack_trace_report(results, show_all=show_all)
        lines.append("")
        lines.extend(stack_trace_report)

    # Layer-wise report if requested
    if show_layers:
        layer_report = _format_layer_report(results, show_all=show_all)
        lines.append("")
        lines.extend(layer_report)

    return "\n".join(lines)


def _format_layer_report(results: dict[str, Any], show_all: bool = False) -> list[str]:
    """Format layer-wise performance breakdown.

    Args:
        results: Analysis results
        show_all: Whether to show all layers without truncation

    Returns:
        List of formatted text lines
    """
    layers = results.get("layers", [])
    if not layers:
        return []

    lines = []
    meta = results["metadata"]

    lines.append("=" * 80)
    lines.append("LAYER-WISE PERFORMANCE BREAKDOWN")
    lines.append("=" * 80)
    lines.append("")
    lines.append("NOTE: Layers are identified by correlation IDs in the execution graph.")
    lines.append("Each layer represents one transformer block (Norm + Attention + FFN).")
    lines.append("Layers may have similar timing if the workload is uniform across the model.")
    lines.append("")

    lines.append(f"Total Layers Detected: {meta.get('amd_layers', 0)} (AMD), {meta.get('nvidia_layers', 0)} (NVIDIA)")
    lines.append("")

    # Separate layers into comparable and trace-unique
    comparable_layers = [layer for layer in layers if layer.get("in_both", True)]
    amd_only_layers = [layer for layer in layers if layer["status"] == "trace1_only" and meta['trace1_platform'] == 'AMD']
    nvidia_only_layers = [layer for layer in layers if layer["status"] == "trace2_only" and meta['trace1_platform'] == 'AMD']

    # Handle case where trace2 is AMD
    if meta['trace1_platform'] != 'AMD':
        amd_only_layers = [layer for layer in layers if layer["status"] == "trace2_only"]
        nvidia_only_layers = [layer for layer in layers if layer["status"] == "trace1_only"]

    slower_layers = [layer for layer in comparable_layers if layer["status"] == "slower"]
    faster_layers = [layer for layer in comparable_layers if layer["status"] == "faster"]
    similar_layers = [layer for layer in comparable_layers if layer["status"] == "similar"]

    lines.append(f"Layers in both traces:       {len(comparable_layers)}")
    lines.append(f"  - AMD is slower:           {len(slower_layers)}")
    lines.append(f"  - AMD is faster:           {len(faster_layers)}")
    lines.append(f"  - Similar performance:     {len(similar_layers)}")
    if amd_only_layers or nvidia_only_layers:
        lines.append(f"Layers only in AMD trace:    {len(amd_only_layers)}")
        lines.append(f"Layers only in NVIDIA trace: {len(nvidia_only_layers)}")
    lines.append("")

    # Show top 20 slowest layers for AMD (or all if show_all)
    if slower_layers:
        slower_to_show = slower_layers if show_all else slower_layers[:20]
        label = f"ALL {len(slower_to_show)}" if show_all else "TOP 20"
        lines.append(f"🔴 {label} LAYERS WHERE AMD IS SLOWER")
        lines.append("=" * 100)
        lines.append(
            f"{'Layer':>6} {'AMD Kernels':>13} {'NV Kernels':>12} "
            f"{'AMD Time':>12} {'NV Time':>11} {'Ratio':>8} {'AMD Slower By':>14}"
        )
        lines.append("-" * 100)

        for layer in slower_to_show:
            lines.append(
                f"{layer['layer']:>6} "
                f"{layer['amd_kernels']:>13,} "
                f"{layer['nvidia_kernels']:>12,} "
                f"{layer['amd_total_ms']:>10.2f}ms "
                f"{layer['nvidia_total_ms']:>9.2f}ms "
                f"{layer['ratio']:>7.2f}x "
                f"{abs(layer['gap_ms']):>13.2f}ms"
            )

        lines.append("")

    # Show top 10 fastest layers for AMD (or all if show_all)
    if faster_layers:
        faster_to_show = faster_layers if show_all else faster_layers[:10]
        label = f"ALL {len(faster_to_show)}" if show_all else "TOP 10"
        lines.append(f"🟢 {label} LAYERS WHERE AMD IS FASTER")
        lines.append("=" * 100)
        lines.append(
            f"{'Layer':>6} {'AMD Kernels':>13} {'NV Kernels':>12} "
            f"{'AMD Time':>12} {'NV Time':>11} {'Ratio':>8} {'AMD Faster By':>14}"
        )
        lines.append("-" * 100)

        for layer in faster_to_show:
            lines.append(
                f"{layer['layer']:>6} "
                f"{layer['amd_kernels']:>13,} "
                f"{layer['nvidia_kernels']:>12,} "
                f"{layer['amd_total_ms']:>10.2f}ms "
                f"{layer['nvidia_total_ms']:>9.2f}ms "
                f"{layer['ratio']:>7.2f}x "
                f"{abs(layer['gap_ms']):>13.2f}ms"
            )

        lines.append("")

    # Show AMD-only layers (simplified display)
    if amd_only_layers:
        amd_to_show = amd_only_layers if show_all else amd_only_layers[:20]
        label = f"ALL {len(amd_to_show)}" if show_all else f"{len(amd_to_show)}/{len(amd_only_layers)}"
        lines.append(f"📊 LAYERS ONLY IN AMD TRACE ({label})")
        lines.append("=" * 60)
        lines.append(f"{'Layer':>6} {'Kernels':>10} {'Time':>12}")
        lines.append("-" * 60)

        for layer in amd_to_show:
            lines.append(
                f"{layer['layer']:>6} "
                f"{layer['amd_kernels']:>10,} "
                f"{layer['amd_total_ms']:>10.2f}ms"
            )

        if not show_all and len(amd_only_layers) > 20:
            lines.append(f"\n... and {len(amd_only_layers) - 20} more AMD-only layers")

        lines.append("")

    # Show NVIDIA-only layers (simplified display)
    if nvidia_only_layers:
        nvidia_to_show = nvidia_only_layers if show_all else nvidia_only_layers[:20]
        label = f"ALL {len(nvidia_to_show)}" if show_all else f"{len(nvidia_to_show)}/{len(nvidia_only_layers)}"
        lines.append(f"📊 LAYERS ONLY IN NVIDIA TRACE ({label})")
        lines.append("=" * 60)
        lines.append(f"{'Layer':>6} {'Kernels':>10} {'Time':>12}")
        lines.append("-" * 60)

        for layer in nvidia_to_show:
            lines.append(
                f"{layer['layer']:>6} "
                f"{layer['nvidia_kernels']:>10,} "
                f"{layer['nvidia_total_ms']:>10.2f}ms"
            )

        if not show_all and len(nvidia_only_layers) > 20:
            lines.append(f"\n... and {len(nvidia_only_layers) - 20} more NVIDIA-only layers")

        lines.append("")

    return lines


def _format_stack_trace_report(results: dict[str, Any], show_all: bool = False) -> list[str]:
    """Format Python stack traces for operations.

    Args:
        results: Analysis results
        show_all: Whether to show all stack traces without truncation

    Returns:
        List of formatted text lines
    """
    lines = []
    ops = results["operations"]
    meta = results["metadata"]
    is_trace1_amd = meta['trace1_platform'] == 'AMD'

    lines.append("=" * 80)
    lines.append("PYTHON STACK TRACES & CPU OPERATOR MAPPING")
    lines.append("=" * 80)
    lines.append("")
    lines.append("Full call stacks showing where GPU operations are invoked from PyTorch/vLLM.")
    lines.append("")

    # Show stack traces for top operations by impact (or all if show_all)
    ops_with_stacks = [
        op for op in ops
        if (op.get("trace1_python_stacks") or op.get("trace2_python_stacks"))
    ]

    if not ops_with_stacks:
        lines.append("No stack trace information available.")
        return lines

    ops_to_show = ops_with_stacks if show_all else ops_with_stacks[:10]
    lines.append(f"Showing {len(ops_to_show)}/{len(ops_with_stacks)} operations")
    lines.append("")

    for op in ops_to_show:
        lines.append(f"Operation: {op['operation']}")

        # Show CPU operator info
        amd_cpu = op.get("trace1_cpu_op" if is_trace1_amd else "trace2_cpu_op", "N/A")
        nv_cpu = op.get("trace2_cpu_op" if is_trace1_amd else "trace1_cpu_op", "N/A")

        if amd_cpu != "N/A" or nv_cpu != "N/A":
            lines.append(f"  Most common CPU operator:")
            if amd_cpu != "N/A":
                lines.append(f"    AMD:    {amd_cpu}")
            if nv_cpu != "N/A":
                lines.append(f"    NVIDIA: {nv_cpu}")

        lines.append("-" * 80)

        # AMD/Trace1 stacks
        trace1_stacks = op.get("trace1_python_stacks", [])
        if trace1_stacks:
            stacks_to_show = trace1_stacks if show_all else trace1_stacks[:3]
            label = "AMD" if is_trace1_amd else "NVIDIA"
            lines.append(f"  {label} Stack Traces ({len(stacks_to_show)}/{len(trace1_stacks)} shown):")
            for i, stack in enumerate(stacks_to_show, 1):
                lines.append(f"    Variant {i}:")
                for frame in stack:
                    lines.append(f"      {frame}")
                if i < len(stacks_to_show):
                    lines.append("")

        # NVIDIA/Trace2 stacks
        trace2_stacks = op.get("trace2_python_stacks", [])
        if trace2_stacks:
            stacks_to_show = trace2_stacks if show_all else trace2_stacks[:3]
            label = "NVIDIA" if is_trace1_amd else "AMD"
            if trace1_stacks:
                lines.append("")
            lines.append(f"  {label} Stack Traces ({len(stacks_to_show)}/{len(trace2_stacks)} shown):")
            for i, stack in enumerate(stacks_to_show, 1):
                lines.append(f"    Variant {i}:")
                for frame in stack:
                    lines.append(f"      {frame}")
                if i < len(stacks_to_show):
                    lines.append("")

        lines.append("")

    return lines


def format_csv(results: dict[str, Any], report_type: str = "operations") -> str:
    """Format comparison results as CSV.

    Args:
        results: Analysis results
        report_type: 'operations' or 'layers'

    Returns:
        CSV formatted string
    """
    lines = []
    meta = results["metadata"]
    is_trace1_amd = meta['trace1_platform'] == 'AMD'

    if report_type == "layers":
        lines.append("layer,amd_kernels,nvidia_kernels,amd_total_ms,nvidia_total_ms,ratio,gap_ms,status,in_both")
        for layer in results.get("layers", []):
            # Convert trace1/trace2 to amd/nvidia
            if is_trace1_amd:
                amd_kernels = layer['trace1_kernels']
                nvidia_kernels = layer['trace2_kernels']
                amd_total_ms = layer['trace1_total_ms']
                nvidia_total_ms = layer['trace2_total_ms']
            else:
                amd_kernels = layer['trace2_kernels']
                nvidia_kernels = layer['trace1_kernels']
                amd_total_ms = layer['trace2_total_ms']
                nvidia_total_ms = layer['trace1_total_ms']

            lines.append(
                f"{layer['layer']},"
                f"{amd_kernels},"
                f"{nvidia_kernels},"
                f"{amd_total_ms:.2f},"
                f"{nvidia_total_ms:.2f},"
                f"{layer['ratio']:.3f},"
                f"{layer['gap_ms']:.2f},"
                f"{layer['status']},"
                f"{layer.get('in_both', True)}"
            )
    else:
        lines.append(
            "operation,amd_count,nvidia_count,amd_avg_us,nvidia_avg_us,amd_total_ms,"
            "nvidia_total_ms,ratio,gap_ms,status,amd_kernel,nvidia_kernel,amd_cpu_op,nvidia_cpu_op"
        )
        for op in results["operations"]:
            # Convert trace1/trace2 to amd/nvidia
            if is_trace1_amd:
                amd_count = op['trace1_count']
                nvidia_count = op['trace2_count']
                amd_avg_us = op['trace1_avg_us']
                nvidia_avg_us = op['trace2_avg_us']
                amd_total_ms = op['trace1_total_ms']
                nvidia_total_ms = op['trace2_total_ms']
                amd_kernel = op.get('trace1_kernel', '')
                nvidia_kernel = op.get('trace2_kernel', '')
                amd_cpu_op = op.get('trace1_cpu_op', '')
                nvidia_cpu_op = op.get('trace2_cpu_op', '')
            else:
                amd_count = op['trace2_count']
                nvidia_count = op['trace1_count']
                amd_avg_us = op['trace2_avg_us']
                nvidia_avg_us = op['trace1_avg_us']
                amd_total_ms = op['trace2_total_ms']
                nvidia_total_ms = op['trace1_total_ms']
                amd_kernel = op.get('trace2_kernel', '')
                nvidia_kernel = op.get('trace1_kernel', '')
                amd_cpu_op = op.get('trace2_cpu_op', '')
                nvidia_cpu_op = op.get('trace1_cpu_op', '')

            lines.append(
                f"{op['operation']},"
                f"{amd_count},"
                f"{nvidia_count},"
                f"{amd_avg_us:.2f},"
                f"{nvidia_avg_us:.2f},"
                f"{amd_total_ms:.2f},"
                f"{nvidia_total_ms:.2f},"
                f"{op['ratio']:.3f},"
                f"{op['gap_ms']:.2f},"
                f"{op['status']},"
                f"{amd_kernel},"
                f"{nvidia_kernel},"
                f"{amd_cpu_op},"
                f"{nvidia_cpu_op}"
            )

    return "\n".join(lines)


def format_json(results: dict[str, Any]) -> str:
    """Format comparison results as JSON.

    Args:
        results: Analysis results

    Returns:
        JSON formatted string
    """
    sanitized = _sanitize_for_json(results)
    return json.dumps(sanitized, indent=2)


def format_fusion_text(results: dict[str, Any]) -> str:
    """Format fusion analysis results as human-readable text.

    Args:
        results: Fusion analysis results

    Returns:
        Formatted text report
    """
    lines = []
    meta = results["metadata"]

    lines.append("=" * 80)
    lines.append("FUSION ANALYSIS REPORT")
    lines.append("=" * 80)
    lines.append("")

    # Use generic trace1/trace2 keys
    lines.append(f"Trace 1 GPU:  {meta['trace1_gpu']}")
    lines.append(f"Trace 2 GPU:  {meta['trace2_gpu']}")
    lines.append(f"Trace 1 Kernels:  {meta['trace1_total_kernels']:,}")
    lines.append(f"Trace 2 Kernels: {meta['trace2_total_kernels']:,}")
    lines.append("")

    lines.append("Correlation Groups Analyzed:")
    lines.append(f"  Trace 1: {meta['trace1_correlation_groups']}")
    lines.append(f"  Trace 2: {meta['trace2_correlation_groups']}")
    lines.append(f"  Matched: {meta['matched_groups']}")
    lines.append("")

    # Convert global_counts from trace1/trace2 to amd/nvidia keys for display
    # Note: fusion analyzer always uses AMD as trace1, NVIDIA as trace2
    global_counts = results["global_counts"]
    for ktype, counts in global_counts.items():
        counts["amd_count"] = counts["trace1_count"]
        counts["nv_count"] = counts["trace2_count"]

    # Convert fusion opportunities from trace1/trace2 to amd/nvidia keys
    for opp in results.get("fusion_opportunities", []):
        opp["amd_total"] = opp["trace1_total"]
        opp["nvidia_total"] = opp["trace2_total"]
        opp["amd_avg_per_group"] = opp["trace1_avg_per_group"]
        opp["nvidia_avg_per_group"] = opp["trace2_avg_per_group"]
        opp["amd_time_ms"] = opp["trace1_time_ms"]
        opp["nvidia_time_ms"] = opp["trace2_time_ms"]

    # Global kernel type distribution
    lines.append("GLOBAL KERNEL TYPE DISTRIBUTION")
    lines.append("=" * 80)
    lines.append(f"{'Kernel Type':<25} {'AMD Count':>12} {'NVIDIA Count':>15} {'Ratio':>12}")
    lines.append("-" * 80)

    sorted_types = sorted(
        global_counts.items(),
        key=lambda x: x[1]["amd_count"] + x[1]["nv_count"],
        reverse=True,
    )

    for ktype, counts in sorted_types:
        amd_c = counts["amd_count"]
        nv_c = counts["nv_count"]
        ratio = counts["ratio"]

        # Mark significant differences
        marker = ""
        if ratio > 2.0:
            marker = " ⚠️  AMD has more"
        elif ratio < 0.5:
            marker = " ⚠️  NVIDIA has more"
        elif nv_c == 0 and amd_c > 20:
            marker = " 🔥 AMD ONLY"
        elif amd_c == 0 and nv_c > 20:
            marker = " 🔥 NVIDIA ONLY"

        ratio_str = f"{ratio:.2f}x" if ratio != float("inf") else "∞"
        lines.append(f"{ktype:<25} {amd_c:>12,} {nv_c:>15,} {ratio_str:>12}{marker}")

    lines.append("")

    # Fusion opportunities
    if results["fusion_opportunities"]:
        lines.append("FUSION OPPORTUNITIES")
        lines.append("=" * 80)
        lines.append("")

        amd_fuses = [opp for opp in results["fusion_opportunities"] if opp["fused_by"] == "AMD"]
        nv_fuses = [opp for opp in results["fusion_opportunities"] if opp["fused_by"] == "NVIDIA"]

        if nv_fuses:
            lines.append("🔴 OPERATIONS AMD RUNS SEPARATELY (NVIDIA fuses them)")
            lines.append("-" * 80)
            lines.append("")

            for i, opp in enumerate(nv_fuses, 1):
                lines.append(f"{i}. {opp['kernel_type']}")
                lines.append("   Kernel Launches:")
                lines.append(f"     AMD:    {opp['amd_total']:,} calls ({opp['amd_avg_per_group']:.1f} per group)")
                lines.append(f"     NVIDIA: {opp['nvidia_total']:,} calls ({opp['nvidia_avg_per_group']:.1f} per group)")
                lines.append(f"     Ratio:  {opp['ratio']:.2f}x (AMD launches more)")
                lines.append("   Execution Time:")
                lines.append(f"     AMD:    {opp['amd_time_ms']:.2f} ms")
                lines.append(f"     NVIDIA: {opp['nvidia_time_ms']:.2f} ms")
                time_marker = ""
                if opp["time_ratio"] > 1.2:
                    time_marker = " (AMD slower ⚠️)"
                elif opp["time_ratio"] < 0.8:
                    time_marker = " (AMD faster ✓)"
                else:
                    time_marker = " (similar)"
                lines.append(f"     Ratio:  {opp['time_ratio']:.2f}x{time_marker}")
                lines.append(f"   Impact: {opp['groups_affected']}/{opp['total_groups']} groups show this difference")

                # Provide interpretation
                if opp["nvidia_total"] == 0:
                    lines.append("   → NVIDIA completely fuses this operation into another kernel")
                else:
                    lines.append(f"   → NVIDIA partially fuses, using {opp['ratio']:.1f}x fewer calls")

                lines.append("")

        if amd_fuses:
            lines.append("🟢 OPERATIONS NVIDIA RUNS SEPARATELY (AMD fuses them)")
            lines.append("-" * 80)
            lines.append("")

            for i, opp in enumerate(amd_fuses, 1):
                lines.append(f"{i}. {opp['kernel_type']}")
                lines.append("   Kernel Launches:")
                lines.append(f"     AMD:    {opp['amd_total']:,} calls ({opp['amd_avg_per_group']:.1f} per group)")
                lines.append(f"     NVIDIA: {opp['nvidia_total']:,} calls ({opp['nvidia_avg_per_group']:.1f} per group)")
                lines.append(f"     Ratio:  {opp['ratio']:.2f}x (NVIDIA launches more)")
                lines.append("   Execution Time:")
                lines.append(f"     AMD:    {opp['amd_time_ms']:.2f} ms")
                lines.append(f"     NVIDIA: {opp['nvidia_time_ms']:.2f} ms")
                time_marker = ""
                if opp["time_ratio"] > 1.2:
                    time_marker = " (AMD slower despite fusion ⚠️)"
                elif opp["time_ratio"] < 0.8:
                    time_marker = " (AMD faster via fusion ✓)"
                else:
                    time_marker = " (similar)"
                lines.append(f"     Ratio:  {opp['time_ratio']:.2f}x{time_marker}")
                lines.append(f"   Impact: {opp['groups_affected']}/{opp['total_groups']} groups show this difference")
                lines.append("")
    else:
        lines.append("No significant fusion differences detected.")
        lines.append("")

    # Fusion mappings
    fusion_mappings = results.get("fusion_mappings", [])
    if fusion_mappings:
        lines.append("")
        lines.append("FUSION MAPPINGS")
        lines.append("=" * 80)
        lines.append("")

        # Group by type
        sequence_mappings = []
        intra_type_mappings = []
        partial_mappings = []

        for mapping in fusion_mappings:
            if len(mapping["unfused_sequence"]) == 2 and \
               mapping["unfused_sequence"][0] == mapping["unfused_sequence"][1] and \
               mapping["unfused_sequence"][0] == mapping["fused_kernel_type"]:
                intra_type_mappings.append(mapping)
            elif len(mapping["unfused_sequence"]) == 1:
                partial_mappings.append(mapping)
            else:
                sequence_mappings.append(mapping)

        # Show sequence fusion
        if sequence_mappings:
            lines.append("🔗 SEQUENCE FUSION")
            lines.append("-" * 80)
            lines.append("")

            # Group by evidence
            from collections import defaultdict
            grouped = defaultdict(list)
            for m in sequence_mappings:
                grouped[m["evidence"]].append(m)

            for evidence, group in list(grouped.items())[:5]:  # Show top 5 patterns
                lines.append(f"Pattern: {evidence}")
                lines.append(f"  Occurrences: {len(group)} correlation groups")
                lines.append(f"  Total calls: {sum(m['pattern_count'] for m in group):,}")
                lines.append(f"  Confidence: {group[0]['pattern_confidence']*100:.0f}%")
                lines.append("")

            if len(grouped) > 5:
                lines.append(f"... and {len(grouped) - 5} more sequence fusion patterns")
                lines.append("")

        # Show intra-type fusion
        if intra_type_mappings:
            lines.append("⛓️  INTRA-TYPE FUSION (Chain Compression)")
            lines.append("-" * 80)
            lines.append("")

            for mapping in intra_type_mappings:
                lines.append(f"Kernel: {mapping['fused_kernel_type']}")
                lines.append(f"  {mapping['evidence']}")
                lines.append(f"  Compression ratio: {mapping['pattern_count'] / max(mapping['fused_count'], 1):.1f}x")
                lines.append("")

        # Show partial fusion
        if partial_mappings:
            lines.append("📊 PARTIAL FUSION")
            lines.append("-" * 80)
            lines.append("")

            for mapping in partial_mappings[:5]:  # Show top 5
                lines.append(f"Kernel: {mapping['unfused_sequence'][0]}")
                lines.append(f"  {mapping['evidence']}")
                lines.append("")

    lines.append("=" * 80)

    return "\n".join(lines)


def format_fusion_csv(results: dict[str, Any]) -> str:
    """Format fusion analysis results as CSV.

    Args:
        results: Fusion analysis results

    Returns:
        CSV formatted string
    """
    lines = []
    lines.append(
        "kernel_type,amd_count,nvidia_count,amd_time_ms,nvidia_time_ms,"
        "time_ratio,launch_ratio,fused_by,groups_affected,total_groups"
    )

    for opp in results["fusion_opportunities"]:
        lines.append(
            f"{opp['kernel_type']},"
            f"{opp['amd_total']},"
            f"{opp['nvidia_total']},"
            f"{opp['amd_time_ms']:.3f},"
            f"{opp['nvidia_time_ms']:.3f},"
            f"{opp['time_ratio']:.3f},"
            f"{opp['ratio']:.3f},"
            f"{opp['fused_by']},"
            f"{opp['groups_affected']},"
            f"{opp['total_groups']}"
        )

    return "\n".join(lines)


def _sanitize_for_json(obj: Any) -> Any:
    """Recursively sanitize data structure to handle Infinity and NaN values.

    Args:
        obj: Data structure to sanitize

    Returns:
        Sanitized data structure with Infinity/NaN converted to None
    """
    import math

    if isinstance(obj, float):
        if math.isinf(obj) or math.isnan(obj):
            return None
        return obj
    elif isinstance(obj, dict):
        return {k: _sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_sanitize_for_json(item) for item in obj]
    else:
        return obj


def format_fusion_json(results: dict[str, Any]) -> str:
    """Format fusion analysis results as JSON.

    Args:
        results: Fusion analysis results

    Returns:
        JSON formatted string
    """
    sanitized = _sanitize_for_json(results)
    return json.dumps(sanitized, indent=2)
