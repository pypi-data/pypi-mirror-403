"""Skill tool.

Loads skill content on demand from ~/.wafer/skills/ or bundled locations.
"""

from wafer_core.rollouts.dtypes import (
    Tool,
    ToolCall,
    ToolFunction,
    ToolFunctionParameter,
    ToolResult,
)

# ── Tool Definition ──────────────────────────────────────────────────────────

SKILL_TOOL = Tool(
    type="function",
    function=ToolFunction(
        name="skill",
        description="Load a skill's full instructions. Skills provide domain-specific knowledge and workflows. Use this when you need detailed guidance for a task mentioned in your available skills.",
        parameters=ToolFunctionParameter(
            type="object",
            properties={
                "name": {
                    "type": "string",
                    "description": "Name of the skill to load (e.g., 'wafer-guide')",
                },
            },
        ),
        required=["name"],
    ),
)


# ── Pure Function Executor ───────────────────────────────────────────────────


async def exec_skill(tool_call: ToolCall) -> ToolResult:
    """Load a skill's full instructions.

    Args:
        tool_call: The tool call with skill name.
    """
    from wafer_core.rollouts.skills import discover_skills, load_skill

    skill_name = tool_call.args["name"]
    skill = load_skill(skill_name)

    if skill is None:
        available = discover_skills()
        available_names = [s.name for s in available]
        return ToolResult(
            tool_call_id=tool_call.id,
            is_error=True,
            content="",
            error=f"Skill not found: {skill_name}. Available skills: {', '.join(available_names) or 'none'}",
        )

    header = f"# Skill: {skill.name}\n\n"
    return ToolResult(
        tool_call_id=tool_call.id,
        is_error=False,
        content=header + skill.content,
    )
