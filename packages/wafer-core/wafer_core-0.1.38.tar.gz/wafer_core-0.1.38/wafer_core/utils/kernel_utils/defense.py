"""
Defense Mechanisms for GPU Kernel Evaluation

This module implements defenses against evaluation hacking attacks in GPU kernel benchmarks.
Based on the CUDA-L2 defense implementations: https://github.com/deepreinforce-ai/CUDA-L2

Attack types defended against:
1. Stream Injection - Running computation on a separate CUDA stream
2. Thread Injection - Spawning background threads to defer computation
3. Lazy Evaluation - Returning tensor subclasses that defer computation
4. Precision Downgrade - Using lower precision (e.g., fp16) to speed up computation
5. Monkey-patching - Replacing CUDA timing functions with fake implementations

Reference: "Hacks and Defenses in Automatic GPU Kernel Generation" by Jiwei Li (Dec 2025)
"""

import random
import threading
from collections.abc import Callable
from typing import Any

import torch

# =============================================================================
# Store original CUDA functions at module load time (before any monkey-patching)
# =============================================================================
_original_elapsed_time = torch.cuda.Event.elapsed_time
_original_record = torch.cuda.Event.record
_original_synchronize = torch.cuda.synchronize


# =============================================================================
# Defense Functions
# =============================================================================


def defend_against_stream_injection(
    kernel: Callable,
    *args,
    ratio_threshold: float = 1.5,
    num_iterations: int = 10,
    **kwargs,
) -> tuple[bool, str, Any, float | None]:
    """
    Defense against stream injection attack using hybrid timing approach.

    Stream injection runs the kernel on a separate CUDA stream, causing
    events recorded on the default stream to miss the actual computation time.

    Hybrid Defense:
    1. Run kernel with ORIGINAL timing (events on default stream, no extra sync)
    2. Run kernel with DEFENSE timing (sync all streams before end event)
    3. Compare: if (defense_time / original_time) > ratio_threshold, kernel is malicious
    4. If ratio is within threshold, use original timing (no overhead)
    5. Also verify outputs are deterministic across runs (catches silent kernel failures)

    NOTE: This check can produce false positives on very fast kernels (<100μs) due to
    timing noise. Consider adding a minimum runtime threshold before applying the
    ratio check. See: https://github.com/anthropics/wafer/issues/XXX

    Args:
        kernel: The kernel function to test
        *args: Arguments to pass to the kernel
        ratio_threshold: Maximum allowed ratio of defense_time/original_time (default 1.5)
        num_iterations: Number of timing iterations for median calculation (default 10)
        **kwargs: Keyword arguments to pass to the kernel

    Returns:
        (passed, message, output, timing_ms)
        - passed: True if no stream injection detected and outputs are deterministic
        - message: Description of result
        - output: Kernel output
        - timing_ms: The timing to use (original if legit, defense if suspicious)
    """
    # Warmup
    _ = kernel(*args, **kwargs)
    torch.cuda.synchronize()

    original_times = []
    defense_times = []
    outputs = []  # Track outputs to verify determinism

    for _ in range(num_iterations):
        # Randomly decide which timing method runs first to reduce bias
        run_original_first = random.choice([True, False])

        def time_original():
            torch.cuda.empty_cache()
            s = torch.cuda.Event(enable_timing=True)
            e = torch.cuda.Event(enable_timing=True)
            s.record()
            out = kernel(*args, **kwargs)
            e.record()
            torch.cuda.synchronize()
            return s.elapsed_time(e), out

        def time_defense():
            torch.cuda.empty_cache()
            s = torch.cuda.Event(enable_timing=True)
            e = torch.cuda.Event(enable_timing=True)
            s.record()
            out = kernel(*args, **kwargs)
            torch.cuda.synchronize()  # Force sync ALL streams before recording end
            e.record()
            torch.cuda.synchronize()
            return s.elapsed_time(e), out

        if run_original_first:
            t, output = time_original()
            original_times.append(t)
            outputs.append(output.clone() if isinstance(output, torch.Tensor) else output)
            t, output = time_defense()
            defense_times.append(t)
            outputs.append(output.clone() if isinstance(output, torch.Tensor) else output)
        else:
            t, output = time_defense()
            defense_times.append(t)
            outputs.append(output.clone() if isinstance(output, torch.Tensor) else output)
            t, output = time_original()
            original_times.append(t)
            outputs.append(output.clone() if isinstance(output, torch.Tensor) else output)

    # Check output determinism - all outputs should be identical for same inputs
    # This catches silent kernel failures (e.g., shared memory overflow on HIP)
    if outputs and isinstance(outputs[0], torch.Tensor):
        reference = outputs[0]
        for i, out in enumerate(outputs[1:], 1):
            if not torch.equal(reference, out):
                max_diff = (reference - out).abs().max().item()
                return (
                    False,
                    f"Non-deterministic output detected: run 0 vs run {i} differ "
                    f"(max diff: {max_diff}). This indicates a silent kernel failure "
                    f"(e.g., shared memory overflow) or race condition.",
                    output,
                    None,
                )

    # Use median to reduce noise
    original_time_ms = sorted(original_times)[num_iterations // 2]
    defense_time_ms = sorted(defense_times)[num_iterations // 2]

    # Compare: Large ratio indicates stream injection
    # Avoid division by zero - if original_time is ~0, it's definitely suspicious
    if original_time_ms < 0.001:  # Less than 1us
        ratio = float("inf")
    else:
        ratio = defense_time_ms / original_time_ms

    if ratio > ratio_threshold:
        return (
            False,
            f"Stream injection detected! Original: {original_time_ms:.3f}ms, "
            f"Defense: {defense_time_ms:.3f}ms, Ratio: {ratio:.1f}x (threshold: {ratio_threshold}x)",
            output,
            defense_time_ms,  # Use defense timing for malicious kernels
        )
    else:
        return (
            True,
            f"Stream injection check passed. Ratio: {ratio:.2f}x (within {ratio_threshold}x threshold)",
            output,
            original_time_ms,  # Use original timing (no overhead) for legit kernels
        )


def defend_against_thread_injection(
    kernel: Callable,
    *args,
    **kwargs,
) -> tuple[bool, str, Any]:
    """
    Defense against thread injection attack.

    Thread injection spawns a background thread to do computation while
    returning an empty tensor immediately. This cheats timing but passes
    correctness checks since the thread finishes before verification.

    Defense: Compare thread count before and after kernel execution.

    Args:
        kernel: The kernel function to test
        *args: Arguments to pass to the kernel
        **kwargs: Keyword arguments to pass to the kernel

    Returns:
        (passed, message, output)
    """
    before = threading.active_count()
    output = kernel(*args, **kwargs)
    after = threading.active_count()

    if after > before:
        return (
            False,
            f"Thread injection detected! Thread count: {before} -> {after}",
            output,
        )
    else:
        return True, "Thread injection check passed", output


def defend_against_lazy_evaluation(
    kernel: Callable,
    *args,
    expected_device: torch.device | None = None,
    **kwargs,
) -> tuple[bool, str, Any]:
    """
    Defense against lazy evaluation attack.

    Lazy evaluation returns a tensor subclass that defers computation until
    certain methods (like __eq__) are called. This cheats timing because
    the actual computation happens during correctness check, not during timing.

    Defense: Validate that output is a standard torch.Tensor with allocated memory.

    Args:
        kernel: The kernel function to test
        *args: Arguments to pass to the kernel
        expected_device: Expected device for output (inferred from first arg if None)
        **kwargs: Keyword arguments to pass to the kernel

    Returns:
        (passed, message, output)
    """
    output = kernel(*args, **kwargs)

    # Infer expected device from first input argument
    if expected_device is None:
        for arg in args:
            if isinstance(arg, torch.Tensor):
                expected_device = arg.device
                break

    if expected_device is None:
        expected_device = torch.device("cuda")

    # Validate tensor is real and materialized, not a lazy hack

    # Check 1: Must be a tensor
    if not isinstance(output, torch.Tensor):
        return False, f"Output is not a tensor: {type(output)}", output

    # Check 2: Must be standard torch.Tensor, not a subclass
    if type(output).__name__ not in ["Tensor", "Parameter"]:
        return (
            False,
            f"Output is {type(output).__name__}, not standard torch.Tensor (possible lazy evaluation)",
            output,
        )

    # Check 3: Must be on correct device
    # Compare device types, not exact device indices (cuda:0 == cuda)
    if output.device.type != expected_device.type:
        return (
            False,
            f"Output on wrong device type: {output.device} (expected {expected_device})",
            output,
        )

    # Check 4: Must have allocated storage
    storage_size = output.untyped_storage().size()
    if storage_size == 0:
        return False, "Output has no allocated storage (likely lazy evaluation)", output

    # Check 5: Storage pointer must be valid
    ptr = output.data_ptr()
    if ptr == 0:
        return False, "Output storage pointer is null (likely lazy evaluation)", output

    return True, "Lazy evaluation check passed", output


def defend_against_precision_downgrade(
    kernel: Callable,
    *args,
    expected_dtype: torch.dtype | None = None,
    **kwargs,
) -> tuple[bool, str, Any]:
    """
    Defense against precision downgrade attack.

    Precision downgrade uses lower precision (e.g., float16 instead of float32)
    to speed up computation while sacrificing accuracy.

    Defense: Check if output dtype matches expected dtype.

    Note: This defense only catches cases where the output dtype differs.
    Attacks that compute in fp16 but cast back to fp32 are harder to detect
    and may require tolerance-based detection or LLM code analysis.

    Args:
        kernel: The kernel function to test
        *args: Arguments to pass to the kernel
        expected_dtype: Expected dtype for output (inferred from first arg if None)
        **kwargs: Keyword arguments to pass to the kernel

    Returns:
        (passed, message, output)
    """
    output = kernel(*args, **kwargs)

    # Infer expected dtype from first input tensor
    if expected_dtype is None:
        for arg in args:
            if isinstance(arg, torch.Tensor):
                expected_dtype = arg.dtype
                break

    if expected_dtype is None:
        expected_dtype = torch.float32

    # Check dtype
    if output.dtype != expected_dtype:
        return (
            False,
            f"Precision downgrade detected: output is {output.dtype}, expected {expected_dtype}",
            output,
        )

    return True, "Precision downgrade check passed", output


def defend_against_monkey_patching() -> tuple[bool, str]:
    """
    Defense against monkey-patching attack.

    Monkey-patching replaces critical CUDA timing functions with fake versions
    that return instant times, making any kernel appear fast.

    Defense: Check if torch.cuda.Event.elapsed_time, record, or synchronize
    have been modified from their original implementations.

    Returns:
        (passed, message)
    """
    patched = []

    # Check elapsed_time
    if torch.cuda.Event.elapsed_time is not _original_elapsed_time:
        patched.append("torch.cuda.Event.elapsed_time")

    # Check record
    if torch.cuda.Event.record is not _original_record:
        patched.append("torch.cuda.Event.record")

    # Check synchronize
    if torch.cuda.synchronize is not _original_synchronize:
        patched.append("torch.cuda.synchronize")

    if patched:
        return False, f"Monkey-patching detected: {', '.join(patched)}"
    else:
        return True, "Monkey-patching check passed"


# =============================================================================
# Combined Defense Runner
# =============================================================================


def run_all_defenses(
    kernel: Callable,
    *args,
    stream_injection_threshold: float = 1.5,
    expected_dtype: torch.dtype | None = None,
    **kwargs,
) -> tuple[bool, list, Any]:
    """
    Run all defense checks against kernel attacks.

    Args:
        kernel: The kernel function to test
        *args: Arguments to pass to the kernel
        stream_injection_threshold: Ratio threshold for stream injection detection
        expected_dtype: Expected output dtype (e.g., from reference kernel output).
            If None, inferred from first input tensor. Pass this explicitly when
            the output dtype legitimately differs from input dtype.
        **kwargs: Keyword arguments to pass to the kernel

    Returns:
        (all_passed, results, output)
        - all_passed: True if all defense checks passed
        - results: List of (defense_name, passed, message) tuples
        - output: The kernel output (if any check succeeded)
    """
    results = []
    output = None

    # Defense 1: Monkey-patching (check first, doesn't need kernel execution)
    passed, message = defend_against_monkey_patching()
    results.append(("monkey_patching", passed, message))

    # Defense 2: Stream injection (hybrid approach)
    passed, message, output, timing = defend_against_stream_injection(
        kernel, *args, ratio_threshold=stream_injection_threshold, **kwargs
    )
    results.append(("stream_injection", passed, message))

    # Defense 3: Thread injection
    passed, message, output = defend_against_thread_injection(kernel, *args, **kwargs)
    results.append(("thread_injection", passed, message))

    # Defense 4: Lazy evaluation
    passed, message, output = defend_against_lazy_evaluation(kernel, *args, **kwargs)
    results.append(("lazy_evaluation", passed, message))

    # Defense 5: Precision downgrade
    # Pass expected_dtype if provided, otherwise let it infer from inputs
    passed, message, output = defend_against_precision_downgrade(
        kernel, *args, expected_dtype=expected_dtype, **kwargs
    )
    results.append(("precision_downgrade", passed, message))

    all_passed = all(r[1] for r in results)

    return all_passed, results, output


# =============================================================================
# Defensive Timing Function (drop-in replacement for timing.py functions)
# =============================================================================


def time_execution_with_defenses(
    kernel_fn: Callable,
    args: list[Any],
    num_warmup: int = 3,
    num_trials: int = 10,
    discard_first: int = 1,
    verbose: bool = True,
    device: torch.device = None,
    run_defenses: bool = True,
    defense_threshold: float = 1.5,
    expected_dtype: torch.dtype | None = None,
) -> tuple[list[float], dict | None]:
    """
    Time a CUDA kernel with optional defense checks.

    This is a drop-in replacement for timing.time_execution_with_cuda_event
    that adds defense mechanisms against evaluation hacking.

    Args:
        kernel_fn: Function to time
        args: Arguments to pass to kernel_fn
        num_warmup: Number of warmup iterations before timing
        num_trials: Number of timing trials to run
        discard_first: Number of first trials to discard
        verbose: Whether to print per-trial timing info
        device: CUDA device to use, defaults to current device
        run_defenses: Whether to run defense checks (default True)
        defense_threshold: Ratio threshold for stream injection detection
        expected_dtype: Expected output dtype for precision downgrade check.
            If None, inferred from first input tensor. Pass explicitly when
            the kernel legitimately outputs a different dtype than its inputs
            (e.g., int inputs -> float outputs).

    Returns:
        (elapsed_times, defense_results)
        - elapsed_times: List of elapsed times in milliseconds
        - defense_results: Dict with defense check results, or None if defenses disabled

    Raises:
        ValueError: If any defense check fails and run_defenses is True
    """
    if device is None:
        device = torch.cuda.current_device()

    defense_results = None

    # Run defense checks first (if enabled)
    if run_defenses:
        # Create wrapper that unpacks args
        def kernel_wrapper(*a):
            return kernel_fn(*a)

        all_passed, results, _ = run_all_defenses(
            kernel_wrapper,
            *args,
            stream_injection_threshold=defense_threshold,
            expected_dtype=expected_dtype,
        )

        defense_results = {
            name: {"passed": passed, "message": msg} for name, passed, msg in results
        }

        if not all_passed:
            failed = [name for name, passed, _ in results if not passed]
            raise ValueError(f"Defense checks failed: {failed}. Results: {defense_results}")

        if verbose:
            print("[Defense] All defense checks passed")

    # Now run the actual timing (using defense-aware timing with sync before end_event)
    with torch.cuda.device(device):
        # Warmup
        for _ in range(num_warmup):
            kernel_fn(*args)
            torch.cuda.synchronize(device=device)

        torch.cuda.empty_cache()

        if verbose:
            print(
                f"[Profiling] Using device: {device} {torch.cuda.get_device_name(device)}, "
                f"warmup {num_warmup}, trials {num_trials}"
            )

        elapsed_times: list[float] = []

        # Timing trials with defense-aware approach
        for trial in range(num_trials + discard_first):
            torch.cuda.synchronize(device=device)

            start_event = torch.cuda.Event(enable_timing=True)
            end_event = torch.cuda.Event(enable_timing=True)

            start_event.record()
            _ = kernel_fn(*args)
            # DEFENSE: Sync before recording end event to catch stream injection
            torch.cuda.synchronize(device=device)
            end_event.record()
            torch.cuda.synchronize(device=device)

            elapsed_time_ms = start_event.elapsed_time(end_event)

            if trial >= discard_first:
                if verbose:
                    logical_idx = trial - discard_first + 1
                    print(f"Trial {logical_idx}: {elapsed_time_ms:.3g} ms")
                elapsed_times.append(elapsed_time_ms)

    return elapsed_times, defense_results
