"""
Oracle environment - adds the oracle tool for consulting GPT-5.2.

Usage:
    from .compose import compose
    from .localfs import LocalFilesystemEnvironment
    from .oracle import OracleEnvironment

    env = compose(
        LocalFilesystemEnvironment(working_dir=Path.cwd()),
        OracleEnvironment(),
    )
    # Now the agent can call the oracle tool during execution
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import trio

from ..dtypes import (
    AgentState,
    Endpoint,
    Message,
    RunConfig,
    Tool,
    ToolCall,
    ToolFunctionParameter,
    ToolResult,
)
from ..tools.oracle import (
    DEFAULT_ORACLE_MODEL,
    DEFAULT_ORACLE_PROVIDER,
    DEFAULT_REASONING_EFFORT,
    FileRange,
    oracle_impl,
)


def _build_oracle_tool() -> Tool:
    """Build the oracle tool definition."""
    from ..dtypes import ToolFunction

    return Tool(
        function=ToolFunction(
            name="oracle",
            description=(
                "Consult the Oracle (GPT-5.2) for expert guidance on planning, code review, "
                "debugging, and architecture analysis. Use when you need deeper analysis or "
                "a second opinion on complex decisions. The Oracle uses extended reasoning "
                "and provides structured recommendations."
            ),
            parameters=ToolFunctionParameter(
                properties={
                    "task": {
                        "type": "string",
                        "description": (
                            "The task or question for the Oracle. Be specific about what "
                            "kind of guidance you need (review, planning, debugging, etc.)."
                        ),
                    },
                    "context": {
                        "type": "string",
                        "description": (
                            "Optional background context about the situation, what you've "
                            "tried, or constraints that would help provide better guidance."
                        ),
                    },
                    "files": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "path": {"type": "string", "description": "File path"},
                                "start": {
                                    "type": "integer",
                                    "description": "Start line (1-indexed, optional)",
                                },
                                "end": {
                                    "type": "integer",
                                    "description": "End line (optional)",
                                },
                            },
                            "required": ["path"],
                        },
                        "description": (
                            "Optional list of file ranges to examine. Prefer specific "
                            "line ranges over full files to focus the analysis."
                        ),
                    },
                },
            ),
            required=["task"],
        )
    )


@dataclass
class OracleEnvironment:
    """Environment that provides the oracle tool.

    The oracle consults GPT-5.2 with high reasoning effort for expert guidance.
    It's useful for:
    - Code review and architecture feedback
    - Planning complex implementations
    - Debugging issues across multiple files
    - Getting a second opinion on decisions

    Args:
        working_dir: Base directory for resolving relative file paths
        endpoint: Custom endpoint for the oracle (defaults to GPT-5.2)
    """

    working_dir: Path = field(default_factory=Path.cwd)
    endpoint: Endpoint | None = None
    _tool: Tool = field(default_factory=_build_oracle_tool, repr=False)

    def get_name(self) -> str:
        return "oracle"

    def get_tools(self) -> list[Tool]:
        return [self._tool]

    def requires_confirmation(self, tool_call: ToolCall) -> bool:
        # Oracle doesn't need confirmation - it's read-only consultation
        return False

    async def on_assistant_message(self, message: Message, state: AgentState) -> AgentState:
        return state

    def _get_endpoint(self) -> Endpoint:
        """Get the oracle endpoint, using default if not configured."""
        if self.endpoint is not None:
            return self.endpoint

        import os

        return Endpoint(
            provider=DEFAULT_ORACLE_PROVIDER,
            model=DEFAULT_ORACLE_MODEL,
            api_base="https://api.openai.com/v1",
            api_key=os.environ.get("OPENAI_API_KEY", ""),
            reasoning_effort=DEFAULT_REASONING_EFFORT,
            max_completion_tokens=16384,
        )

    async def exec_tool(
        self,
        tool_call: ToolCall,
        current_state: AgentState,
        run_config: RunConfig,
        cancel_scope: trio.CancelScope | None = None,
    ) -> ToolResult:
        """Execute the oracle tool."""
        if tool_call.name != "oracle":
            return ToolResult(
                tool_call_id=tool_call.id,
                is_error=True,
                content="",
                error=f"Unknown tool: {tool_call.name}",
            )

        args = dict(tool_call.args)
        task = args.get("task", "")
        context = args.get("context")
        files_raw = args.get("files", [])

        # Parse file ranges
        files: list[FileRange] = []
        for f in files_raw or []:
            if isinstance(f, dict):
                files.append(
                    FileRange(
                        path=f.get("path", ""),
                        start=f.get("start"),
                        end=f.get("end"),
                    )
                )

        # File reader that resolves relative paths
        async def read_file(path: str) -> str | None:
            try:
                p = Path(path)
                if not p.is_absolute():
                    p = self.working_dir / p
                return p.read_text()
            except Exception:
                return None

        endpoint = self._get_endpoint()

        # Check for API key
        if not endpoint.api_key:
            return ToolResult(
                tool_call_id=tool_call.id,
                is_error=True,
                content="",
                error="OPENAI_API_KEY not set. Cannot consult the Oracle.",
            )

        try:
            result = await oracle_impl(
                task=task,
                context=context,
                files=files if files else None,
                endpoint=endpoint,
                read_fn=read_file,
                max_turns=1,
            )
            return ToolResult(
                tool_call_id=tool_call.id,
                content=result,
            )
        except Exception as e:
            return ToolResult(
                tool_call_id=tool_call.id,
                is_error=True,
                content="",
                error=f"Oracle error: {e}",
            )

    async def serialize(self) -> dict[str, Any]:
        return {
            "env_kind": "oracle",
            "working_dir": str(self.working_dir),
        }

    @staticmethod
    async def deserialize(data: dict[str, Any]) -> "OracleEnvironment":
        return OracleEnvironment(
            working_dir=Path(data.get("working_dir", ".")),
        )
