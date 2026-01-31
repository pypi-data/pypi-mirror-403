"""Sandbox execution for untrusted commands.

This module provides OS-level sandboxing for bash command execution,
protecting users from accidental or malicious agent actions.

Supported platforms:
- macOS: Uses Seatbelt (sandbox-exec) with SBPL policies
- Linux: Uses Landlock LSM for filesystem isolation (kernel 5.13+)
- Windows: Not yet supported (will fail with clear error)

Implementation based on OpenAI Codex CLI (MIT License):
https://github.com/openai/codex/tree/main/codex-rs

Usage:
    from wafer_core.sandbox import SandboxPolicy, execute_sandboxed

    policy = SandboxPolicy.workspace_write(working_dir)
    result = await execute_sandboxed(command, policy)
"""

from wafer_core.sandbox.executor import execute_sandboxed, is_sandbox_available
from wafer_core.sandbox.policy import SandboxMode, SandboxPolicy

__all__ = [
    "SandboxMode",
    "SandboxPolicy",
    "execute_sandboxed",
    "is_sandbox_available",
]
