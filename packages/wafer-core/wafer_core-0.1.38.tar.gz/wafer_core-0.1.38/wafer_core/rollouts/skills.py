"""Skill discovery and loading.

Skills are documentation files that agents can load on demand.
Format follows agentskills.io spec: SKILL.md with YAML frontmatter.

Discovery order:
1. ~/.wafer/skills/{name}/SKILL.md (user-installed)
2. Bundled skills (wafer-cli package)
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .paths import get_config_dir


@dataclass(frozen=True)
class SkillMetadata:
    """Lightweight skill metadata for system prompt injection."""

    name: str
    description: str
    path: Path  # Path to SKILL.md file


@dataclass(frozen=True)
class Skill:
    """Full skill with content."""

    name: str
    description: str
    content: str  # Full markdown content (without frontmatter)
    path: Path


def _parse_skill_file(path: Path) -> tuple[dict[str, str], str] | None:
    """Parse SKILL.md file into (frontmatter, content).

    Returns None if file doesn't exist or is malformed.
    """
    if not path.exists():
        return None

    try:
        text = path.read_text()
    except (OSError, PermissionError):
        return None

    # Parse YAML frontmatter (between --- markers)
    if not text.startswith("---"):
        return None

    # Find closing ---
    end_idx = text.find("---", 3)
    if end_idx == -1:
        return None

    frontmatter_text = text[3:end_idx].strip()
    content = text[end_idx + 3 :].strip()

    # Parse YAML (simple key: value format, no dependencies)
    frontmatter: dict[str, str] = {}
    for raw_line in frontmatter_text.split("\n"):
        stripped = raw_line.strip()
        if not stripped or ":" not in stripped:
            continue
        key, _, value = stripped.partition(":")
        frontmatter[key.strip()] = value.strip()

    # Validate required fields
    if "name" not in frontmatter or "description" not in frontmatter:
        return None

    return frontmatter, content


def _get_bundled_skills_dir() -> Path | None:
    """Get path to bundled skills in wafer-cli package."""
    # Try to find wafer-cli's skills directory
    try:
        import wafer

        wafer_cli_path = Path(wafer.__file__).parent
        skills_dir = wafer_cli_path / "skills"
        if skills_dir.exists():
            return skills_dir
    except ImportError:
        pass

    return None


def discover_skills() -> list[SkillMetadata]:
    """Discover all available skills.

    Returns list of SkillMetadata (name + description only).
    """
    skills: dict[str, SkillMetadata] = {}

    # 1. User-installed skills (~/.wafer/skills/)
    user_skills_dir = get_config_dir() / "skills"
    if user_skills_dir.exists():
        for skill_dir in user_skills_dir.iterdir():
            if not skill_dir.is_dir():
                continue
            skill_file = skill_dir / "SKILL.md"
            parsed = _parse_skill_file(skill_file)
            if parsed:
                frontmatter, _ = parsed
                skills[frontmatter["name"]] = SkillMetadata(
                    name=frontmatter["name"],
                    description=frontmatter["description"],
                    path=skill_file,
                )

    # 2. Bundled skills (wafer-cli package)
    bundled_dir = _get_bundled_skills_dir()
    if bundled_dir:
        for skill_dir in bundled_dir.iterdir():
            if not skill_dir.is_dir():
                continue
            skill_file = skill_dir / "SKILL.md"
            parsed = _parse_skill_file(skill_file)
            if parsed:
                frontmatter, _ = parsed
                # User skills take precedence
                if frontmatter["name"] not in skills:
                    skills[frontmatter["name"]] = SkillMetadata(
                        name=frontmatter["name"],
                        description=frontmatter["description"],
                        path=skill_file,
                    )

    return list(skills.values())


def load_skill(name: str) -> Skill | None:
    """Load a skill by name.

    Returns full Skill with content, or None if not found.
    """
    # Find the skill
    for metadata in discover_skills():
        if metadata.name == name:
            parsed = _parse_skill_file(metadata.path)
            if parsed:
                frontmatter, content = parsed
                return Skill(
                    name=frontmatter["name"],
                    description=frontmatter["description"],
                    content=content,
                    path=metadata.path,
                )
    return None


def format_skill_metadata_for_prompt(skills: list[SkillMetadata]) -> str:
    """Format skill metadata for system prompt injection.

    Returns a compact section listing available skills.
    """
    if not skills:
        return ""

    lines = ["## Available Skills", ""]
    lines.append(
        "You have access to the following skills. Use the `skill` tool to load full instructions when needed."
    )
    lines.append("")

    for skill in skills:
        lines.append(f"- **{skill.name}**: {skill.description}")

    return "\n".join(lines)
