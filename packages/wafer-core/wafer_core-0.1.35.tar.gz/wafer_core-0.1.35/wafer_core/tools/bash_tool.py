"""Bash command execution tool.

Pure function executor for bash commands that accepts ToolCall and returns ToolResult.
Supports optional OS-level sandboxing for security.
"""

from __future__ import annotations

import os
import subprocess
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

import trio

from wafer_core.rollouts.dtypes import (
    Tool,
    ToolCall,
    ToolFunction,
    ToolFunctionParameter,
    ToolResult,
)

if TYPE_CHECKING:
    from wafer_core.sandbox import SandboxPolicy

# Constants
MAX_OUTPUT_SIZE = 30_000  # 30KB (matches Claude Code's default)


class BashPermission(Enum):
    """Result of checking bash command permissions."""

    ALLOW = "allow"  # Execute without prompting
    ASK = "ask"  # Prompt user for approval (interactive only)
    DENY = "deny"  # Always block


@dataclass
class BashPermissionResult:
    """Result of permission check with details."""

    permission: BashPermission
    blocked_commands: list[str]  # Commands that triggered ASK or DENY
    reason: str  # Human-readable explanation


# Type alias for approval callback
ApprovalCallback = Callable[[str, list[str]], Awaitable[bool]]


# ── Tool Definition ──────────────────────────────────────────────────────────

BASH_TOOL = Tool(
    type="function",
    function=ToolFunction(
        name="bash",
        description="Execute a bash command in the current working directory. Returns stdout and stderr.",
        parameters=ToolFunctionParameter(
            type="object",
            properties={
                "command": {"type": "string", "description": "Bash command to execute"},
                "timeout": {"type": "integer", "description": "Timeout in seconds (default: 180)"},
            },
        ),
        required=["command"],
    ),
)


# ── Helper Functions ─────────────────────────────────────────────────────────


def _split_compound_command(command: str) -> list[str]:
    """Split a compound bash command into individual commands.

    Handles &&, ||, ;, and | operators while respecting quotes.
    Returns list of individual command strings.

    Examples:
        "cd foo && ls" -> ["cd foo", "ls"]
        "echo 'a && b'" -> ["echo 'a && b'"]  # quoted && preserved
        "a | b | c" -> ["a", "b", "c"]
    """
    commands = []
    current = []
    in_single_quote = False
    in_double_quote = False
    i = 0

    while i < len(command):
        char = command[i]

        # Handle quotes
        if char == "'" and not in_double_quote:
            in_single_quote = not in_single_quote
            current.append(char)
        elif char == '"' and not in_single_quote:
            in_double_quote = not in_double_quote
            current.append(char)
        # Handle operators (only outside quotes)
        elif not in_single_quote and not in_double_quote:
            # Check for && or ||
            if i + 1 < len(command) and command[i : i + 2] in ("&&", "||"):
                if current:
                    commands.append("".join(current).strip())
                    current = []
                i += 2
                continue
            # Check for ; or |
            if char in (";", "|"):
                if current:
                    commands.append("".join(current).strip())
                    current = []
            else:
                current.append(char)
        else:
            current.append(char)

        i += 1

    # Add final command
    if current:
        cmd = "".join(current).strip()
        if cmd:
            commands.append(cmd)

    return commands


def check_bash_allowlist(command: str, allowlist: list[str] | None) -> str | None:
    """Check if all commands in a (potentially compound) bash command are allowed.

    Splits compound commands (using &&, ||, ;, |) and checks each individual
    command against the allowlist.

    Returns None if all commands allowed, or an error message if any blocked.

    DEPRECATED: Use check_bash_permissions for three-tier allow/ask/deny.
    """
    if allowlist is None:
        return None  # No allowlist = all commands allowed

    # Split compound command into individual commands
    individual_commands = _split_compound_command(command)

    if not individual_commands:
        # Empty command, allow it (will fail at execution anyway)
        return None

    # Check each command against the allowlist
    blocked_commands = []
    for cmd in individual_commands:
        allowed = False
        for prefix in allowlist:
            if cmd.startswith(prefix):
                allowed = True
                break
        if not allowed:
            blocked_commands.append(cmd)

    if blocked_commands:
        allowed_str = ", ".join(f"'{p}'" for p in allowlist)
        blocked_str = ", ".join(f"'{c}'" for c in blocked_commands)
        return (
            f"Command(s) not allowed: {blocked_str}\n"
            f"This environment only permits commands starting with: {allowed_str}"
        )

    return None  # All commands allowed


def _matches_any_prefix(cmd: str, prefixes: list[str]) -> bool:
    """Check if command matches any prefix in the list."""
    return any(cmd.startswith(prefix) for prefix in prefixes)


def check_bash_permissions(
    command: str,
    allowlist: list[str] | None = None,
    denylist: list[str] | None = None,
) -> BashPermissionResult:
    """Check bash command permissions with three-tier allow/ask/deny system.

    Order of evaluation:
    1. DENY: If command matches denylist → always blocked
    2. ALLOW: If command matches allowlist → execute without prompting
    3. ASK: Otherwise → prompt user (or deny in headless mode)

    Args:
        command: The bash command to check (may be compound with &&, ||, etc.)
        allowlist: Commands to allow without prompting (prefix match)
        denylist: Commands to always deny (prefix match)

    Returns:
        BashPermissionResult with permission level and details
    """
    individual_commands = _split_compound_command(command)

    if not individual_commands:
        return BashPermissionResult(
            permission=BashPermission.ALLOW,
            blocked_commands=[],
            reason="Empty command",
        )

    denied_commands: list[str] = []
    ask_commands: list[str] = []

    for cmd in individual_commands:
        # 1. Check denylist first (always wins)
        if denylist and _matches_any_prefix(cmd, denylist):
            denied_commands.append(cmd)
            continue

        # 2. Check allowlist
        if allowlist and _matches_any_prefix(cmd, allowlist):
            continue  # Allowed

        # 3. Not in allowlist → needs approval (if allowlist is set)
        if allowlist is not None:
            ask_commands.append(cmd)

    # Determine final permission
    if denied_commands:
        return BashPermissionResult(
            permission=BashPermission.DENY,
            blocked_commands=denied_commands,
            reason=f"Command(s) blocked (dangerous): {', '.join(repr(c) for c in denied_commands)}",
        )

    if ask_commands:
        return BashPermissionResult(
            permission=BashPermission.ASK,
            blocked_commands=ask_commands,
            reason=f"Command(s) require approval: {', '.join(repr(c) for c in ask_commands)}",
        )

    return BashPermissionResult(
        permission=BashPermission.ALLOW,
        blocked_commands=[],
        reason="All commands allowed",
    )


# ── Pure Function Executor ───────────────────────────────────────────────────


async def exec_bash(
    tool_call: ToolCall,
    working_dir: Path,
    cancel_scope: trio.CancelScope | None = None,
    bash_allowlist: list[str] | None = None,
    bash_denylist: list[str] | None = None,
    approval_callback: ApprovalCallback | None = None,
    sandbox_policy: SandboxPolicy | None = None,
) -> ToolResult:
    """Execute bash command (pure function - takes working_dir as parameter).

    Args:
        tool_call: The tool call containing command and timeout.
        working_dir: Working directory for command execution.
        cancel_scope: Optional trio cancel scope.
        bash_allowlist: Optional list of allowed command prefixes (from template).
        bash_denylist: Optional list of denied command prefixes (always blocked).
        approval_callback: Optional async callback for "ask" tier approval.
            Called with (command, blocked_commands) and returns True to approve.
            If None, "ask" tier commands are denied in headless mode.
        sandbox_policy: Optional sandbox policy for OS-level isolation.
            If provided, command runs in a sandbox with restricted filesystem
            and network access.
    """
    command = tool_call.args["command"]
    timeout = tool_call.args.get("timeout", 180)

    # Check permissions with three-tier system
    perm_result = check_bash_permissions(command, bash_allowlist, bash_denylist)

    if perm_result.permission == BashPermission.DENY:
        return ToolResult(
            tool_call_id=tool_call.id,
            is_error=True,
            content="",
            error=perm_result.reason,
        )

    if perm_result.permission == BashPermission.ASK:
        if approval_callback is None:
            # Headless mode - deny commands that need approval
            return ToolResult(
                tool_call_id=tool_call.id,
                is_error=True,
                content="",
                error=f"{perm_result.reason}\n"
                f"This environment only permits commands starting with: "
                f"{', '.join(repr(p) for p in (bash_allowlist or []))}",
            )

        # Interactive mode - ask user
        approved = await approval_callback(command, perm_result.blocked_commands)
        if not approved:
            return ToolResult(
                tool_call_id=tool_call.id,
                is_error=True,
                content="",
                error="Command rejected by user",
            )

    try:
        # Execute with or without sandbox
        if sandbox_policy is not None:
            return await _exec_bash_sandboxed(tool_call, command, timeout, sandbox_policy)
        else:
            return await _exec_bash_unsandboxed(tool_call, command, timeout, working_dir)

    except subprocess.TimeoutExpired:
        return ToolResult(
            tool_call_id=tool_call.id,
            is_error=True,
            content="",
            error=f"Command timed out after {timeout} seconds",
        )
    except trio.Cancelled:
        return ToolResult(
            tool_call_id=tool_call.id, is_error=True, content="", error="Command aborted"
        )


async def _exec_bash_unsandboxed(
    tool_call: ToolCall,
    command: str,
    timeout: int,
    working_dir: Path,
) -> ToolResult:
    """Execute bash command without sandboxing.

    Uses trio.lowlevel.open_process with streaming stdout/stderr capture.
    This preserves partial output on timeout - critical for debugging long-running
    commands that get killed.
    """
    env = os.environ.copy()
    partial_stdout = b""
    partial_stderr = b""
    timed_out = False
    returncode: int | None = None

    try:
        process = await trio.lowlevel.open_process(
            ["sh", "-c", command],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(working_dir),
            env=env,
        )
    except OSError as e:
        return ToolResult(
            tool_call_id=tool_call.id,
            is_error=True,
            content="",
            error=f"Failed to start process: {e}",
        )

    try:
        # Read streams concurrently with timeout
        with trio.move_on_after(timeout) as cancel_scope:

            async def read_stdout() -> None:
                nonlocal partial_stdout
                assert process.stdout is not None
                async for chunk in process.stdout:
                    partial_stdout += chunk

            async def read_stderr() -> None:
                nonlocal partial_stderr
                assert process.stderr is not None
                async for chunk in process.stderr:
                    partial_stderr += chunk

            async with trio.open_nursery() as nursery:
                nursery.start_soon(read_stdout)
                nursery.start_soon(read_stderr)

        timed_out = cancel_scope.cancelled_caught

        # If timeout occurred, terminate the process
        if timed_out:
            process.terminate()
            # Give process 5s to clean up gracefully
            with trio.move_on_after(5):
                await process.wait()
            # Force kill if still running
            if process.returncode is None:
                process.kill()
                await process.wait()
        else:
            # Normal completion - wait for exit
            await process.wait()

        returncode = process.returncode

    except trio.Cancelled:
        # Re-raise cancellation after cleanup
        process.kill()
        raise

    # Decode output
    stdout = partial_stdout.decode("utf-8", errors="replace")
    stderr = partial_stderr.decode("utf-8", errors="replace")

    output = stdout
    if stderr:
        if output:
            output += "\n"
        output += stderr

    # Add timeout indicator if it occurred (preserving partial output)
    if timed_out:
        if output:
            output += "\n\n"
        output += f"[Command timed out after {timeout} seconds - output above is partial]"

    # Truncate if too large
    if len(output) > MAX_OUTPUT_SIZE:
        output = output[:MAX_OUTPUT_SIZE] + "\n\n... (output truncated)"

    # Determine error status
    if timed_out:
        return ToolResult(
            tool_call_id=tool_call.id,
            is_error=True,
            content=output or "(no output)",
            error=f"Command timed out after {timeout} seconds",
        )

    if returncode != 0:
        return ToolResult(
            tool_call_id=tool_call.id,
            is_error=True,
            content=output or "(no output)",
            error=f"Command exited with code {returncode}",
        )

    return ToolResult(tool_call_id=tool_call.id, is_error=False, content=output or "(no output)")


async def _exec_bash_sandboxed(
    tool_call: ToolCall,
    command: str,
    timeout: int,
    sandbox_policy: SandboxPolicy,
) -> ToolResult:
    """Execute bash command inside OS-level sandbox."""
    from wafer_core.sandbox import execute_sandboxed
    from wafer_core.sandbox.executor import SandboxError, SandboxUnavailableError

    try:
        result = await execute_sandboxed(
            command=command,
            policy=sandbox_policy,
            timeout=timeout,
        )

        output = ""
        if result.stdout:
            output += result.stdout
        if result.stderr:
            if output:
                output += "\n"
            output += result.stderr

        # Truncate if too large
        if len(output) > MAX_OUTPUT_SIZE:
            output = output[:MAX_OUTPUT_SIZE] + "\n\n... (output truncated)"

        # Check if sandbox blocked the operation
        if result.sandbox_denied:
            error_msg = result.denied_reason or "Operation blocked by sandbox: filesystem or network access denied"
            return ToolResult(
                tool_call_id=tool_call.id,
                is_error=True,
                content=output or "(no output)",
                error=error_msg,
            )

        if result.returncode != 0:
            return ToolResult(
                tool_call_id=tool_call.id,
                is_error=True,
                content=output or "(no output)",
                error=f"Command exited with code {result.returncode}",
            )

        return ToolResult(
            tool_call_id=tool_call.id, is_error=False, content=output or "(no output)"
        )

    except SandboxUnavailableError as e:
        return ToolResult(
            tool_call_id=tool_call.id,
            is_error=True,
            content="",
            error=f"Sandbox unavailable: {e}. Use --no-sandbox to run without sandboxing.",
        )
    except SandboxError as e:
        return ToolResult(
            tool_call_id=tool_call.id,
            is_error=True,
            content="",
            error=f"Sandbox error: {e}",
        )
