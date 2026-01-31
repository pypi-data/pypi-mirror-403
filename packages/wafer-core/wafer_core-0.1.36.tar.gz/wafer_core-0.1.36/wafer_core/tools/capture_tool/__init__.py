"""Capture tool - Execute commands and capture execution context, artifacts, and metrics.

The capture_tool package exports the CAPTURE_TOOL and exec_capture function.
All helper modules are internal to this package.
"""

import logging
from datetime import datetime, timezone
from pathlib import Path

import trio

from wafer_core.rollouts.dtypes import (
    Tool,
    ToolCall,
    ToolFunction,
    ToolFunctionParameter,
    ToolResult,
)

from wafer_core.tools.capture_tool.core import capture, capture_from_execution_result
from wafer_core.tools.capture_tool.dtypes import (
    ArtifactDiff,
    CaptureConfig,
    CaptureContext,
    CaptureResult,
    DirectorySnapshot,
    ExecutionResult,
    FileInfo,
    GitContext,
    GPUContext,
    MetricsResult,
    RunnerFunction,
    SystemContext,
)
from wafer_core.tools.capture_tool.executor import execute_command
from wafer_core.tools.capture_tool.artifacts import snapshot_directory

logger = logging.getLogger(__name__)

# ── Tool Definition ──────────────────────────────────────────────────────────

CAPTURE_TOOL = Tool(
    type="function",
    function=ToolFunction(
        name="capture",
        description="Execute a command and capture its execution context, artifacts, and metrics. Useful for reproducible experiments and performance analysis.",
        parameters=ToolFunctionParameter(
            type="object",
            properties={
                "command": {"type": "string", "description": "Command to execute"},
                "label": {"type": "string", "description": "Label for this capture (e.g., 'baseline', 'optimized')"},
                "variant": {"type": "string", "description": "Variant identifier (optional)"},
                "tags": {"type": "array", "items": {"type": "string"}, "description": "Tags for categorization"},
                "timeout": {"type": "integer", "description": "Timeout in seconds (default: 300)"},
                "code_denylist": {"type": "array", "items": {"type": "string"}, "description": "File patterns to exclude from code collection"},
                "artifact_denylist": {"type": "array", "items": {"type": "string"}, "description": "File patterns to exclude from artifact collection"},
            }
        ),
        required=["command", "label"]
    )
)


# ── Tool Executor ────────────────────────────────────────────────────────────

async def exec_capture(
    tool_call: ToolCall,
    working_dir: Path,
    cancel_scope: trio.CancelScope | None = None,
) -> ToolResult:
    """Execute command with capture (pure function)."""
    # Validate required args
    if "command" not in tool_call.args:
        return ToolResult(
            tool_call_id=tool_call.id,
            is_error=True,
            content="",
            error="Missing required argument: 'command'"
        )
    if "label" not in tool_call.args:
        return ToolResult(
            tool_call_id=tool_call.id,
            is_error=True,
            content="",
            error="Missing required argument: 'label'"
        )

    command = tool_call.args["command"]
    label = tool_call.args["label"]
    variant = tool_call.args.get("variant")
    tags = tool_call.args.get("tags", [])
    timeout = tool_call.args.get("timeout", 300)
    code_denylist = tool_call.args.get("code_denylist", [])
    artifact_denylist = tool_call.args.get("artifact_denylist", [])

    config = CaptureConfig(
        label=label,
        command=command,
        working_dir=working_dir,
        variant=variant,
        tags=tags,
        code_denylist=code_denylist,
        artifact_denylist=artifact_denylist,
    )

    async def runner(cmd: str, cwd: Path, env_vars: dict[str, str]) -> ExecutionResult:
        start_time = datetime.now(timezone.utc)

        import os
        exec_env = os.environ.copy()
        exec_env.update(env_vars)

        try:
            # Use move_on_after for timeout support
            with trio.move_on_after(timeout):
                process = await trio.run_process(
                    cmd,
                    cwd=str(cwd),
                    env=exec_env,
                    shell=True,
                    capture_stdout=True,
                    capture_stderr=True,
                    check=False,
                )

                end_time = datetime.now(timezone.utc)
                duration = (end_time - start_time).total_seconds()

                stdout = process.stdout.decode("utf-8", errors="replace")
                stderr = process.stderr.decode("utf-8", errors="replace")
                exit_code = process.returncode

                await trio.sleep(1.0)  # Wait for file system flush

                return ExecutionResult(
                    exit_code=exit_code,
                    stdout=stdout,
                    stderr=stderr,
                    duration_seconds=duration,
                    start_time=start_time,
                    end_time=end_time,
                )

            # Timeout occurred (move_on_after exited without raising)
            end_time = datetime.now(timezone.utc)
            duration = (end_time - start_time).total_seconds()
            return ExecutionResult(
                exit_code=-1,
                stdout="",
                stderr=f"Command timed out after {timeout} seconds",
                duration_seconds=duration,
                start_time=start_time,
                end_time=end_time,
            )
        except trio.TooSlowError:
            # Timeout occurred (trio raised TooSlowError)
            end_time = datetime.now(timezone.utc)
            duration = (end_time - start_time).total_seconds()
            return ExecutionResult(
                exit_code=-1,
                stdout="",
                stderr=f"Command timed out after {timeout} seconds",
                duration_seconds=duration,
                start_time=start_time,
                end_time=end_time,
            )
        except trio.Cancelled:
            end_time = datetime.now(timezone.utc)
            duration = (end_time - start_time).total_seconds()
            return ExecutionResult(
                exit_code=-1,
                stdout="",
                stderr="Command aborted",
                duration_seconds=duration,
                start_time=start_time,
                end_time=end_time,
            )
        except Exception as e:
            end_time = datetime.now(timezone.utc)
            duration = (end_time - start_time).total_seconds()
            return ExecutionResult(
                exit_code=-1,
                stdout="",
                stderr=f"Command execution failed: {str(e)}",
                duration_seconds=duration,
                start_time=start_time,
                end_time=end_time,
            )

    try:
        capture_result = await capture(config, runner)

        content_lines = [
            f"Capture completed: {capture_result.label}",
            f"Capture ID: {capture_result.id}",
            f"Command: {capture_result.command}",
            f"Exit code: {capture_result.exit_code}",
            f"Duration: {capture_result.duration_seconds:.2f}s",
        ]

        if capture_result.metrics.stdout_metrics:
            content_lines.append(f"\nMetrics ({len(capture_result.metrics.stdout_metrics)}):")
            for key, value in list(capture_result.metrics.stdout_metrics.items())[:10]:
                content_lines.append(f"  {key}: {value}")
            if len(capture_result.metrics.stdout_metrics) > 10:
                content_lines.append(f"  ... and {len(capture_result.metrics.stdout_metrics) - 10} more")

        if capture_result.artifacts:
            content_lines.append(f"\nArtifacts ({len(capture_result.artifacts)}):")
            for artifact in capture_result.artifacts[:10]:
                content_lines.append(f"  - {artifact}")
            if len(capture_result.artifacts) > 10:
                content_lines.append(f"  ... and {len(capture_result.artifacts) - 10} more")

        if capture_result.stdout:
            stdout_preview = capture_result.stdout[:500]
            content_lines.append(f"\nOutput:\n{stdout_preview}")
            if len(capture_result.stdout) > 500:
                content_lines.append(f"\n... (output truncated, {len(capture_result.stdout)} chars total)")

        return ToolResult(
            tool_call_id=tool_call.id,
            is_error=False,
            content="\n".join(content_lines)
        )

    except Exception as e:
        return ToolResult(
            tool_call_id=tool_call.id,
            is_error=True,
            content="",
            error=f"Capture failed: {str(e)}"
        )


__all__ = [
    "CAPTURE_TOOL",
    "exec_capture",
    "capture",
    "capture_from_execution_result",
    "CaptureConfig",
    "CaptureResult",
    "ExecutionResult",
    "DirectorySnapshot",
    "ArtifactDiff",
    "FileInfo",
    "GitContext",
    "GPUContext",
    "SystemContext",
    "CaptureContext",
    "MetricsResult",
    "RunnerFunction",
    "snapshot_directory",
    "execute_command",
]
