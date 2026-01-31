"""Profiling tool interfaces.

Stateful classes for NSYS, ROCprofiler, and Perfetto profiling tools.
"""

# Lazy imports to avoid loading heavy dependencies
def __getattr__(name: str):
    """Lazy import profiling tool components."""
    if name in ("PerfettoTool", "PerfettoConfig"):
        from wafer_core.lib.perfetto import PerfettoConfig, PerfettoTool
        if name == "PerfettoTool":
            return PerfettoTool
        return PerfettoConfig
    
    if name in ("TraceManager", "TraceMeta"):
        from wafer_core.lib.perfetto import TraceManager, TraceMeta
        if name == "TraceManager":
            return TraceManager
        return TraceMeta
    
    if name in ("TraceProcessorManager", "TraceProcessorStatus"):
        from wafer_core.lib.perfetto import (
            TraceProcessorManager,
            TraceProcessorStatus,
        )
        if name == "TraceProcessorManager":
            return TraceProcessorManager
        return TraceProcessorStatus
    
    # Support submodule imports (rocprofiler, nsys, perfetto)
    # These are packages, not individual classes
    if name in ("rocprofiler", "nsys", "perfetto"):
        import importlib
        return importlib.import_module(f"wafer_core.lib.{name}")
    
    raise AttributeError(f"module 'wafer_core.lib' has no attribute {name!r}")
