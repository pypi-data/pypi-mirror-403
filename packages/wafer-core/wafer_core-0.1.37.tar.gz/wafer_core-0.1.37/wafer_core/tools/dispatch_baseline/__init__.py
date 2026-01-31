"""Kernel trace tool for discovering SOTA kernels.

Given a PyTorch operation, traces what kernel PyTorch dispatches to on target hardware.

Usage:
    from wafer_core.tools.dispatch_baseline import quick_trace

    result = quick_trace(
        "torch.matmul(A, B)",
        {"A": (4096, 4096), "B": (4096, 4096)},
        hardware="H100",
    )
    print(result.summary())
"""

from wafer_core.tools.dispatch_baseline.client import (
    lookup_baseline,
    store_baseline,
)
from wafer_core.tools.dispatch_baseline.codegen import (
    generate_trace_script,
    parse_op_string,
    update_dtypes,
    update_shapes,
)
from wafer_core.tools.dispatch_baseline.dtypes import (
    HardwareSpec,
    KernelInfo,
    KernelTraceConfig,
    KernelTraceResult,
    OpSpec,
    RooflineAnalysis,
    TensorSpec,
)
from wafer_core.tools.dispatch_baseline.executor import (
    TraceExecutionResult,
    quick_trace,
    trace_kernel_local,
    trace_kernel_remote,
)
from wafer_core.tools.dispatch_baseline.roofline import (
    HARDWARE_SPECS,
    compute_roofline,
    get_hardware_spec,
)

__all__ = [
    # Data types
    "HardwareSpec",
    "KernelInfo",
    "KernelTraceConfig",
    "KernelTraceResult",
    "OpSpec",
    "RooflineAnalysis",
    "TensorSpec",
    "TraceExecutionResult",
    # Codegen
    "generate_trace_script",
    "parse_op_string",
    "update_dtypes",
    "update_shapes",
    # Execution
    "quick_trace",
    "trace_kernel_local",
    "trace_kernel_remote",
    # Database
    "lookup_baseline",
    "store_baseline",
    # Roofline
    "HARDWARE_SPECS",
    "compute_roofline",
    "get_hardware_spec",
]
