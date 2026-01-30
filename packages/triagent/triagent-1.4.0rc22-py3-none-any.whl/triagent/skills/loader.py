"""Skill and persona loader for the triagent skills system.

This module handles:
- Parsing YAML frontmatter from markdown skill files
- Loading individual skills from .md files
- Loading persona definitions from YAML files
- Composing complete personas with all their skills and subagents
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from .encrypted_loader import (
    get_persona_content,
    get_skill_content,
    is_encrypted_mode,
    load_encrypted_skills,
)
from .models import (
    LoadedPersona,
    PersonaDefinition,
    SkillDefinition,
    SkillMetadata,
    SubagentConfig,
)

# Base directory for skills files
SKILLS_DIR = Path(__file__).parent


def parse_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    """Parse YAML frontmatter from markdown content.

    Args:
        content: Markdown content with optional YAML frontmatter

    Returns:
        Tuple of (frontmatter dict, remaining content)

    Example:
        ```
        ---
        name: my_skill
        description: A skill
        ---

        ## Skill Content
        Instructions here...
        ```
    """
    # Match YAML frontmatter between --- delimiters
    frontmatter_pattern = re.compile(
        r"^---\s*\n(.*?)\n---\s*\n?",
        re.DOTALL | re.MULTILINE,
    )

    match = frontmatter_pattern.match(content)
    if not match:
        return {}, content

    frontmatter_yaml = match.group(1)
    remaining_content = content[match.end():].strip()

    try:
        frontmatter = yaml.safe_load(frontmatter_yaml) or {}
    except yaml.YAMLError:
        frontmatter = {}

    return frontmatter, remaining_content


def load_skill(path: Path, content: str | None = None) -> SkillDefinition | None:
    """Load a single skill from a markdown file or content string.

    Args:
        path: Path to the skill .md file (used for name extraction if no frontmatter)
        content: Optional pre-loaded content (skips file read if provided)

    Returns:
        SkillDefinition or None if loading fails
    """
    if content is None:
        if not path.exists() or not path.suffix == ".md":
            return None
        try:
            content = path.read_text(encoding="utf-8")
        except Exception:
            return None

    try:
        frontmatter, skill_content = parse_frontmatter(content)

        if not frontmatter.get("name"):
            # Use filename as name if not specified
            frontmatter["name"] = path.stem

        metadata = SkillMetadata.from_dict(frontmatter)
        return SkillDefinition(
            metadata=metadata,
            content=skill_content,
            file_path=path,
        )
    except Exception:
        return None


def load_subagent(path: Path) -> SubagentConfig | None:
    """Load a subagent configuration from a Python or YAML file.

    Args:
        path: Path to the subagent config file

    Returns:
        SubagentConfig or None if loading fails
    """
    if not path.exists():
        return None

    try:
        if path.suffix == ".yaml" or path.suffix == ".yml":
            content = yaml.safe_load(path.read_text(encoding="utf-8"))
            return SubagentConfig.from_dict(content)
        elif path.suffix == ".py":
            # Import and get SUBAGENT_CONFIG dict
            # For safety, we parse the file rather than executing it
            content = path.read_text(encoding="utf-8")

            # Simple extraction of SUBAGENT_CONFIG dict
            # This is a simplified approach - in production, use AST parsing
            config_match = re.search(
                r'SUBAGENT_CONFIG\s*=\s*\{([^}]+(?:\{[^}]*\}[^}]*)*)\}',
                content,
                re.DOTALL,
            )
            if config_match:
                # Parse the dict-like string (simplified)
                config_str = "{" + config_match.group(1) + "}"
                # Convert to valid Python dict
                # This is a simplified approach for demonstration
                try:
                    # Use eval in a restricted context
                    config = eval(config_str, {"__builtins__": {}}, {})  # noqa: S307
                    return SubagentConfig.from_dict(config)
                except Exception:
                    pass
        return None
    except Exception:
        return None


def create_subagent_from_skill(skill: SkillDefinition, subagent_name: str) -> SubagentConfig:
    """Create SubagentConfig from skill content.

    The skill's markdown content becomes the subagent's prompt.
    The skill's description and tools are inherited. This allows subagent
    prompts to be generated dynamically from the skill files without
    requiring separate YAML configuration files.

    Args:
        skill: The skill definition containing metadata and content
        subagent_name: The subagent name from skill.metadata.subagents

    Returns:
        SubagentConfig generated from skill content
    """
    # Build the subagent prompt from skill content
    prompt = f"""You are a {skill.metadata.display_name} specialist.

{skill.content}

When providing feedback:
- Organize by priority (Critical, High, Medium, Low)
- Include specific code examples showing fixes
- Reference the guidelines above"""

    return SubagentConfig(
        name=subagent_name,
        description=skill.metadata.description,
        prompt=prompt,
        tools=skill.metadata.tools,
        model="sonnet",
    )


def load_persona_definition(team: str, persona_name: str) -> PersonaDefinition | None:
    """Load a persona definition from YAML file or encrypted bundle.

    Args:
        team: Team identifier (e.g., "omnia-data")
        persona_name: Persona name ("developer" or "support")

    Returns:
        PersonaDefinition or None if not found
    """
    # Check encrypted mode first
    if is_encrypted_mode():
        try:
            rel_path = f"{team}/_persona_{persona_name}.yaml"
            content = get_persona_content(rel_path)
            if not content:
                return None
            data = yaml.safe_load(content)
            data["name"] = persona_name
            return PersonaDefinition.from_dict(data, team)
        except Exception:
            # Decryption failed or invalid content - fall back to file-based
            pass

    # Fall back to file-based loading
    persona_file = SKILLS_DIR / team / f"_persona_{persona_name}.yaml"

    if not persona_file.exists():
        return None

    try:
        data = yaml.safe_load(persona_file.read_text(encoding="utf-8"))
        data["name"] = persona_name  # Ensure name is set
        return PersonaDefinition.from_dict(data, team)
    except Exception:
        return None


def get_available_personas(team: str) -> list[PersonaDefinition]:
    """Get all available personas for a team.

    Args:
        team: Team identifier

    Returns:
        List of PersonaDefinition objects
    """
    # Check encrypted mode first
    if is_encrypted_mode():
        try:
            skills_data = load_encrypted_skills()
            personas = []
            for path in skills_data.get("personas", {}):
                # Match paths like "omnia-data/_persona_developer.yaml"
                if path.startswith(f"{team}/") and "_persona_" in path:
                    # Extract persona name from path
                    filename = path.split("/")[-1]  # "_persona_developer.yaml"
                    persona_name = filename.replace("_persona_", "").replace(".yaml", "")
                    persona = load_persona_definition(team, persona_name)
                    if persona:
                        personas.append(persona)
            return personas
        except Exception:
            return []

    # Fall back to file-based loading
    team_dir = SKILLS_DIR / team
    if not team_dir.exists():
        return []

    personas = []
    for persona_file in team_dir.glob("_persona_*.yaml"):
        persona_name = persona_file.stem.replace("_persona_", "")
        persona = load_persona_definition(team, persona_name)
        if persona:
            personas.append(persona)

    return personas


def _load_skill_encrypted(skill_name: str, team: str, persona_name: str | None = None) -> SkillDefinition | None:
    """Load a skill from encrypted bundle.

    Args:
        skill_name: Name of the skill (without .md extension)
        team: Team identifier
        persona_name: Optional persona name for persona-specific skills

    Returns:
        SkillDefinition or None if not found
    """
    try:
        # Build search paths (team core first, then global core)
        search_paths = []
        if persona_name:
            search_paths.append(f"{team}/{persona_name}/{skill_name}.md")
        search_paths.append(f"{team}/core/{skill_name}.md")
        search_paths.append(f"core/{skill_name}.md")

        for rel_path in search_paths:
            content = get_skill_content(rel_path)
            if content:
                # Create a fake path for name extraction
                fake_path = Path(rel_path)
                return load_skill(fake_path, content=content)
    except Exception:
        # Decryption failed - return None
        pass

    return None


def load_persona(team: str, persona_name: str) -> LoadedPersona | None:
    """Load a complete persona with all skills and subagents.

    Args:
        team: Team identifier (e.g., "omnia-data")
        persona_name: Persona name ("developer" or "support")

    Returns:
        LoadedPersona with all resolved skills and subagents
    """
    # Load persona definition
    definition = load_persona_definition(team, persona_name)
    if not definition:
        return None

    skills: dict[str, SkillDefinition] = {}
    subagents: dict[str, SubagentConfig] = {}

    encrypted_mode = is_encrypted_mode()

    # Load core skills
    for skill_name in definition.core_skills:
        if encrypted_mode:
            skill = _load_skill_encrypted(skill_name, team)
        else:
            # File-based loading (team-specific first, then global fallback)
            team_core_dir = SKILLS_DIR / team / "core"
            global_core_dir = SKILLS_DIR / "core"
            skill_path = team_core_dir / f"{skill_name}.md"
            if not skill_path.exists():
                skill_path = global_core_dir / f"{skill_name}.md"
            skill = load_skill(skill_path)
        if skill:
            skills[skill_name] = skill

    # Load persona-specific skills
    # Use skill_directory if defined, otherwise use persona_name
    skill_dir_name = definition.skill_directory or persona_name
    for skill_name in definition.skills:
        if encrypted_mode:
            skill = _load_skill_encrypted(skill_name, team, skill_dir_name)
        else:
            persona_dir = SKILLS_DIR / team / skill_dir_name
            skill_path = persona_dir / f"{skill_name}.md"
            skill = load_skill(skill_path)
        if skill:
            skills[skill_name] = skill

    # Load subagents from core (only file-based, subagents not encrypted)
    global_core_dir = SKILLS_DIR / "core"
    core_subagents_dir = global_core_dir / "_subagents"
    if core_subagents_dir.exists():
        for subagent_file in core_subagents_dir.glob("*.yaml"):
            subagent = load_subagent(subagent_file)
            if subagent:
                subagents[subagent.name] = subagent
        for subagent_file in core_subagents_dir.glob("*.py"):
            subagent = load_subagent(subagent_file)
            if subagent:
                subagents[subagent.name] = subagent

    # Load subagents from team
    team_subagents_dir = SKILLS_DIR / team / "_subagents"
    if team_subagents_dir.exists():
        for subagent_file in team_subagents_dir.glob("*.yaml"):
            subagent = load_subagent(subagent_file)
            if subagent:
                subagents[subagent.name] = subagent
        for subagent_file in team_subagents_dir.glob("*.py"):
            subagent = load_subagent(subagent_file)
            if subagent:
                subagents[subagent.name] = subagent

    # Generate subagents dynamically from skills that reference them
    # This allows skill markdown content to become the subagent's prompt
    # without requiring separate YAML configuration files
    for _skill_name, skill in skills.items():
        for subagent_name in skill.metadata.subagents:
            if subagent_name not in subagents:
                subagents[subagent_name] = create_subagent_from_skill(skill, subagent_name)

    return LoadedPersona(
        definition=definition,
        skills=skills,
        subagents=subagents,
    )




def get_persona_full_context(team: str, persona_name: str) -> dict[str, Any] | None:
    """Get complete persona context including full skill content.

    This is used by switch_persona tool to inject new persona context
    into the current conversation without restarting.

    Args:
        team: Team identifier (e.g., "omnia-data")
        persona_name: Persona name (e.g., "developer", "support")

    Returns:
        dict with:
        - display_name: Human-readable persona name
        - description: Persona description
        - capabilities: List of skill summaries
        - skill_content: Full markdown content of all persona skills
        - on_demand_skills: List of on-demand skill names
        - system_prompt_additions: Persona-specific system prompt additions
        Or None if persona not found
    """
    persona = load_persona(team, persona_name)
    if not persona:
        return None

    # Build capabilities list
    capabilities = []
    for skill_name in persona.definition.skills:
        if skill_name in persona.skills:
            skill = persona.skills[skill_name]
            capabilities.append({
                "name": skill.metadata.display_name,
                "description": skill.metadata.description,
            })

    # Also include core skills in capabilities
    for skill_name in persona.definition.core_skills:
        if skill_name in persona.skills:
            skill = persona.skills[skill_name]
            capabilities.append({
                "name": skill.metadata.display_name,
                "description": skill.metadata.description,
            })

    # Build full skill content (like system prompt does)
    skill_content_parts = []
    for _skill_name, skill in persona.skills.items():
        if skill.content:
            skill_content_parts.append(
                f"## {skill.metadata.display_name}\n\n{skill.content}"
            )

    return {
        "display_name": persona.definition.display_name,
        "description": persona.definition.description,
        "capabilities": capabilities,
        "skill_content": "\n\n---\n\n".join(skill_content_parts),
        "on_demand_skills": persona.definition.on_demand_skills,
        "system_prompt_additions": persona.definition.system_prompt_additions or "",
    }


def load_skill_by_name(skill_name: str, team: str = "omnia-data") -> str | None:
    """Load a skill's content by name for on-demand retrieval.

    Searches for the skill in the following order:
    1. Team's developer persona directory (e.g., omnia-data/developer/)
    2. Team's developer sub-skill directories (code-review/, pipeline/)
    3. Team's support persona directory (e.g., omnia-data/support/)
    4. Team's po-bsa persona directory (e.g., omnia-data/po-bsa/)
    5. Team's finops directory (e.g., omnia-data/finops/)
    6. Team's core directory (e.g., omnia-data/core/)
    7. Global core directory (core/)
    8. Global reference directory (reference/)

    Args:
        skill_name: Name of the skill (without .md extension)
        team: Team identifier (default: "omnia-data")

    Returns:
        Skill content as string, or None if not found
    """
    # Extended search paths in order of priority
    search_rel_paths = [
        f"{team}/developer/{skill_name}.md",
        f"{team}/developer/code-review/{skill_name}.md",
        f"{team}/developer/pipeline/{skill_name}.md",
        f"{team}/support/{skill_name}.md",
        f"{team}/po-bsa/{skill_name}.md",
        f"{team}/finops/{skill_name}.md",
        f"{team}/core/{skill_name}.md",
        f"core/{skill_name}.md",
        f"reference/{skill_name}.md",
    ]

    # Check encrypted mode first
    if is_encrypted_mode():
        try:
            for rel_path in search_rel_paths:
                content = get_skill_content(rel_path)
                if content:
                    fake_path = Path(rel_path)
                    skill = load_skill(fake_path, content=content)
                    if skill:
                        # Return the full skill content including display name header
                        if skill.metadata.display_name:
                            header = "# " + skill.metadata.display_name + chr(10) + chr(10)
                        else:
                            header = ""
                        return header + skill.content
            return None
        except Exception:
            # Decryption failed - fall back to file-based loading
            pass

    # Fall back to file-based loading with extended paths
    search_paths = [
        SKILLS_DIR / team / "developer" / f"{skill_name}.md",
        SKILLS_DIR / team / "developer" / "code-review" / f"{skill_name}.md",
        SKILLS_DIR / team / "developer" / "pipeline" / f"{skill_name}.md",
        SKILLS_DIR / team / "support" / f"{skill_name}.md",
        SKILLS_DIR / team / "po-bsa" / f"{skill_name}.md",
        SKILLS_DIR / team / "finops" / f"{skill_name}.md",
        SKILLS_DIR / team / "core" / f"{skill_name}.md",
        SKILLS_DIR / "core" / f"{skill_name}.md",
        SKILLS_DIR / "reference" / f"{skill_name}.md",
    ]

    for path in search_paths:
        if path.exists():
            skill = load_skill(path)
            if skill:
                # Return the full skill content including display name header
                if skill.metadata.display_name:
                    header = "# " + skill.metadata.display_name + chr(10) + chr(10)
                else:
                    header = ""
                return header + skill.content

    return None


def discover_personas(team: str) -> list[dict[str, str]]:
    """Discover all personas for a team from _persona_*.yaml files.

    Returns persona metadata sorted alphabetically by display_name.

    Args:
        team: Team identifier (e.g., "omnia-data")

    Returns:
        List of dicts with persona metadata:
        [{"name": "developer", "display_name": "Developer", "description": "...", "file": "_persona_developer.yaml"}]
    """
    personas: list[dict[str, str]] = []

    # Check encrypted mode first
    if is_encrypted_mode():
        try:
            skills_data = load_encrypted_skills()
            for path in skills_data.get("personas", {}):
                if path.startswith(f"{team}/") and "_persona_" in path:
                    filename = path.split("/")[-1]
                    persona_name = filename.replace("_persona_", "").replace(".yaml", "")
                    content = get_persona_content(path)
                    if content:
                        data = yaml.safe_load(content)
                        personas.append({
                            "name": persona_name,
                            "display_name": data.get("display_name", persona_name.title()),
                            "description": data.get("description", ""),
                            "file": filename,
                        })
        except Exception:
            pass
        return sorted(personas, key=lambda p: p["display_name"])

    # Fall back to file-based loading
    team_dir = SKILLS_DIR / team
    if not team_dir.exists():
        return []

    for persona_file in team_dir.glob("_persona_*.yaml"):
        try:
            data = yaml.safe_load(persona_file.read_text(encoding="utf-8"))
            persona_name = persona_file.stem.replace("_persona_", "")
            personas.append({
                "name": persona_name,
                "display_name": data.get("display_name", persona_name.title()),
                "description": data.get("description", ""),
                "file": persona_file.name,
            })
        except Exception:
            continue

    return sorted(personas, key=lambda p: p["display_name"])

class SkillLoader:
    """Convenience class for loading skills and personas."""

    def __init__(self, skills_dir: Path | None = None) -> None:
        """Initialize skill loader.

        Args:
            skills_dir: Custom skills directory (defaults to package dir)
        """
        self.skills_dir = skills_dir or SKILLS_DIR

    def get_available_teams(self) -> list[str]:
        """Get list of teams with skills defined."""
        # Check encrypted mode first
        if is_encrypted_mode():
            try:
                skills_data = load_encrypted_skills()
                teams_set: set[str] = set()
                # Extract team names from persona paths like "omnia-data/_persona_developer.yaml"
                for path in skills_data.get("personas", {}):
                    if "/" in path and "_persona_" in path:
                        team = path.split("/")[0]
                        if team != "core":
                            teams_set.add(team)
                return sorted(teams_set)
            except Exception:
                return []

        # Fall back to file-based loading
        teams_list: list[str] = []
        for item in self.skills_dir.iterdir():
            if item.is_dir() and not item.name.startswith("_") and item.name != "core":
                teams_list.append(item.name)
        return sorted(teams_list)

    def get_personas_for_team(self, team: str) -> list[PersonaDefinition]:
        """Get available personas for a team."""
        return get_available_personas(team)

    def load_persona(self, team: str, persona_name: str) -> LoadedPersona | None:
        """Load a complete persona."""
        return load_persona(team, persona_name)

    def load_skill(self, path: Path) -> SkillDefinition | None:
        """Load a single skill from file."""
        return load_skill(path)
