"""
Integration tests for reward hack defenses.

Tests the two cut points:
1. validate_kernel_static() - catches hacks in source code
2. run_all_defenses_extended() - catches hacks at runtime

Each test runs a known attack through the full defense pipeline.
Requires torch + CUDA — skipped entirely in CI environments without GPU.
"""

import pytest

torch = pytest.importorskip("torch", reason="torch required for reward hack defense tests")

from wafer_core.utils.kernel_utils.defense import (  # noqa: E402
    run_all_defenses,
    run_all_defenses_extended,
)
from wafer_core.utils.kernel_utils.static_checker import validate_kernel_static  # noqa: E402
from wafer_core.utils.kernel_utils.test_reward_hacks import (  # noqa: E402
    STATIC_HACK_SAMPLES,
    caching,
    clear_cache,
    hardcoded_256,
    identity_kernel,
    lazy_evaluation,
    legit_matmul,
    precision_downgrade,
    thread_injection,
)

requires_cuda = pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")


# =============================================================================
# Cut point 1: validate_kernel_static catches code-level hacks
# =============================================================================


@pytest.mark.parametrize(
    "name,code,expected_checks",
    [(name, code, checks) for name, (code, checks) in STATIC_HACK_SAMPLES.items()],
    ids=list(STATIC_HACK_SAMPLES.keys()),
)
def test_static_checker_catches_hack(name, code, expected_checks):
    """Each hack code sample should fail validate_kernel_static."""
    valid, errors, warnings = validate_kernel_static(code)
    # At least one of the expected checks should have fired
    assert not valid or len(warnings) > 0, (
        f"Static checker missed {name}: expected checks {expected_checks} to fire, "
        f"got errors={errors}, warnings={warnings}"
    )


def test_static_checker_passes_clean_code():
    """Non-hack code should pass static checks."""
    clean = "@triton.jit\ndef kernel(ptr, BLOCK: tl.constexpr):\n    tl.store(ptr, tl.load(ptr))\n"
    valid, errors, warnings = validate_kernel_static(clean, backend="triton")
    assert valid, f"Clean code should pass: errors={errors}"


# =============================================================================
# Cut point 2: run_all_defenses / run_all_defenses_extended
# =============================================================================


@requires_cuda
@pytest.mark.parametrize(
    "name,attack_fn",
    [
        ("thread_injection", thread_injection),
        ("lazy_evaluation", lazy_evaluation),
        ("precision_downgrade", precision_downgrade),
    ],
)
def test_runtime_defense_catches_timing_attack(name, attack_fn):
    """Timing attacks are caught by run_all_defenses."""
    A = torch.randn(256, 256, device="cuda")
    B = torch.randn(256, 256, device="cuda")
    torch.cuda.synchronize()

    all_passed, results, _ = run_all_defenses(legit_matmul, A, B)
    # Sanity: legit passes
    assert all_passed

    all_passed, results, _ = run_all_defenses(attack_fn, A, B)
    assert not all_passed, f"{name} should be caught"


@requires_cuda
def test_monkey_patch_detected():
    """Monkey-patching of timing functions is caught."""
    original = torch.cuda.Event.elapsed_time
    try:
        torch.cuda.Event.elapsed_time = lambda self, end: 0.001
        A = torch.randn(256, 256, device="cuda")
        B = torch.randn(256, 256, device="cuda")
        all_passed, results, _ = run_all_defenses(legit_matmul, A, B)
        assert not all_passed
    finally:
        torch.cuda.Event.elapsed_time = original


@requires_cuda
def test_caching_attack_caught():
    """Caching/memoization is caught by multi-input validation."""
    clear_cache()

    def input_gen():
        return (
            torch.randn(256, 256, device="cuda"),
            torch.randn(256, 256, device="cuda"),
        )

    A, B = input_gen()
    all_passed, results, _ = run_all_defenses_extended(
        caching,
        A,
        B,
        reference_fn=torch.matmul,
        input_generator=input_gen,
    )
    assert not all_passed, "Caching attack should be caught"


@requires_cuda
def test_hardcoded_shapes_caught():
    """Hardcoded optimization is caught by multi-shape validation."""
    A = torch.randn(256, 256, device="cuda")
    B = torch.randn(256, 256, device="cuda")

    all_passed, results, _ = run_all_defenses_extended(
        hardcoded_256,
        A,
        B,
        reference_fn=torch.matmul,
        test_shapes=[(128, 128), (256, 256), (512, 512)],
    )
    assert not all_passed, "Hardcoded shapes attack should be caught"


@requires_cuda
def test_identity_kernel_caught():
    """Identity kernel is caught when reference produces different output."""
    x = torch.randn(256, 256, device="cuda")

    all_passed, results, _ = run_all_defenses_extended(
        identity_kernel,
        x,
        reference_fn=torch.relu,
    )
    assert not all_passed, "Identity kernel should be caught"


@requires_cuda
def test_extended_pipeline_legit_with_all_defenses():
    """Legit kernel passes full extended pipeline with all defense flags enabled.

    This is the actual code path used by `wafer evaluate kernelbench`.
    Exercises: base timing defenses, caching, shape, identity, GEMM exact
    correctness, ULP precision, and memory guards — all through the single
    run_all_defenses_extended() entry point.
    """

    def input_gen():
        return (
            torch.randn(256, 256, device="cuda"),
            torch.randn(256, 256, device="cuda"),
        )

    A, B = input_gen()
    all_passed, results, _ = run_all_defenses_extended(
        legit_matmul,
        A,
        B,
        reference_fn=torch.matmul,
        input_generator=input_gen,
        test_shapes=[(128, 128), (256, 256)],
        is_gemm=True,
        gemm_dims=(128, 128, 128),
        check_precision_ulp=True,
    )
    failed = [(name, msg) for name, passed, msg in results if not passed]
    assert all_passed, f"Legit kernel failed full extended pipeline: {failed}"
