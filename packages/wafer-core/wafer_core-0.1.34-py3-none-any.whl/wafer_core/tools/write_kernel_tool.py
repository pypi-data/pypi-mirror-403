"""Write kernel tool.

Pure function executor for writing kernel files and automatically testing them on remote GPU.
"""

import logging
from dataclasses import dataclass, replace
from pathlib import Path

from wafer_core.rollouts.dtypes import (
    Tool,
    ToolCall,
    ToolFunction,
    ToolFunctionParameter,
    ToolResult,
)
from wafer_core.utils.code_validation import (
    create_validation_error_result,
    validate_language_requirements,
)
from wafer_core.utils.kernel_utils.deployment import DeploymentState
from wafer_core.utils.remote_execution import (
    KernelExecutionContext,
    ProfilingArtifactConfig,
    execute_kernel_remote,
)
logger = logging.getLogger(__name__)

# Constants
BENCHMARK_NAME = "gpumode"

# Workspace file operation constants
MAX_FILE_SIZE = 100 * 1024  # 100KB - reasonable for kernel code
MAX_FILES = 20  # Prevent runaway file creation
ALLOWED_EXTENSIONS = {".py", ".txt", ".md", ".cu"}  # Explicit whitelist


# ── Data Classes ──────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class KernelSubmission:
    """Record of a single kernel submission attempt.
    
    Immutable data structure following CLASSES_VS_FUNCTIONAL.md decision tree:
    "Is it just data?" → Frozen dataclass
    """

    filepath: str
    attempt_number: int

    # Compilation
    compiled: bool = False
    compile_error: str | None = None
    error_details: str | None = None

    # Test results (populated after execution)
    correctness_score: float = 0.0
    geomean_speedup: float = 0.0
    all_correct: bool = False

    # Raw results for detailed analysis
    raw_results: dict | None = None

    # Artifact path (from submission library)
    artifact_path: str | None = None


@dataclass(frozen=True)
class WriteKernelState:
    """Immutable state container for write_kernel tool execution."""

    workspace_dir: Path
    submissions: tuple[KernelSubmission, ...]  # Tuple for immutability
    best_submission: KernelSubmission | None
    deployment_state: DeploymentState | None
    deployment_state_cache: dict
    language: str
    problem_id: str
    sample_data: dict
    test_suite: str
    reference_backend: str
    benchmark_suite: str
    profile_on_success: bool
    ncu_on_success: bool
    artifacts_dir: Path | None
    available_targets: list | None


@dataclass(frozen=True)
class WriteKernelOutput:
    """Output from write_kernel execution with updated state."""

    tool_result: ToolResult
    updated_submissions: tuple[KernelSubmission, ...]
    updated_best: KernelSubmission | None
    updated_deployment_state: DeploymentState | None
    updated_deployment_state_cache: dict


# ── Tool Definition ───────────────────────────────────────────────────────────

WRITE_KERNEL_TOOL = Tool(
    type="function",
    function=ToolFunction(
        name="write_kernel",
        description="Write a kernel file to workspace and automatically test it on remote GPU. Returns correctness and performance feedback.",
        parameters=ToolFunctionParameter(
            type="object",
            properties={
                "filepath": {
                    "type": "string",
                    "description": "Filename for the kernel (e.g., 'kernel.py', 'optimized.py')",
                },
                "code": {"type": "string", "description": "Complete kernel implementation code"},
            },
        ),
        required=["filepath", "code"],
    ),
)


# ── Workspace File Operations ──────────────────────────────────────────────────

def validate_path(filepath: str, workspace_dir: Path) -> tuple[Path | None, str | None]:
    """Validate path for workspace access.

    Args:
        filepath: Relative path from user
        workspace_dir: Workspace root directory

    Returns:
        (resolved_path, error_message) - one will be None
    """
    assert workspace_dir is not None, "workspace_dir must be set"
    assert workspace_dir.exists(), "workspace_dir must exist"

    if not filepath:
        return None, "Filepath cannot be empty"

    if Path(filepath).is_absolute():
        return None, f"Absolute paths not allowed: {filepath}"

    full_path = (workspace_dir / filepath).resolve()

    try:
        full_path.relative_to(workspace_dir.resolve())
    except ValueError:
        return None, f"Path outside workspace: {filepath}"

    if full_path.suffix and full_path.suffix not in ALLOWED_EXTENSIONS:
        return (
            None,
            f"File extension not allowed: {full_path.suffix}. Allowed: {ALLOWED_EXTENSIONS}",
        )

    if any(part.startswith(".") for part in Path(filepath).parts):
        return None, f"Hidden files/directories not allowed: {filepath}"

    return full_path, None


def check_workspace_limits(workspace_dir: Path) -> tuple[bool, str | None]:
    """Check workspace hasn't exceeded limits.

    Args:
        workspace_dir: Workspace root directory

    Returns:
        (ok, error_message)
    """
    assert workspace_dir is not None

    num_files = len(list(workspace_dir.rglob("*")))
    if num_files >= MAX_FILES:
        return False, f"Workspace file limit reached ({MAX_FILES} files)"

    return True, None


async def write_file(filepath: str, content: str, workspace_dir: Path) -> ToolResult:
    """Write file to workspace.

    Args:
        filepath: Relative path to write
        content: File content
        workspace_dir: Workspace root directory

    Returns:
        ToolResult with success/error
    """
    path, err = validate_path(filepath, workspace_dir)
    if err:
        return ToolResult(is_error=True, content="", error=err)
    assert path is not None

    ok, err = check_workspace_limits(workspace_dir)
    if not ok:
        return ToolResult(is_error=True, content="", error=err)

    content_size = len(content.encode("utf-8"))
    if content_size > MAX_FILE_SIZE:
        return ToolResult(
            is_error=True,
            content="",
            error=f"File too large: {content_size} bytes (max {MAX_FILE_SIZE})",
        )

    path.parent.mkdir(parents=True, exist_ok=True)

    try:
        path.write_text(content)
        logger.info(f"wrote file: {path} (workspace: {workspace_dir})")
        if not path.exists():
            logger.error(f"file write succeeded but file doesn't exist! {path}")
        else:
            logger.info(f"verified file exists: {path}")
        return ToolResult(is_error=False, content=f"Wrote {content_size} bytes to {filepath}", error=None)
    except Exception as e:
        return ToolResult(is_error=True, content="", error=f"Failed to write file: {e}")


# ── Pure Helper Functions ──────────────────────────────────────────────────────

def format_error_feedback(submission: KernelSubmission) -> str:
    """Format feedback for compilation/execution errors (pure function)."""
    error_section = submission.compile_error or "Unknown error"

    return f"""Kernel compilation/execution failed (Attempt {submission.attempt_number}):

{error_section}

Please fix the error and submit a corrected version."""


def format_failed_tests(failed_tests: list[dict], max_tests: int = 3) -> str:
    """Format details of failed tests for feedback (pure function).

    Args:
        failed_tests: List of failed test dicts from correctness_tests
        max_tests: Maximum number of tests to show details for

    Returns:
        Formatted string with test failure details
    """
    if not failed_tests:
        return ""

    lines = []
    shown = 0

    for test in failed_tests[:max_tests]:
        test_name = test.get("test_name", "unknown")
        error_msg = test.get("error_msg", "")
        error_type = test.get("error_type", "")
        test_params = test.get("test_params", "")

        # Format test header
        lines.append(f"  ❌ {test_name}")
        if test_params:
            lines.append(f"     Parameters: {test_params}")

        # Format error details
        if error_type:
            lines.append(f"     Error type: {error_type}")

        if error_msg:
            # Truncate very long error messages but show enough context
            error_lines = error_msg.split("\n")
            if len(error_lines) > 10:
                # Show first 5 and last 3 lines
                truncated = error_lines[:5] + ["     ..."] + error_lines[-3:]
                error_text = "\n".join(f"     {line}" for line in truncated)
            else:
                error_text = "\n".join(f"     {line}" for line in error_lines)
            lines.append(f"     Details:\n{error_text}")

        lines.append("")  # Blank line between tests
        shown += 1

    # Note if more tests failed
    remaining = len(failed_tests) - shown
    if remaining > 0:
        lines.append(f"  ... and {remaining} more test(s) failed")

    return "\n".join(lines)


def format_success_feedback(
    submission: KernelSubmission, best_submission: KernelSubmission | None
) -> str:
    """Format feedback for successful execution (pure function)."""
    # Build correctness summary
    if submission.all_correct:
        correctness_summary = "✅ All correctness tests passed!"
    else:
        passed = submission.raw_results.get("passed_tests", 0) if submission.raw_results else 0
        total = submission.raw_results.get("total_tests", 0) if submission.raw_results else 0
        correctness_summary = f"⚠️  Correctness: {passed}/{total} tests passed ({submission.correctness_score:.1%})"

    # Build performance summary
    perf_summary = f"Performance: {submission.geomean_speedup:.2f}x speedup vs reference"

    # Best submission marker
    is_best = best_submission == submission
    best_marker = " (NEW BEST!)" if is_best else ""

    # Build failed test details if not all correct
    failed_tests_section = ""
    if not submission.all_correct and submission.raw_results:
        correctness_tests = submission.raw_results.get("correctness_tests", [])
        failed_tests = [t for t in correctness_tests if not t.get("is_correct", True)]
        if failed_tests:
            failed_tests_section = f"\nFailed tests:\n{format_failed_tests(failed_tests)}\n"

    # Build final message
    if submission.all_correct:
        closing = "Great! All tests passed."
    else:
        closing = "Please fix the failing tests before optimizing performance."

    return f"""Kernel test results (Attempt {submission.attempt_number}){best_marker}:

{correctness_summary}

{perf_summary}
{failed_tests_section}
{closing}"""


def is_better_than_best(
    submission: KernelSubmission, best_submission: KernelSubmission | None
) -> bool:
    """Check if submission is better than current best (pure function).

    Criteria:
    1. Correctness first (must pass all tests)
    2. Then performance (higher speedup)
    """
    if not best_submission:
        return True

    # Prioritize correctness
    if submission.all_correct and not best_submission.all_correct:
        return True
    if not submission.all_correct and best_submission.all_correct:
        return False

    # Both correct or both incorrect - compare performance
    return submission.geomean_speedup > best_submission.geomean_speedup


# ── Pure Function Executor ────────────────────────────────────────────────────

async def exec_write_kernel(
    tool_call: ToolCall,
    state: WriteKernelState,
) -> WriteKernelOutput:
    """Execute write_kernel tool (pure function - takes state as parameter, returns updated state).

    Writes kernel file to workspace and automatically submits for testing on remote GPU.
    Returns ToolResult for LLM and updated state with new submission.
    """
    filepath = tool_call.args["filepath"]
    code = tool_call.args["code"]

    # Write to workspace using pure function
    write_result = await write_file(filepath, code, state.workspace_dir)
    if write_result.is_error:
        return WriteKernelOutput(
            tool_result=ToolResult(
                tool_call_id=tool_call.id,
                is_error=True,
                content="",
                error=write_result.error,
            ),
            updated_submissions=state.submissions,
            updated_best=state.best_submission,
            updated_deployment_state=state.deployment_state,
            updated_deployment_state_cache=state.deployment_state_cache,
        )

    logger.debug(f"wrote kernel to workspace: {filepath} ({len(code)} chars)")
    logger.debug(f"attempt: {len(state.submissions) + 1}")

    # Create submission record
    attempt_number = len(state.submissions) + 1
    submission = KernelSubmission(filepath=filepath, attempt_number=attempt_number)

    # Validate language requirements (CuteDSL)
    is_valid, validation_error = validate_language_requirements(code, state.language)
    if not is_valid:
        logger.warning(f"⚠️  Language validation failed: {validation_error}")
        eval_results = create_validation_error_result(validation_error, state.language)

        # Treat as compilation failure
        failed_submission = replace(
            submission,
            compiled=False,
            compile_error=eval_results.get("error_message", "Validation failed"),
        )

        # Create new state with appended submission
        new_submissions = state.submissions + (failed_submission,)
        new_state = replace(state, submissions=new_submissions)

        error_msg = format_error_feedback(failed_submission)
        logger.info("tests failed: validation error")

        return WriteKernelOutput(
            tool_result=ToolResult(
                tool_call_id=tool_call.id,
                is_error=True,
                content="",
                error=error_msg,
            ),
            updated_submissions=new_state.submissions,
            updated_best=new_state.best_submission,
            updated_deployment_state=new_state.deployment_state,
            updated_deployment_state_cache=new_state.deployment_state_cache,
        )

    # Execute on remote GPU using pure function
    logger.info(f"testing kernel on remote gpu (problem: {state.problem_id})")

    # Create execution context (used by both legacy and pluggable target paths)
    context = KernelExecutionContext(
        problem_id=state.problem_id,
        sample_data=state.sample_data,
        test_suite=state.test_suite,
        reference_backend=state.reference_backend,
        benchmark_name=BENCHMARK_NAME,
        benchmark_suite=state.benchmark_suite,
        language=None,  # GPUMode doesn't use language filter
    )

    # Create profiling config (used by both legacy and pluggable target paths)
    profiling_config = ProfilingArtifactConfig(
        profile_on_success=state.profile_on_success,
        ncu_on_success=state.ncu_on_success,
        artifacts_dir=state.artifacts_dir,
    )

    # Handle both legacy mode and targets mode
    eval_results: dict | None = None
    err: str | None = None
    updated_cache = state.deployment_state_cache.copy()

    if state.available_targets is not None:
        # Targets mode: Use pluggable target system
        from wafer_core.utils.kernel_utils.targets import (
            run_operation_on_target,
            select_target_for_operation,
        )

        # Select target for correctness operation
        target = select_target_for_operation("correctness", state.available_targets)
        if target is None:
            return WriteKernelOutput(
                tool_result=ToolResult(
                    tool_call_id=tool_call.id,
                    is_error=True,
                    content="",
                    error="No capable target available for correctness testing",
                ),
                updated_submissions=state.submissions,
                updated_best=state.best_submission,
                updated_deployment_state=state.deployment_state,
                updated_deployment_state_cache=state.deployment_state_cache,
            )

        logger.debug(f"   Selected target for correctness: {target.name}")

        # Run on selected target (with deployment state caching)
        eval_results, err = await run_operation_on_target(
            operation="correctness",
            target=target,
            kernel_code=code,
            context=context,
            profiling_config=profiling_config,
            check_availability=True,
            deployment_state_cache=updated_cache,
        )

        # Update cache from the function (it may have modified it)
        # Note: run_operation_on_target may mutate the cache dict, so we need to track changes
        # For now, we'll pass the cache through and let the environment update it

    else:
        # Legacy mode: Use direct deployment
        assert state.deployment_state is not None, (
            "_deployment_state not initialized - call setup_remote_environment first"
        )

        eval_results = await execute_kernel_remote(
            deployment_state=state.deployment_state,
            kernel_code=code,
            context=context,
            profiling_config=profiling_config,
        )

    # Handle execution errors (targets mode)
    if err:
        # Treat as compilation/execution failure
        failed_submission = replace(
            submission,
            compiled=False,
            compile_error=err,
        )

        new_submissions = state.submissions + (failed_submission,)
        new_state = replace(state, submissions=new_submissions)

        error_msg = format_error_feedback(failed_submission)
        logger.info(f"tests failed: {err}")

        return WriteKernelOutput(
            tool_result=ToolResult(
                tool_call_id=tool_call.id,
                is_error=True,
                content="",
                error=error_msg,
            ),
            updated_submissions=new_state.submissions,
            updated_best=new_state.best_submission,
            updated_deployment_state=new_state.deployment_state,
            updated_deployment_state_cache=updated_cache,
        )

    # Type narrowing: execute_kernel_remote always returns dict, never None
    assert eval_results is not None, "eval_results should not be None"

    if not eval_results["compiled"]:
        # Compilation failure
        failed_submission = replace(
            submission,
            compiled=False,
            compile_error=eval_results.get("error_message", "Unknown error"),
        )

        new_submissions = state.submissions + (failed_submission,)
        new_state = replace(state, submissions=new_submissions)

        error_msg = format_error_feedback(failed_submission)
        logger.info("tests failed: compilation error")

        return WriteKernelOutput(
            tool_result=ToolResult(
                tool_call_id=tool_call.id,
                is_error=True,
                content="",
                error=error_msg,
            ),
            updated_submissions=new_state.submissions,
            updated_best=new_state.best_submission,
            updated_deployment_state=new_state.deployment_state,
            updated_deployment_state_cache=updated_cache,
        )
    else:
        # Success - parse results
        success_submission = replace(
            submission,
            compiled=True,
            correctness_score=eval_results["correctness_score"],
            geomean_speedup=eval_results["geomean_speedup"],
            all_correct=eval_results["all_correct"],
            raw_results=eval_results,
        )

        # Determine new best submission (pure computation)
        new_best = (
            success_submission
            if is_better_than_best(success_submission, state.best_submission)
            else state.best_submission
        )

        # Create new state with updated submissions and best
        new_submissions = state.submissions + (success_submission,)
        new_state = replace(
            state,
            submissions=new_submissions,
            best_submission=new_best,
        )

        success_msg = format_success_feedback(success_submission, new_best)

        if success_submission.all_correct:
            logger.info(
                f"tests complete: all correct, speedup={success_submission.geomean_speedup:.2f}x"
            )
        else:
            passed = eval_results.get("passed_tests", 0)
            total = eval_results.get("total_tests", 0)
            logger.info(
                f"tests complete: {passed}/{total} passed, speedup={success_submission.geomean_speedup:.2f}x"
            )

        return WriteKernelOutput(
            tool_result=ToolResult(
                tool_call_id=tool_call.id,
                is_error=False,
                content=success_msg,
                error=None,
            ),
            updated_submissions=new_state.submissions,
            updated_best=new_state.best_submission,
            updated_deployment_state=new_state.deployment_state,
            updated_deployment_state_cache=updated_cache,
        )
