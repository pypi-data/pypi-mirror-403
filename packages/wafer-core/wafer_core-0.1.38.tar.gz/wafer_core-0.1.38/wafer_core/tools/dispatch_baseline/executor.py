"""Executor for kernel trace operations.

Runs profiling scripts on remote GPUs and returns structured results.
"""

import logging
import tempfile
from dataclasses import dataclass, replace
from pathlib import Path

from wafer_core.ssh import ExecResult, SSHClient
from wafer_core.tools.dispatch_baseline.analyzer import ParsedTraceResult, parse_trace_output
from wafer_core.tools.dispatch_baseline.codegen import generate_trace_script
from wafer_core.tools.dispatch_baseline.dtypes import (
    KernelTraceConfig,
    KernelTraceResult,
    OpSpec,
    TensorSpec,
)
from wafer_core.tools.dispatch_baseline.roofline import (
    compute_roofline,
    estimate_attention_bytes,
    estimate_attention_flops,
    estimate_matmul_bytes,
    estimate_matmul_flops,
    estimate_softmax_bytes,
    estimate_softmax_flops,
    get_hardware_spec,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TraceExecutionResult:
    """Result of trace execution with environment info for caching."""

    result: KernelTraceResult
    pytorch_version: str
    runtime_version: str
    gpu_arch: str
    from_cache: bool = False


def trace_kernel_local(config: KernelTraceConfig) -> TraceExecutionResult:
    """Trace a kernel on the local GPU.

    Args:
        config: Kernel trace configuration

    Returns:
        TraceExecutionResult with kernel information and environment info
    """
    import subprocess
    import sys

    script = generate_trace_script(config)

    # Write script to temp file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(script)
        script_path = f.name

    try:
        # Run script
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            timeout=config.timeout_seconds,
        )

        output = result.stdout + result.stderr

        if result.returncode != 0:
            return TraceExecutionResult(
                result=KernelTraceResult(
                    op_spec=config.op_spec,
                    hardware=config.hardware,
                    kernels=[],
                    primary_kernel=None,
                    raw_output=output,
                    error=f"Script failed with exit code {result.returncode}: {result.stderr}",
                ),
                pytorch_version="unknown",
                runtime_version="unknown",
                gpu_arch="unknown",
            )

        # Parse output (now includes environment info)
        parsed = parse_trace_output(output, config.op_spec, config.hardware)

        # Add roofline analysis if we can estimate FLOPS
        trace_result = _add_roofline_analysis(parsed.result, config)

        return TraceExecutionResult(
            result=trace_result,
            pytorch_version=parsed.pytorch_version,
            runtime_version=parsed.runtime_version,
            gpu_arch=parsed.gpu_arch,
        )

    except subprocess.TimeoutExpired:
        return TraceExecutionResult(
            result=KernelTraceResult(
                op_spec=config.op_spec,
                hardware=config.hardware,
                kernels=[],
                primary_kernel=None,
                error=f"Script timed out after {config.timeout_seconds}s",
            ),
            pytorch_version="unknown",
            runtime_version="unknown",
            gpu_arch="unknown",
        )

    finally:
        # Cleanup
        Path(script_path).unlink(missing_ok=True)


def trace_kernel_remote(
    config: KernelTraceConfig,
    ssh_client: SSHClient,
    workspace_path: str = "/tmp",
) -> TraceExecutionResult:
    """Trace a kernel on a remote GPU via SSH.

    Args:
        config: Kernel trace configuration
        ssh_client: Connected SSH client
        workspace_path: Remote directory to use for temporary files

    Returns:
        TraceExecutionResult with kernel information and environment info
    """
    script = generate_trace_script(config)
    script_filename = "dispatch_baseline_script.py"
    remote_script_path = f"{workspace_path}/{script_filename}"

    try:
        # Upload script
        logger.debug(f"Uploading trace script to {remote_script_path}")
        ssh_client.upload_content(script, remote_script_path)

        # Run script
        # TODO: Add timeout to SSHClient.exec() to prevent hanging on remote failures
        logger.debug("Running trace script...")
        run_cmd = f"cd {workspace_path} && python {script_filename}"
        result: ExecResult = ssh_client.exec(run_cmd)

        output = result.stdout + result.stderr

        if result.exit_code != 0:
            return TraceExecutionResult(
                result=KernelTraceResult(
                    op_spec=config.op_spec,
                    hardware=config.hardware,
                    kernels=[],
                    primary_kernel=None,
                    raw_output=output,
                    error=f"Script failed with exit code {result.exit_code}: {result.stderr}",
                ),
                pytorch_version="unknown",
                runtime_version="unknown",
                gpu_arch="unknown",
            )

        # Parse output (now includes environment info)
        parsed = parse_trace_output(output, config.op_spec, config.hardware)

        # Add roofline analysis
        trace_result = _add_roofline_analysis(parsed.result, config)

        return TraceExecutionResult(
            result=trace_result,
            pytorch_version=parsed.pytorch_version,
            runtime_version=parsed.runtime_version,
            gpu_arch=parsed.gpu_arch,
        )

    except Exception as e:
        logger.exception("Failed to trace kernel remotely")
        return TraceExecutionResult(
            result=KernelTraceResult(
                op_spec=config.op_spec,
                hardware=config.hardware,
                kernels=[],
                primary_kernel=None,
                error=f"Remote execution failed: {e}",
            ),
            pytorch_version="unknown",
            runtime_version="unknown",
            gpu_arch="unknown",
        )

    finally:
        # Cleanup remote script
        try:
            ssh_client.exec(f"rm -f {remote_script_path}")
        except Exception:
            pass


def _add_roofline_analysis(
    result: KernelTraceResult, config: KernelTraceConfig
) -> KernelTraceResult:
    """Add roofline analysis to trace result if possible.
    
    Supports: matmul, softmax, attention, and generic elementwise ops.
    """
    if result.primary_kernel is None:
        return result
    
    if config.hardware is None:
        return result

    # Try to estimate FLOPS based on operation type
    op_lower = config.op_spec.op.lower()
    shapes = [t.shape for t in config.op_spec.inputs]
    dtype_bytes = _get_dtype_bytes(config.op_spec.inputs[0].dtype) if config.op_spec.inputs else 2
    
    flops = 0.0
    bytes_transferred = 0.0

    if "matmul" in op_lower or "mm" in op_lower or "linear" in op_lower:
        # Matrix multiplication: C[M,N] = A[M,K] @ B[K,N]
        if len(shapes) >= 2 and len(shapes[0]) >= 2 and len(shapes[1]) >= 2:
            # Handle batched matmul by taking last 2 dims
            m, k1 = shapes[0][-2], shapes[0][-1]
            k2, n = shapes[1][-2], shapes[1][-1]
            # Validate batch dimensions match (if present)
            batch_dims_0 = shapes[0][:-2]
            batch_dims_1 = shapes[1][:-2]
            if k1 != k2:
                logger.warning(f"Matmul inner dims mismatch: {k1} vs {k2}, skipping roofline")
            elif batch_dims_0 != batch_dims_1:
                logger.warning(f"Matmul batch dims mismatch: {batch_dims_0} vs {batch_dims_1}, skipping roofline")
            else:
                # Account for batch dimensions
                batch_size = 1
                for dim in batch_dims_0:
                    batch_size *= dim
                flops = batch_size * estimate_matmul_flops(m, n, k1)
                bytes_transferred = batch_size * estimate_matmul_bytes(m, n, k1, dtype_bytes)
                
    elif "softmax" in op_lower:
        # Softmax: read input, write output
        if shapes:
            elements = 1
            for dim in shapes[0]:
                elements *= dim
            flops = estimate_softmax_flops(elements)
            bytes_transferred = estimate_softmax_bytes(elements, dtype_bytes)
            
    elif "attention" in op_lower or "sdpa" in op_lower:
        # Scaled dot-product attention
        # Expect inputs like Q[B,H,S,D], K[B,H,S,D], V[B,H,S,D]
        if len(shapes) >= 3 and len(shapes[0]) == 4:
            batch, heads, seq_len, head_dim = shapes[0]
            flops = estimate_attention_flops(batch, heads, seq_len, head_dim)
            bytes_transferred = estimate_attention_bytes(batch, heads, seq_len, head_dim, dtype_bytes)
            
    elif any(op in op_lower for op in ["relu", "gelu", "silu", "tanh", "sigmoid", "exp", "log"]):
        # Elementwise activation: ~1-5 ops per element, read+write
        if shapes:
            elements = 1
            for dim in shapes[0]:
                elements *= dim
            flops = 5.0 * elements  # Conservative estimate for transcendentals
            bytes_transferred = 2.0 * elements * dtype_bytes  # Read + write
            
    elif any(op in op_lower for op in ["add", "sub", "mul", "div"]):
        # Binary elementwise: 1 op per element
        if shapes:
            elements = 1
            for dim in shapes[0]:
                elements *= dim
            flops = float(elements)
            bytes_transferred = 3.0 * elements * dtype_bytes  # Read 2 inputs + write 1 output
            
    elif "layernorm" in op_lower or "layer_norm" in op_lower or "rmsnorm" in op_lower:
        # Normalization: mean, variance, normalize (~10 ops per element)
        if shapes:
            elements = 1
            for dim in shapes[0]:
                elements *= dim
            flops = 10.0 * elements
            bytes_transferred = 2.0 * elements * dtype_bytes
            
    elif "conv" in op_lower:
        # Convolution is complex, skip for now (would need kernel size, stride, etc.)
        pass

    if flops > 0 and bytes_transferred > 0:
        roofline = compute_roofline(
            result.primary_kernel,
            config.hardware,
            flops,
            bytes_transferred,
        )
        if roofline:
            return replace(result, roofline=roofline)

    return result


def _get_dtype_bytes(dtype: str) -> int:
    """Get bytes per element for a dtype."""
    dtype_map = {
        "float16": 2,
        "float32": 4,
        "float64": 8,
        "bfloat16": 2,
        "int8": 1,
        "int16": 2,
        "int32": 4,
        "int64": 8,
    }
    return dtype_map.get(dtype, 2)


def quick_trace(
    op: str,
    shapes: dict[str, tuple[int, ...]],
    hardware: str = "H100",
    dtype: str = "float16",
) -> KernelTraceResult:
    """Quick helper to trace an operation locally.

    Args:
        op: Operation string like "torch.matmul(A, B)"
        shapes: Dict mapping tensor names to shapes
        hardware: Hardware name (for roofline analysis)
        dtype: Data type for tensors

    Returns:
        KernelTraceResult

    Example:
        result = quick_trace(
            "torch.matmul(A, B)",
            {"A": (4096, 4096), "B": (4096, 4096)},
            hardware="H100",
        )
        print(result.summary())
    """
    from wafer_core.tools.dispatch_baseline.codegen import parse_op_string, update_dtypes, update_shapes

    op_spec = parse_op_string(op)
    op_spec = update_shapes(op_spec, shapes)
    op_spec = update_dtypes(op_spec, dtype)

    config = KernelTraceConfig(
        op_spec=op_spec,
        hardware=hardware,
    )

    execution_result = trace_kernel_local(config)
    return execution_result.result
