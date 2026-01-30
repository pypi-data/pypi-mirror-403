"""Skills and personas system for triagent.

This module provides the skills architecture that enables:
- Team-specific personas (Developer, Support, Product Owner, Business Analyst)
- Composed skill sets with YAML frontmatter metadata
- Subagent configuration for automatic routing
- Language detection for code review tasks
- Dynamic skill loading based on triggers and user queries
- HTML template rendering for reports

Usage:
    from triagent.skills import SkillLoader, load_persona, discover_personas

    # Load a persona
    loader = SkillLoader()
    persona = loader.load_persona("omnia-data", "developer")

    # Get subagent definitions for SDK
    agents = persona.get_agent_definitions()

    # Discover available personas for a team
    personas = discover_personas("omnia-data")
    # Returns: [{"name": "developer", "display_name": "Developer", ...}, ...]

    # Detect code reviewer from PR files
    from triagent.skills import detect_code_reviewer
    reviewer = detect_code_reviewer([".cs", ".csproj"])

    # Dynamic skill loading
    from triagent.skills.skill_loader import (
        match_skill_trigger,
        detect_code_review_language,
        load_sub_skill,
    )

    # Template rendering
    from triagent.skills.template_loader import (
        load_template,
        render_template,
        create_report_from_template,
    )
"""

from .loader import (
    SkillLoader,
    discover_personas,
    get_available_personas,
    get_persona_full_context,
    load_persona,
    load_skill,
    load_skill_by_name,
    parse_frontmatter,
)
from .models import (
    FILE_EXTENSION_MAP,
    LoadedPersona,
    PersonaDefinition,
    SkillDefinition,
    SkillMetadata,
    SubagentConfig,
    detect_code_reviewer,
)
from .system import get_system_prompt

__all__ = [
    # Models
    "SkillMetadata",
    "SkillDefinition",
    "SubagentConfig",
    "PersonaDefinition",
    "LoadedPersona",
    # Loader
    "SkillLoader",
    "load_skill",
    "load_skill_by_name",
    "load_persona",
    "get_available_personas",
    "get_persona_full_context",
    "discover_personas",
    "parse_frontmatter",
    # System prompt
    "get_system_prompt",
    # Language detection
    "FILE_EXTENSION_MAP",
    "detect_code_reviewer",
]
