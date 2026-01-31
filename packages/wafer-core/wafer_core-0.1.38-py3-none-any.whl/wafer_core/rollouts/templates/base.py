"""Base template configuration for rollouts agents.

Templates define constrained agents for specific tasks:
- Specific toolset (subset of coding env tools)
- Bash allowlist (prefix-matching)
- Model and token limits
- System prompt with variable interpolation

All runtime config should be explicit in the template - no hidden defaults.
"""

from __future__ import annotations

import string
from dataclasses import dataclass, field
from typing import Any

# Safe read-only commands with no side effects.
# Templates can extend this with task-specific commands.
# NOTE: The allowlist uses prefix matching, so "git branch" also allows
# "git branch -D" which is destructive. Only include truly read-only commands.
SAFE_BASH_COMMANDS: list[str] = [
    # File inspection
    "ls",
    "cat",
    "head",
    "tail",
    "less",
    "more",
    "file",
    "stat",
    "wc",
    # Search
    "find",
    "grep",
    "rg",
    "fd",
    # Navigation
    "pwd",
    "tree",
    "which",
    "whereis",
    # Comparison/processing
    "diff",
    "sort",
    "uniq",
    # Disk info
    "du",
    "df",
    # Git read-only (only commands with no destructive subcommands)
    "git status",
    "git log",
    "git diff",
    "git show",
    # Data processing
    "jq",
]

# Dangerous commands that should always be denied.
# These can cause irreversible damage or security issues.
DANGEROUS_BASH_COMMANDS: list[str] = [
    # Destructive file operations
    "rm ",
    "rm\t",
    "rmdir",
    "shred",
    "dd ",
    "dd\t",
    "truncate",
    # Moving/overwriting without backup
    "mv ",
    "mv\t",
    # Privilege escalation
    "sudo",
    "su ",
    "su\t",
    "doas",
    # System control
    "reboot",
    "shutdown",
    "poweroff",
    "halt",
    "init ",
    "init\t",
    # Service/process control
    "systemctl start",
    "systemctl stop",
    "systemctl restart",
    "systemctl enable",
    "systemctl disable",
    "service ",
    "kill ",
    "kill\t",
    "killall",
    "pkill",
    # Package managers (system-wide changes)
    "apt install",
    "apt remove",
    "apt purge",
    "apt-get install",
    "apt-get remove",
    "apt-get purge",
    "yum install",
    "yum remove",
    "dnf install",
    "dnf remove",
    "pacman -S",
    "pacman -R",
    "brew install",
    "brew uninstall",
    "pip install",
    "pip uninstall",
    "npm install -g",
    "npm uninstall -g",
    # Disk/filesystem operations
    "mkfs",
    "fdisk",
    "parted",
    "mount ",
    "mount\t",
    "umount",
    # Network danger
    "iptables",
    "ufw ",
    "ufw\t",
    # Chmod/chown (can break permissions)
    "chmod ",
    "chmod\t",
    "chown ",
    "chown\t",
    "chgrp",
]


# Safe read-only commands with no side effects.
# Templates can extend this with task-specific commands.
SAFE_BASH_COMMANDS: list[str] = [
    # File inspection
    "ls",
    "cat",
    "head",
    "tail",
    "less",
    "more",
    "file",
    "stat",
    "wc",
    # Search
    "find",
    "grep",
    "rg",
    "fd",
    # Navigation
    "pwd",
    "tree",
    "which",
    "whereis",
    # Comparison/processing
    "diff",
    "sort",
    "uniq",
    # Disk info
    "du",
    "df",
    # Git read-only
    "git status",
    "git log",
    "git diff",
    "git show",
    "git branch",
    "git remote",
    # Data processing
    "jq",
    "python -c",
]


@dataclass(frozen=True)
class TemplateConfig:
    """Configuration for a task-specific agent template.

    Templates are constrained agents designed for headless execution.
    All runtime config is explicit here - no hidden defaults in CLI code.

    Example:
        >>> template = TemplateConfig(
        ...     name="ask-docs",
        ...     system_prompt="You analyze documentation to answer questions...",
        ...     tools=["read", "glob", "grep", "bash"],
        ...     bash_allowlist=["wafer ask-docs", "jq", "python -c"],
        ...     single_turn=False,
        ...     max_tokens=8192,
        ...     thinking=False,
        ... )
    """

    # Identity
    name: str
    description: str = ""

    # System prompt (supports $variable interpolation)
    system_prompt: str = ""

    # Tools available to the agent
    tools: list[str] = field(default_factory=lambda: ["read", "glob", "grep", "bash"])

    # Bash constraints (prefix matching, None = all allowed)
    bash_allowlist: list[str] | None = None

    # Model config
    model: str = "anthropic/claude-sonnet-4-5-20250929"
    max_tokens: int = 8192

    # Thinking config (extended thinking for complex reasoning)
    thinking: bool = False
    thinking_budget: int = 10000

    # Execution mode
    single_turn: bool = False  # True = answer once and exit, False = multi-turn REPL

    # Template variables and their defaults
    # Example: {"corpus": "./docs/", "format": "markdown"}
    defaults: dict[str, str] = field(default_factory=dict)

    # Skill discovery - if True, discovers skills and adds skill tool
    include_skills: bool = False

    def interpolate_prompt(self, args: dict[str, str] | None = None) -> str:
        """Interpolate template variables into the system prompt.

        Args:
            args: Variable values from --args. Example: {"corpus": "./my-docs/"}

        Returns:
            System prompt with $variables replaced.

        Raises:
            ValueError: If required variables are missing.
        """
        params = dict(self.defaults)
        if args:
            params.update(args)

        # Find all variables in the template
        template = string.Template(self.system_prompt)
        required_vars = self._extract_vars(template)

        # Check for missing required variables
        missing = [v for v in required_vars if v not in params]
        if missing:
            raise ValueError(
                f"Template '{self.name}' requires variables: {', '.join(missing)}. "
                f"Provide them with --args {missing[0]}=value"
            )

        return template.safe_substitute(**params)

    def get_variables(self) -> list[str]:
        """Get list of variables used in the system prompt."""
        template = string.Template(self.system_prompt)
        return self._extract_vars(template)

    @staticmethod
    def _extract_vars(template: string.Template) -> list[str]:
        """Extract variable names from a string.Template."""
        return [
            match.group("named") or match.group("braced")
            for match in template.pattern.finditer(template.template)
            if match.group("named") or match.group("braced")
        ]

    def to_cli_args(self) -> dict[str, Any]:
        """Convert to CLI argument dict for consumption by runner."""
        return {
            "tools": self.tools,
            "bash_allowlist": self.bash_allowlist,
            "model": self.model,
            "max_tokens": self.max_tokens,
            "thinking": self.thinking,
            "thinking_budget": self.thinking_budget,
            "single_turn": self.single_turn,
        }
