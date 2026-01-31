"""Coding environment with minimal toolset for code editing tasks.

Tools: read, write, edit, glob, grep, bash

# TODO(wafer-tool): Consider adding a 'wafer' tool that provides access to
# wafer subcommands (ask-docs, ncu-analyze, remote-run, etc.) while keeping
# them separate from general bash access. See git history for implementation.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import trio

from wafer_core.rollouts.dtypes import (
    AgentState,
    Message,
    RunConfig,
    Tool,
    ToolCall,
    ToolResult,
)
from wafer_core.sandbox import SandboxMode, SandboxPolicy
from wafer_core.sandbox.executor import (
    get_sandbox_unavailable_reason,
    is_sandbox_available,
)
from wafer_core.tools import (
    BASH_TOOL,
    EDIT_TOOL,
    GLOB_TOOL,
    GREP_TOOL,
    READ_TOOL,
    SKILL_TOOL,
    WRITE_TOOL,
    ApprovalCallback,
    exec_bash,
    exec_edit,
    exec_glob,
    exec_grep,
    exec_read,
    exec_skill,
    exec_write,
)


def _shorten_path(path: str) -> str:
    """Convert absolute path to tilde notation if in home directory."""
    home = os.path.expanduser("~")
    if path.startswith(home):
        return "~" + path[len(home) :]
    return path


# Tool definitions are imported from wafer_core.tools
ALL_TOOLS = {
    "read": READ_TOOL,
    "write": WRITE_TOOL,
    "edit": EDIT_TOOL,
    "glob": GLOB_TOOL,
    "grep": GREP_TOOL,
    "bash": BASH_TOOL,
    "skill": SKILL_TOOL,
    # TODO(wafer-tool): "wafer": WAFER_TOOL,
}


@dataclass
class CodingEnvironment:
    """Local filesystem environment with read, write, edit, glob, grep, bash tools.

    Args:
        working_dir: Working directory for file operations and commands.
        enabled_tools: List of tool names to enable. If None, all tools enabled.
            Valid tools: read, write, edit, glob, grep, bash.
        bash_allowlist: List of allowed bash command prefixes. Commands matching
            these prefixes execute without prompting.
        bash_denylist: List of denied bash command prefixes. Commands matching
            these prefixes are always blocked.
        bash_approval_callback: Optional callback for "ask" tier approval.
            If None, commands not in allowlist are denied (headless mode).
        sandbox_mode: Controls OS-level sandboxing for bash commands.
            - ENABLED (default): Sandbox required. Fails if unavailable.
            - DISABLED: No sandboxing. User accepts liability.
        extra_writable_paths: Additional paths the sandbox should allow writes to.
        allow_network: Whether to allow network access in the sandbox.
    """

    working_dir: Path = field(default_factory=Path.cwd)
    enabled_tools: list[str] | None = None
    bash_allowlist: list[str] | None = None
    bash_denylist: list[str] | None = None
    bash_approval_callback: ApprovalCallback | None = None
    sandbox_mode: SandboxMode = SandboxMode.ENABLED
    extra_writable_paths: list[Path] | None = None
    allow_network: bool = False

    # Computed at __post_init__
    _sandbox_policy: SandboxPolicy | None = field(init=False, repr=False, default=None)

    def __post_init__(self) -> None:
        """Validate enabled_tools and setup sandbox at construction time."""
        if self.enabled_tools is not None:
            valid_tools = set(ALL_TOOLS.keys())
            unknown = set(self.enabled_tools) - valid_tools
            if unknown:
                raise ValueError(
                    f"Unknown tools: {sorted(unknown)}. Available: {sorted(valid_tools)}"
                )

        # Setup sandbox policy if enabled
        if self.sandbox_mode == SandboxMode.ENABLED:
            if not is_sandbox_available():
                reason = get_sandbox_unavailable_reason()
                raise RuntimeError(
                    f"Sandbox mode is ENABLED but sandboxing is not available: {reason}\n"
                    "Use sandbox_mode=SandboxMode.DISABLED to run without sandboxing "
                    "(you accept liability for any damage caused by the agent)."
                )

            object.__setattr__(
                self,
                "_sandbox_policy",
                SandboxPolicy.workspace_write(
                    working_dir=self.working_dir,
                    extra_writable=self.extra_writable_paths,
                    network_access=self.allow_network,
                ),
            )

    def get_name(self) -> str:
        """Return environment name identifier."""
        return "coding"

    async def serialize(self) -> dict:
        return {
            "working_dir": str(self.working_dir),
            "enabled_tools": self.enabled_tools,
            "bash_allowlist": self.bash_allowlist,
            "bash_denylist": self.bash_denylist,
            "sandbox_mode": self.sandbox_mode.value,
            "extra_writable_paths": [str(p) for p in self.extra_writable_paths]
            if self.extra_writable_paths
            else None,
            "allow_network": self.allow_network,
            # Note: approval_callback is not serializable
        }

    @staticmethod
    async def deserialize(data: dict) -> CodingEnvironment:
        extra_paths = data.get("extra_writable_paths")
        return CodingEnvironment(
            working_dir=Path(data["working_dir"]),
            enabled_tools=data.get("enabled_tools"),
            bash_allowlist=data.get("bash_allowlist"),
            bash_denylist=data.get("bash_denylist"),
            sandbox_mode=SandboxMode(data.get("sandbox_mode", "enabled")),
            extra_writable_paths=[Path(p) for p in extra_paths] if extra_paths else None,
            allow_network=data.get("allow_network", False),
        )

    def requires_confirmation(self, tool_call: ToolCall) -> bool:
        """Only bash commands require confirmation by default."""
        return tool_call.name == "bash"

    def get_tools(self) -> list[Tool]:
        """Return enabled tools."""
        if self.enabled_tools is None:
            return list(ALL_TOOLS.values())

        return [ALL_TOOLS[name] for name in self.enabled_tools if name in ALL_TOOLS]

    async def on_assistant_message(self, message: Message, state: AgentState) -> AgentState:
        """No feedback needed for coding environment."""
        return state

    async def exec_tool(
        self,
        tool_call: ToolCall,
        current_state: AgentState,
        run_config: RunConfig,
        cancel_scope: trio.CancelScope | None = None,
    ) -> ToolResult:
        """Execute tool call."""
        # Check if tool is enabled
        if self.enabled_tools is not None and tool_call.name not in self.enabled_tools:
            return ToolResult(
                tool_call_id=tool_call.id,
                is_error=True,
                content="",
                error=f"Tool '{tool_call.name}' is not enabled. Enabled tools: {', '.join(self.enabled_tools)}",
            )

        # Dispatch to pure function handlers
        # All file tools receive working_dir for relative path resolution
        handlers = {
            "read": lambda tc: exec_read(tc, self.working_dir),
            "write": lambda tc: exec_write(tc, self.working_dir),
            "edit": lambda tc: exec_edit(tc, self.working_dir),
            "glob": lambda tc: exec_glob(tc, self.working_dir),
            "grep": lambda tc: exec_grep(tc, self.working_dir),
            "bash": lambda tc: exec_bash(
                tc,
                self.working_dir,
                cancel_scope,
                self.bash_allowlist,
                self.bash_denylist,
                self.bash_approval_callback,
                self._sandbox_policy,
            ),
            "skill": lambda tc: exec_skill(tc),
            # TODO(wafer-tool): "wafer": lambda tc: exec_wafer(
            #     tc, self.working_dir, self.enabled_tools, self.allow_spawn, cancel_scope
            # ),
        }

        handler = handlers.get(tool_call.name)
        if handler is None:
            return ToolResult(
                tool_call_id=tool_call.id,
                is_error=True,
                content="",
                error=f"Unknown tool: {tool_call.name}",
            )

        try:
            return await handler(tool_call)
        except Exception as e:
            return ToolResult(tool_call_id=tool_call.id, is_error=True, content="", error=str(e))
