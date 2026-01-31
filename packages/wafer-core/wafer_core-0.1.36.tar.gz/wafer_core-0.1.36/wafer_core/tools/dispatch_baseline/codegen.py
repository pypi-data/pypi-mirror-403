"""Code generator for kernel trace profiling scripts.

Generates minimal Python scripts that:
1. Create tensors with specified shapes/dtypes
2. Run the PyTorch op with warmup
3. Profile using torch.profiler
4. Output structured JSON with kernel info
"""

from wafer_core.tools.dispatch_baseline.dtypes import KernelTraceConfig, OpSpec, TensorSpec


def generate_trace_script(config: KernelTraceConfig) -> str:
    """Generate a profiling script for the given operation.

    Args:
        config: Kernel trace configuration with op spec and settings

    Returns:
        Python script as a string
    """
    op_spec = config.op_spec
    tensor_setup = _generate_tensor_setup(op_spec.inputs)
    op_call = _generate_op_call(op_spec)

    script = f'''"""Auto-generated kernel trace script."""
import json
import sys
import torch

# Ensure CUDA is available
assert torch.cuda.is_available(), "CUDA not available"

# Setup tensors
{tensor_setup}

# Warmup
print("Warming up...", file=sys.stderr)
for _ in range({config.num_warmup}):
    _ = {op_call}
torch.cuda.synchronize()

# Profile with torch.profiler
print("Profiling...", file=sys.stderr)
with torch.profiler.profile(
    activities=[
        torch.profiler.ProfilerActivity.CPU,
        torch.profiler.ProfilerActivity.CUDA,
    ],
    record_shapes=True,
    with_stack=False,
) as prof:
    for _ in range({config.num_runs}):
        _ = {op_call}
    torch.cuda.synchronize()

# Extract kernel information
kernels = []
for event in prof.key_averages():
    if event.device_type == torch.profiler.DeviceType.CUDA:
        # Use device_time (new) or cuda_time (old) for average time in us
        duration = getattr(event, 'device_time', None) or getattr(event, 'cuda_time', 0)
        kernels.append({{
            "name": event.key,
            "duration_us": duration,
            "count": event.count,
        }})

# Sort by duration (longest first)
kernels.sort(key=lambda k: k["duration_us"], reverse=True)

# Get environment info for caching
props = torch.cuda.get_device_properties(0)

# Detect runtime version (CUDA or ROCm)
if hasattr(torch.version, 'hip') and torch.version.hip:
    runtime_version = torch.version.hip
    # ROCm uses gcnArchName for architecture (e.g., "gfx942")
    gpu_arch = getattr(props, 'gcnArchName', f"gfx{{props.major}}{{props.minor}}")
else:
    runtime_version = torch.version.cuda or "unknown"
    gpu_arch = f"sm_{{props.major}}{{props.minor}}"

env_info = {{
    "pytorch_version": torch.__version__,
    "runtime_version": runtime_version,
    "gpu_arch": gpu_arch,
    "gpu_name": props.name,
}}

# Build result
result = {{
    "op": "{op_spec.op}",
    "inputs": {_serialize_inputs(op_spec.inputs)},
    "num_runs": {config.num_runs},
    "kernels": kernels,
    "total_cuda_time_us": sum(k["duration_us"] for k in kernels),
    "environment": env_info,
}}

# Output as JSON (marker for parsing)
print("KERNEL_TRACE_RESULT_JSON:" + json.dumps(result))
'''
    return script


def _generate_tensor_setup(inputs: list[TensorSpec]) -> str:
    """Generate tensor creation code."""
    lines = []
    for tensor in inputs:
        shape_str = ", ".join(str(d) for d in tensor.shape)
        dtype_map = {
            "float16": "torch.float16",
            "float32": "torch.float32",
            "bfloat16": "torch.bfloat16",
            "float64": "torch.float64",
            "int8": "torch.int8",
            "int16": "torch.int16",
            "int32": "torch.int32",
            "int64": "torch.int64",
        }
        dtype = dtype_map.get(tensor.dtype, f"torch.{tensor.dtype}")

        # Use randn for float types, randint for int types
        if "int" in tensor.dtype:
            lines.append(
                f'{tensor.name} = torch.randint(-128, 127, ({shape_str},), '
                f'dtype={dtype}, device="{tensor.device}")'
            )
        else:
            lines.append(
                f'{tensor.name} = torch.randn({shape_str}, dtype={dtype}, device="{tensor.device}")'
            )

    return "\n".join(lines)


def _generate_op_call(op_spec: OpSpec) -> str:
    """Generate the operation call code."""
    args = [t.name for t in op_spec.inputs]
    kwargs = [f"{k}={v}" for k, v in op_spec.kwargs.items()]
    all_args = ", ".join(args + kwargs)
    return f"{op_spec.op}({all_args})"


def _serialize_inputs(inputs: list[TensorSpec]) -> str:
    """Serialize inputs for JSON output."""
    items = []
    for t in inputs:
        items.append(f'{{"name": "{t.name}", "shape": {list(t.shape)}, "dtype": "{t.dtype}"}}')
    return "[" + ", ".join(items) + "]"


def parse_op_string(op_string: str) -> OpSpec:
    """Parse a simple operation string into an OpSpec.

    Supports formats like:
        - "torch.matmul(A, B)"
        - "torch.nn.functional.softmax(x, dim=-1)"

    For shapes, use --shape flags separately.

    Args:
        op_string: Operation string like "torch.matmul(A, B)"

    Returns:
        OpSpec with parsed operation and placeholder inputs
    """
    # Extract op name and arguments
    if "(" not in op_string or ")" not in op_string:
        raise ValueError(f"Invalid op format: {op_string}. Expected: op(args)")

    op_name = op_string[: op_string.index("(")].strip()
    args_str = op_string[op_string.index("(") + 1 : op_string.rindex(")")].strip()

    # Parse arguments (simple comma split, doesn't handle nested calls)
    args = [a.strip() for a in args_str.split(",") if a.strip()]

    # Separate positional args (tensor names) from kwargs
    inputs = []
    kwargs = {}

    for arg in args:
        if "=" in arg:
            key, value = arg.split("=", 1)
            kwargs[key.strip()] = value.strip()
        else:
            # Assume it's a tensor input with default shape
            inputs.append(
                TensorSpec(
                    name=arg,
                    shape=(1024, 1024),  # Default shape, override with --shape
                    dtype="float16",
                )
            )

    return OpSpec(op=op_name, inputs=inputs, kwargs=kwargs)


def update_shapes(op_spec: OpSpec, shapes: dict[str, tuple[int, ...]]) -> OpSpec:
    """Update tensor shapes in an OpSpec.

    Args:
        op_spec: Original OpSpec
        shapes: Dict mapping tensor name to new shape

    Returns:
        New OpSpec with updated shapes
    """
    new_inputs = []
    for tensor in op_spec.inputs:
        if tensor.name in shapes:
            new_inputs.append(
                TensorSpec(
                    name=tensor.name,
                    shape=shapes[tensor.name],
                    dtype=tensor.dtype,
                    device=tensor.device,
                )
            )
        else:
            new_inputs.append(tensor)

    return OpSpec(op=op_spec.op, inputs=new_inputs, kwargs=op_spec.kwargs)


def update_dtypes(op_spec: OpSpec, dtype: str) -> OpSpec:
    """Update all tensor dtypes in an OpSpec.

    Args:
        op_spec: Original OpSpec
        dtype: New dtype for all tensors

    Returns:
        New OpSpec with updated dtypes
    """
    new_inputs = [
        TensorSpec(
            name=t.name,
            shape=t.shape,
            dtype=dtype,
            device=t.device,
        )
        for t in op_spec.inputs
    ]
    return OpSpec(op=op_spec.op, inputs=new_inputs, kwargs=op_spec.kwargs)
