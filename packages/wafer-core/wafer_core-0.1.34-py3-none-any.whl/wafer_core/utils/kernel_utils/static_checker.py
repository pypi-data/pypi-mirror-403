"""
Static kernel checker - Pattern-based validation for GPU kernel code.

Validates that kernel implementations use the correct backend primitives
and don't contain reward hacking patterns (try-except fallback, PyTorch ops, etc.).

Based on KernelBench's kernel_static_checker.py.
"""

import re
from collections.abc import Callable


def _strip_comments(code: str) -> str:
    """Remove # and // comments from code."""
    lines = []
    for line in code.split("\n"):
        if "#" in line:
            line = line[: line.index("#")]
        if "//" in line:
            line = line[: line.index("//")]
        lines.append(line)
    return "\n".join(lines)


# =============================================================================
# BYPASS CHECKS - Strictly Prohibited
# =============================================================================

TRY_EXCEPT_PATTERNS = [r"\btry\s*:", r"\bexcept\s*:", r"\bexcept\s+\w+"]
PASS_PATTERN = r"\bpass\b"


def check_code_bypass(code: str) -> tuple[bool, str]:
    """Check for code bypass patterns (try-except fallback, pass statement)."""
    code = _strip_comments(code)

    for pattern in TRY_EXCEPT_PATTERNS:
        if re.search(pattern, code):
            return (True, "Contains try-except block (potential fallback bypass)")

    if re.search(PASS_PATTERN, code):
        return (True, "Contains 'pass' statement (inheritance bypass)")

    return (False, "")


# =============================================================================
# PYTORCH USAGE CHECKS
# =============================================================================

# Allows: nn.Module, nn.Parameter, nn.ParameterList, nn.ParameterDict,
#         nn.ModuleList, nn.ModuleDict, nn.init (needed for model structure)
# Blocks: nn.Linear, nn.Conv2d, nn.ReLU, etc. (compute layers)
PYTORCH_DISALLOWED_NN_PATTERN = r"torch\.nn\.(?!(Module|parameter|Parameter|ParameterList|ParameterDict|ModuleList|ModuleDict|init)\b)"


def check_pytorch_wrap(code: str) -> tuple[bool, str]:
    """Check for PyTorch nn module usage (nn.Linear, nn.Conv2d, etc.)."""
    code = _strip_comments(code)
    if re.search(PYTORCH_DISALLOWED_NN_PATTERN, code):
        return (True, "Uses torch.nn compute layer (only containers, Parameter, init allowed)")
    return (False, "")


TORCH_COMPUTATION_OPS = [
    # Matrix operations
    "torch.mm",
    "torch.bmm",
    "torch.matmul",
    "torch.einsum",
    # Convolutions
    "torch.conv1d",
    "torch.conv2d",
    "torch.conv3d",
    "torch.conv",
    "torch.conv_transpose1d",
    "torch.conv_transpose2d",
    "torch.conv_transpose3d",
    # Pooling
    "torch.avg_pool1d",
    "torch.avg_pool2d",
    "torch.avg_pool3d",
    "torch.max_pool1d",
    "torch.max_pool2d",
    "torch.max_pool3d",
    "torch.adaptive_avg_pool1d",
    "torch.adaptive_avg_pool2d",
    "torch.adaptive_avg_pool3d",
    "torch.adaptive_max_pool1d",
    "torch.adaptive_max_pool2d",
    "torch.adaptive_max_pool3d",
    # Activations
    "torch.relu",
    "torch.hardtanh",
    "torch.elu",
    "torch.selu",
    "torch.leaky_relu",
    "torch.gelu",
    "torch.softsign",
    "torch.softplus",
    "torch.softmax",
    "torch.log_softmax",
    "torch.tanh",
    "torch.sigmoid",
    "torch.hardsigmoid",
    "torch.silu",
    "torch.mish",
    # Normalization
    "torch.batch_norm",
    "torch.group_norm",
    "torch.layer_norm",
    "torch.instance_norm",
    "torch.rms_norm",
    "torch.normalize",
    # Linear & Loss
    "torch.linear",
    "torch.cross_entropy",
    "torch.kl_div",
    "torch.mse_loss",
    "torch.huber_loss",
    "torch.triplet_margin_loss",
    "torch.cosine_similarity",
    # Others
    "torch.logsumexp",
    "torch.clamp",
    "torch.dropout",
]

TORCH_FUNCTIONAL_PATTERNS = [
    r"torch\.nn\.functional\.\w+",  # torch.nn.functional.*
    r"\bnn\.functional\.\w+",  # nn.functional.*
    r"\bF\.(conv|linear|relu|gelu|softmax|batch_norm|layer_norm|dropout|max_pool|avg_pool|scaled_dot_product_attention)",
]


def check_torch_computation_ops(code: str) -> tuple[bool, str]:
    """Check for high-level torch computation operations."""
    code = _strip_comments(code)

    # Check torch.* ops
    torch_pattern = (
        r"\b(" + "|".join(re.escape(f) for f in TORCH_COMPUTATION_OPS) + r")(?=\s*\(|\s|$)"
    )
    match = re.search(torch_pattern, code)
    if match:
        return (True, f"Uses torch computation op: {match.group(0)}")

    # Check F.* / nn.functional ops
    for pattern in TORCH_FUNCTIONAL_PATTERNS:
        match = re.search(pattern, code)
        if match:
            return (True, f"Uses torch.nn.functional op: {match.group(0)}")

    return (False, "")


# =============================================================================
# NN.MODULE FORWARD CALL CHECKS (Reward Hacking in forward())
# =============================================================================

# These patterns detect calling PyTorch nn.Module forward methods inside forward()
# e.g., self.conv(x), self.linear(x), self.bn(x) - these invoke cuBLAS/cuDNN
# 
# This is different from:
# - nn.Linear(...) in __init__ = OK (just creates parameter container)
# - self.linear.weight in forward() = OK (accessing weights for custom kernel)
# - self.linear(x) in forward() = BAD (invokes PyTorch's matmul via cuBLAS)

NN_MODULE_FORWARD_PATTERNS = [
    # Common layer types being called as functions
    r"self\.(conv\d*d?|linear|bn|batch_norm|layer_norm|group_norm|instance_norm)\s*\(",
    # More generic pattern: self.<name>(x) or self.<name>(input)
    # But we need to be careful not to match custom module calls
]

# =============================================================================
# TORCH.NN.FUNCTIONAL CHECKS (Reward Hacking)
# =============================================================================

# Patterns for torch.nn.functional / F.* calls that bypass custom kernel requirement
# These call into cuBLAS/cuDNN under the hood
TORCH_FUNCTIONAL_PATTERNS = [
    # F.linear, F.conv*, F.batch_norm etc. (common alias)
    r"\bF\.(linear|conv[123]d|conv_transpose[123]d|batch_norm|layer_norm|group_norm|instance_norm)\s*\(",
    # Full path torch.nn.functional.*
    r"\btorch\.nn\.functional\.(linear|conv[123]d|conv_transpose[123]d|batch_norm|layer_norm|group_norm|instance_norm)\s*\(",
]


def check_torch_functional_calls(code: str) -> tuple[bool, str]:
    """Check for torch.nn.functional / F.* calls in forward() method (reward hacking).
    
    Detects patterns like F.linear(x, weight), F.conv2d(x, weight) which invoke
    PyTorch's built-in operations (backed by cuBLAS/cuDNN) instead of custom kernels.
    
    Note: We only check inside forward() to avoid false positives from imports or
    training-mode fallbacks that aren't used during inference.
    """
    # Only check inside forward() method
    forward_code = _extract_forward_method(code)
    if not forward_code:
        return (False, "")
    
    forward_code = _strip_comments(forward_code)
    
    for pattern in TORCH_FUNCTIONAL_PATTERNS:
        match = re.search(pattern, forward_code)
        if match:
            return (True, f"Uses torch.nn.functional in forward(): {match.group(0)} (reward hacking - must use custom kernel)")
    
    return (False, "")


def _extract_forward_method(code: str) -> str:
    """Extract only the forward() method content from code."""
    lines = code.split('\n')
    result = []
    in_forward = False
    base_indent = 0
    
    for i, line in enumerate(lines):
        # Look for forward method definition
        if re.search(r'\bdef\s+forward\s*\(\s*self', line):
            in_forward = True
            # Get the indentation level of the def line
            base_indent = len(line) - len(line.lstrip())
            result.append(line)
            continue
        
        if in_forward:
            # Check if we've exited the forward method (new method/class at same or lower indent)
            stripped = line.strip()
            if stripped and not stripped.startswith('#') and not stripped.startswith('"""') and not stripped.startswith("'''"):
                current_indent = len(line) - len(line.lstrip())
                # If we hit a new def/class at the same or lower indentation, we're done
                if current_indent <= base_indent and (stripped.startswith('def ') or stripped.startswith('class ')):
                    break
            result.append(line)
    
    return '\n'.join(result)


def check_nn_module_forward_call(code: str) -> tuple[bool, str]:
    """Check for nn.Module forward calls inside forward() method (reward hacking).
    
    Detects patterns like self.conv(x), self.linear(x) which invoke PyTorch's
    built-in layers (backed by cuBLAS/cuDNN) instead of custom kernels.
    """
    # Only check inside forward() method
    forward_code = _extract_forward_method(code)
    if not forward_code:
        return (False, "")
    
    forward_code = _strip_comments(forward_code)
    
    for pattern in NN_MODULE_FORWARD_PATTERNS:
        match = re.search(pattern, forward_code)
        if match:
            return (True, f"Calls PyTorch nn.Module in forward(): {match.group(0)} (reward hacking - must use custom kernel)")
    
    return (False, "")


# =============================================================================
# CUBLAS/CUDNN DIRECT USAGE CHECKS (Reward Hacking)
# =============================================================================

# Direct cuBLAS calls bypass custom kernel requirement
CUBLAS_PATTERNS = [
    r"\bcublas[A-Z]\w+\s*\(",  # cublasSgemm, cublasGemmEx, etc.
    r"\bcublasCreate\b",
    r"\bcublasDestroy\b",
    r"\bcublasSetStream\b",
    r"\bcublasSetMathMode\b",
    r"#include\s*[<\"]cublas",  # #include <cublas_v2.h>
    r"CUBLAS_TENSOR_OP_MATH",
]

# Direct cuDNN calls bypass custom kernel requirement
CUDNN_PATTERNS = [
    r"\bcudnn[A-Z]\w+\s*\(",  # cudnnConvolutionForward, etc.
    r"\bcudnnCreate\b",
    r"\bcudnnDestroy\b",
    r"#include\s*[<\"]cudnn",  # #include <cudnn.h>
]


def check_cublas_usage(code: str) -> tuple[bool, str]:
    """Check for direct cuBLAS API usage (reward hacking)."""
    code = _strip_comments(code)
    
    for pattern in CUBLAS_PATTERNS:
        match = re.search(pattern, code)
        if match:
            return (True, f"Uses cuBLAS directly: {match.group(0)} (reward hacking - must write custom kernel)")
    
    return (False, "")


def check_cudnn_usage(code: str) -> tuple[bool, str]:
    """Check for direct cuDNN API usage (reward hacking)."""
    code = _strip_comments(code)
    
    for pattern in CUDNN_PATTERNS:
        match = re.search(pattern, code)
        if match:
            return (True, f"Uses cuDNN directly: {match.group(0)} (reward hacking - must write custom kernel)")
    
    return (False, "")


# =============================================================================
# TIMING MANIPULATION CHECKS
# =============================================================================

STREAM_PATTERNS = [
    r"torch\.cuda\.Stream\s*\(",
    r"cuda\.Stream\s*\(",
    r"with\s+torch\.cuda\.stream",
    r"\.wait_stream\s*\(",
    r"\.record_stream\s*\(",
]


def check_stream_injection(code: str) -> tuple[bool, str]:
    """Check for CUDA stream injection patterns."""
    code = _strip_comments(code)

    for pattern in STREAM_PATTERNS:
        if re.search(pattern, code):
            return (True, "Uses CUDA streams (potential timing manipulation)")

    return (False, "")


THREAD_PATTERNS = [
    r"threading\.Thread\s*\(",
    r"import\s+threading",
    r"from\s+threading\s+import",
    r"multiprocessing\.(Process|Pool|Manager|Queue|Pipe)",
    r"import\s+multiprocessing",
    r"concurrent\.futures",
    r"ThreadPoolExecutor",
    r"ProcessPoolExecutor",
]


def check_thread_injection(code: str) -> tuple[bool, str]:
    """Check for thread/multiprocessing injection patterns."""
    code = _strip_comments(code)

    for pattern in THREAD_PATTERNS:
        if re.search(pattern, code):
            return (True, "Uses threading/multiprocessing (potential timing manipulation)")

    return (False, "")


LAZY_TENSOR_PATTERNS = [
    r"_make_subclass",
    r"class\s+\w+.*\(torch\.Tensor\)",
    r"class\s+\w+.*\(Tensor\)",
    r"torch\.Tensor\.__new__",
]


def check_lazy_eval(code: str) -> tuple[bool, str]:
    """Check for lazy tensor creation patterns."""
    code = _strip_comments(code)

    for pattern in LAZY_TENSOR_PATTERNS:
        if re.search(pattern, code):
            return (True, "Uses lazy tensor pattern (potential reward hack)")

    return (False, "")


TIMING_EVENT_PATCH_PATTERNS = [
    r"torch\.cuda\.Event\.record\s*=",
    r"torch\.cuda\.Event\.elapsed_time\s*=",
    r"torch\.cuda\.synchronize\s*=",
    r"torch\.cuda\.Event\s*=",
    r"time\.perf_counter\s*=",
    r"time\.time\s*=",
]


def check_timing_event_patch(code: str) -> tuple[bool, str]:
    """Check for monkey patching of timing functions."""
    code = _strip_comments(code)

    for pattern in TIMING_EVENT_PATCH_PATTERNS:
        if re.search(pattern, code):
            return (True, "Reassigns timing function (monkey patch detected)")

    return (False, "")


# =============================================================================
# BACKEND IMPLEMENTATION CHECKS
# =============================================================================

CUDA_COMPILE_PATTERNS = ["load_inline", "cpp_extension"]


def check_cuda_impl(code: str) -> tuple[bool, str]:
    """Check for valid CUDA kernel implementation."""
    code = _strip_comments(code)
    if "__global__" not in code:
        return (True, "Missing __global__ kernel definition")
    if not any(p in code for p in CUDA_COMPILE_PATTERNS):
        return (True, "Missing load_inline or cpp_extension for compilation")
    return (False, "")


def check_hip_impl(code: str) -> tuple[bool, str]:
    """Check for valid HIP kernel implementation.

    HIP uses the same syntax as CUDA (__global__ kernels compiled via hipcc).
    """
    code = _strip_comments(code)
    if "__global__" not in code:
        return (True, "Missing __global__ kernel definition")
    if not any(p in code for p in CUDA_COMPILE_PATTERNS):
        return (True, "Missing load_inline or cpp_extension for compilation")
    return (False, "")


TRITON_JIT_PATTERN = r"@triton\.(jit|autotune)"
TRITON_OPS_PATTERN = r"\btl\.\w+"


def check_triton_impl(code: str) -> tuple[bool, str]:
    """Check for valid Triton kernel implementation."""
    code = _strip_comments(code)
    if not re.search(TRITON_JIT_PATTERN, code):
        return (True, "Missing @triton.jit or @triton.autotune")
    if not re.search(TRITON_OPS_PATTERN, code):
        return (True, "No tl.* operations found in Triton kernel")
    return (False, "")


TK_WARP_PATTERNS = [
    r"kittens::warp\b",
    r"kittens::warpgroup\b",
    r"::warpgroup::",
    r"::warp::",
    r"warpgroup::",
    r"warp::",
]
TK_TILE_PATTERN = r"(?:kittens::)?(?:st|rt)_\w+\s*<[^>]+>"


def check_tk_impl(code: str) -> tuple[bool, str]:
    """Check for valid ThunderKittens kernel implementation."""
    code = _strip_comments(code)
    if not any(re.search(p, code) for p in TK_WARP_PATTERNS):
        return (True, "Missing ThunderKittens warp/warpgroup patterns")
    if not re.search(TK_TILE_PATTERN, code):
        return (True, "Missing ThunderKittens tile declarations (st_*/rt_*)")
    return (False, "")


def check_cute_impl(code: str) -> tuple[bool, str]:
    """Check for valid CUTLASS/CuTe kernel implementation."""
    code = _strip_comments(code)
    # Accept explicit namespace qualifiers OR using namespace declarations
    valid_patterns = [
        "cute::",
        "cutlass::",
        "from cutlass",
        "using namespace cute",
        "using namespace cutlass",
    ]
    if not any(p in code for p in valid_patterns):
        return (True, "Missing cute:: or cutlass:: namespace (or 'using namespace')")
    return (False, "")


def check_tilelang_impl(code: str) -> tuple[bool, str]:
    """Check for valid TileLang kernel implementation."""
    code = _strip_comments(code)
    if not re.search(r"@T\.prim_func", code):
        return (True, "Missing @T.prim_func decorator")
    return (False, "")


# =============================================================================
# REGISTRY
# =============================================================================

CHECK_FUNCTIONS: dict[str, Callable[[str], tuple[bool, str]]] = {
    # Bypass checks (strict)
    "code_bypass": check_code_bypass,
    "pytorch_wrap": check_pytorch_wrap,
    "timing_event_patch": check_timing_event_patch,
    # Torch ops
    "torch_computation_ops": check_torch_computation_ops,
    # Reward hacking checks
    "cublas_usage": check_cublas_usage,
    "cudnn_usage": check_cudnn_usage,
    "nn_module_forward_call": check_nn_module_forward_call,
    "torch_functional_calls": check_torch_functional_calls,
    # Timing manipulation
    "stream_injection": check_stream_injection,
    "thread_injection": check_thread_injection,
    "lazy_eval": check_lazy_eval,
    # Backend implementation checks
    "cuda_impl": check_cuda_impl,
    "hip_impl": check_hip_impl,
    "triton_impl": check_triton_impl,
    "tk_impl": check_tk_impl,
    "cute_impl": check_cute_impl,
    "tilelang_impl": check_tilelang_impl,
}

BACKEND_IMPL_CHECK = {
    "cuda": "cuda_impl",
    "hip": "hip_impl",
    "triton": "triton_impl",
    "thunderkittens": "tk_impl",
    "cute": "cute_impl",
    "cutlass": "cute_impl",
    "tilelang": "tilelang_impl",
}

# Checks that always cause failure
STRICT_CHECKS = [
    "code_bypass",
    "timing_event_patch",
    "thread_injection",
    "lazy_eval",
    "cublas_usage",  # Direct cuBLAS is reward hacking
    "cudnn_usage",   # Direct cuDNN is reward hacking
    "nn_module_forward_call",  # Calling self.conv(x), self.linear(x) in forward() is reward hacking
    "torch_functional_calls",  # Calling F.linear(), F.conv2d() in forward() is reward hacking
    "torch_computation_ops",  # torch.mm, torch.matmul, torch.conv* etc. are reward hacking
]

# Checks that emit warnings but don't fail
WARNING_CHECKS = [
    "pytorch_wrap",
    "stream_injection",
]


def validate_kernel_static(
    code: str,
    backend: str | None = None,
    forbidden: list[str] | None = None,
    warnings: list[str] | None = None,
) -> tuple[bool, list[str], list[str]]:
    """
    Validate kernel code through static analysis.

    Args:
        code: Kernel source code
        backend: "cuda", "hip", "triton", "cute", "tilelang", "thunderkittens"
        forbidden: Check categories that cause errors (default: STRICT_CHECKS)
        warnings: Check categories that cause warnings (default: WARNING_CHECKS)

    Returns:
        (valid, errors, warnings)
    """
    forbidden_checks = list(forbidden) if forbidden is not None else list(STRICT_CHECKS)
    warning_checks = list(warnings) if warnings is not None else list(WARNING_CHECKS)

    # Add backend implementation check if specified
    # Normalize to lowercase since BACKEND_IMPL_CHECK uses lowercase keys
    backend_lower = backend.lower() if backend else None
    if backend_lower and backend_lower in BACKEND_IMPL_CHECK:
        impl_check = BACKEND_IMPL_CHECK[backend_lower]
        if impl_check not in forbidden_checks:
            forbidden_checks.append(impl_check)

    errors: list[str] = []
    warnings_list: list[str] = []

    for check_name in set(forbidden_checks + warning_checks):
        if check_name not in CHECK_FUNCTIONS:
            continue

        has_issue, msg = CHECK_FUNCTIONS[check_name](code)

        if has_issue:
            if check_name in forbidden_checks:
                errors.append(msg)
            else:
                warnings_list.append(msg)

    valid = len(errors) == 0
    return valid, errors, warnings_list
