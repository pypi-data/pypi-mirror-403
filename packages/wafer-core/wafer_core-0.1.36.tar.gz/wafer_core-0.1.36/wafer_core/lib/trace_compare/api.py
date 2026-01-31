"""Unified API for trace comparison analysis.

Provides a single entry point that combines all analysis types:
- Operation-level comparison
- Layer-wise comparison
- Kernel-to-kernel alignment
- Fusion analysis
- Same kernel analysis
- Warnings
"""

import sys
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Literal

MetadataCallback = Callable[["StreamingMetadata", "StreamingMetadata"], None]

from .analyzer import analyze_traces_from_loaded, analyze_traces_aligned
from .fusion_analyzer import analyze_fusion_from_alignment
from .same_kernel_analyzer import analyze_same_kernels_from_alignment
from .architecture import ArchitectureType, detect_architecture
from .loader import load_trace_full, ProgressCallback, StreamingMetadata, _extract_metadata_fast
from .warnings import TraceWarning, detect_warnings


@dataclass(frozen=True)
class TraceComparisonResult:
    """Complete trace comparison result with all analysis types."""

    metadata: dict[str, Any]
    operations: list[dict[str, Any]]
    layers: list[dict[str, Any]]
    fusion_opportunities: list[dict[str, Any]]
    fusion_mappings: list[dict[str, Any]]
    warnings: list[TraceWarning]
    architecture: ArchitectureType
    # New alignment-based fields
    layer_alignments: list[dict[str, Any]] | None = None
    fusion_analysis: dict[str, Any] | None = None
    same_kernel_analysis: dict[str, Any] | None = None


def analyze_trace_pair(
    trace1_path: str | Path,
    trace2_path: str | Path,
    phase: Literal["all", "prefill", "decode"] = "all",
    include_stacks: bool = True,
    on_progress: ProgressCallback | None = None,
    on_metadata: MetadataCallback | None = None,
) -> TraceComparisonResult:
    """Single entry point combining all analyses.
    
    Args:
        trace1_path: Path to first trace file
        trace2_path: Path to second trace file
        phase: Filter by phase ('all', 'prefill', or 'decode')
        include_stacks: Whether to include Python stack traces
        on_progress: Optional callback for progress updates: (stage_name, progress_fraction)
        on_metadata: Optional callback for early metadata (~2ms): (trace1_meta, trace2_meta)
        
    Returns:
        Complete comparison result with all analysis types
    """
    trace1_path = Path(trace1_path)
    trace2_path = Path(trace2_path)
    
    def _progress(stage: str, fraction: float) -> None:
        if on_progress:
            on_progress(stage, fraction)
    
    if on_metadata:
        meta1 = _extract_metadata_fast(trace1_path)
        meta2 = _extract_metadata_fast(trace2_path)
        on_metadata(meta1, meta2)
    
    t0 = time.perf_counter()
    _progress("Loading traces", 0.0)
    
    with ProcessPoolExecutor(max_workers=2) as executor:
        future1 = executor.submit(load_trace_full, trace1_path, include_stacks, None)
        future2 = executor.submit(load_trace_full, trace2_path, include_stacks, None)
        
        if on_progress:
            import threading
            stop_progress = threading.Event()
            
            def progress_updater():
                base_progress = 0.0
                max_progress = 0.75
                start_time = time.perf_counter()
                estimated_duration = 30.0
                
                stages = [
                    ("Reading files", 0.05),
                    ("Parsing JSON", 0.15),
                    ("Processing events", 0.40),
                    ("Building DataFrames", 0.60),
                    ("Finalizing", 0.75),
                ]
                
                stage_idx = 0
                last_progress = 0.0
                while not stop_progress.is_set():
                    elapsed = time.perf_counter() - start_time
                    if elapsed > estimated_duration:
                        elapsed = estimated_duration
                    
                    if stage_idx < len(stages):
                        stage_name, stage_max = stages[stage_idx]
                        stage_progress = min(elapsed / estimated_duration, 1.0) * (stage_max - base_progress)
                        current_progress = base_progress + stage_progress
                        
                        if current_progress - last_progress >= 0.01:
                            _progress(f"Loading: {stage_name}", current_progress)
                            last_progress = current_progress
                        
                        if current_progress >= stage_max and stage_idx < len(stages) - 1:
                            base_progress = stage_max
                            stage_idx += 1
                    else:
                        if max_progress - last_progress >= 0.01:
                            _progress("Loading traces", max_progress)
                            last_progress = max_progress
                    
                    if stop_progress.wait(timeout=0.2):
                        break
            
            progress_thread = threading.Thread(target=progress_updater, daemon=True)
            progress_thread.start()
        
        trace1 = future1.result()
        trace2 = future2.result()
        
        if on_progress:
            stop_progress.set()
            progress_thread.join(timeout=1.0)
    
    # Normalize trace order: trace1 should always be AMD, trace2 should be NVIDIA
    # This ensures consistent output where trace1_* fields always refer to AMD
    if trace1.platform != "AMD" and trace2.platform == "AMD":
        trace1, trace2 = trace2, trace1
    
    t1 = time.perf_counter()
    print(f"Trace loading: {t1-t0:.1f}s", file=sys.stderr)
    _progress("Traces loaded", 0.8)
    
    t2_start = time.perf_counter()
    _progress("Detecting architecture", 0.8)
    all_kernel_names = list(trace1.df["name"].unique()) + list(trace2.df["name"].unique())
    architecture, _ = detect_architecture(all_kernel_names)
    
    _progress("Comparing operations", 0.85)
    comparison_result = analyze_traces_from_loaded(trace1, trace2, phase_filter=phase)
    t2_end = time.perf_counter()
    print(f"Operation analysis: {t2_end-t2_start:.1f}s", file=sys.stderr)
    
    _progress("Aligning kernels", 0.9)
    t3_start = time.perf_counter()
    alignment_result = analyze_traces_aligned(trace1, trace2, phase_filter=phase)
    t3_end = time.perf_counter()
    print(f"Alignment analysis: {t3_end-t3_start:.1f}s", file=sys.stderr)
    
    t4_start = time.perf_counter()
    kernel_names1 = [ev.get("name", "") for ev in trace1.all_events if ev.get("cat") == "kernel"]
    kernel_names2 = [ev.get("name", "") for ev in trace2.all_events if ev.get("cat") == "kernel"]
    
    phases1 = [
        ev for ev in trace1.all_events
        if ev.get("cat") == "user_annotation" and ev.get("name", "").startswith("execute_context")
    ]
    phases2 = [
        ev for ev in trace2.all_events
        if ev.get("cat") == "user_annotation" and ev.get("name", "").startswith("execute_context")
    ]
    
    warnings1 = detect_warnings(
        trace1.all_events,
        kernel_names1,
        phases1,
        comparison_result["metadata"].get("trace1_layers", 0),
        len(kernel_names1),
    )
    warnings2 = detect_warnings(
        trace2.all_events,
        kernel_names2,
        phases2,
        comparison_result["metadata"].get("trace2_layers", 0),
        len(kernel_names2),
    )
    t4_end = time.perf_counter()
    print(f"Warning detection: {t4_end-t4_start:.1f}s", file=sys.stderr)
    
    all_warnings: list[TraceWarning] = []
    seen_codes: set[str] = set()
    for warning in warnings1 + warnings2:
        if warning.code not in seen_codes:
            all_warnings.append(warning)
            seen_codes.add(warning.code)
    
    print(f"Total analysis time: {t4_end-t0:.1f}s", file=sys.stderr)
    
    _progress("Complete", 1.0)
    
    fusion_opportunities = []
    fusion_mappings = []
    if alignment_result.get("fusion_analysis"):
        fusion_analysis = alignment_result["fusion_analysis"]
        fusion_opportunities = fusion_analysis.get("fusion_opportunities", [])
        fusion_mappings = fusion_analysis.get("fusion_mappings", [])
    
    return TraceComparisonResult(
        metadata=comparison_result["metadata"],
        operations=comparison_result["operations"],
        layers=comparison_result.get("layers", []),
        fusion_opportunities=fusion_opportunities,
        fusion_mappings=fusion_mappings,
        warnings=all_warnings,
        architecture=architecture,
        layer_alignments=alignment_result.get("layer_alignments"),
        fusion_analysis=alignment_result.get("fusion_analysis"),
        same_kernel_analysis=alignment_result.get("same_kernel_analysis"),
    )
