"""System prompts for Triagent CLI."""

from __future__ import annotations

from triagent.skills.loader import get_available_personas, load_persona
from triagent.teams.config import get_team_config

BASE_SYSTEM_PROMPT = """You are Triagent, a Claude-powered assistant for Azure DevOps automation.

You have access to Azure CLI commands and Azure DevOps MCP tools to help users:
- Query Azure Kusto for log data
- Create and manage Azure DevOps work items
- Create, review, and manage Pull Requests
- Monitor build and release pipelines

## Clarifying Questions

When a user's request is ambiguous or missing critical information, use the AskUserQuestion tool
to gather the necessary details BEFORE proceeding. This is especially important for:
- Log/telemetry investigations (need: environment, timeframe, service)
- Work item operations (need: project, area path, assignment)
- Any destructive or irreversible operations

Do NOT make assumptions - ask clarifying questions first to ensure you have the correct context.

Always be helpful, concise, and professional in your responses."""


PERSONA_SWITCHING_INSTRUCTIONS = """
## Persona Switching

You can switch personas when users request different capabilities. Recognize these patterns:
- "switch to [persona]" / "change to [persona]" / "I want to be a [persona]"
- "I need support capabilities" / "help me with code review"
- "can you investigate this incident?" (implies support persona may be needed)
- "let me work as [persona]" / "change my role to [persona]"

**When user requests a persona switch:**
1. Call the `switch_persona` tool with the target persona name
2. The tool returns full persona context and skill instructions
3. Apply those guidelines immediately in this conversation
4. Confirm the switch with a summary of new capabilities

**Important:** The conversation continues seamlessly - no restart occurs. The new persona's
skill content is provided in the tool response for immediate use.
"""


def get_system_prompt(team_name: str, persona_name: str = "developer") -> str:
    """Get the full system prompt for a team and persona.

    Args:
        team_name: Team identifier
        persona_name: Persona name ("developer" or "support")

    Returns:
        Complete system prompt including team and persona-specific instructions
    """
    team_config = get_team_config(team_name)

    prompt_parts = [BASE_SYSTEM_PROMPT]

    # Add persona switching instructions with available personas
    available_personas = get_available_personas(team_name)
    if available_personas:
        persona_list = "\n".join(
            f"- **{p.name}**: {p.description[:80]}..."
            if len(p.description) > 80
            else f"- **{p.name}**: {p.description}"
            for p in available_personas
        )
        switching_with_personas = PERSONA_SWITCHING_INSTRUCTIONS + f"\n**Available personas for this team:**\n{persona_list}\n"
        prompt_parts.append(switching_with_personas)
    else:
        prompt_parts.append(PERSONA_SWITCHING_INSTRUCTIONS)

    if team_config:
        prompt_parts.append("\n## Team Context\n")
        prompt_parts.append(f"- Team: {team_config.display_name}")
        prompt_parts.append(f"- ADO Project: {team_config.ado_project}")
        prompt_parts.append(f"- ADO Organization: {team_config.ado_organization}")

    # Add persona context if available
    persona = load_persona(team_name, persona_name)
    if persona:
        prompt_parts.append(f"\n## Active Persona: {persona.definition.display_name}\n")
        prompt_parts.append(persona.definition.description)

        # Add persona-specific system prompt additions
        if persona.definition.system_prompt_additions:
            prompt_parts.append(f"\n{persona.definition.system_prompt_additions}")

        # Add skills summary section
        if persona.skills:
            prompt_parts.append("\n## Available Skills\n")
            prompt_parts.append(
                "The following skills are available for this persona. "
                "Apply these guidelines DIRECTLY in this conversation.\n"
            )
            prompt_parts.append(
                "**DO NOT use the Task tool to spawn subagents** - "
                "the skill guidelines are included below.\n"
            )

            # Core skills
            core_skill_names = persona.definition.core_skills
            if core_skill_names:
                prompt_parts.append("\n### Core Skills\n")
                for skill_name in core_skill_names:
                    if skill_name in persona.skills:
                        skill = persona.skills[skill_name]
                        prompt_parts.append(
                            f"- **{skill.metadata.display_name}**: "
                            f"{skill.metadata.description}"
                        )

            # Persona-specific skills
            persona_skill_names = persona.definition.skills
            if persona_skill_names:
                prompt_parts.append(f"\n### {persona.definition.display_name} Skills\n")
                for skill_name in persona_skill_names:
                    if skill_name in persona.skills:
                        skill = persona.skills[skill_name]
                        prompt_parts.append(
                            f"- **{skill.metadata.display_name}**: "
                            f"{skill.metadata.description}"
                        )

            prompt_parts.append("\n### How to Use Skills\n")
            prompt_parts.append("1. **Identify the skill** based on user request and file types")
            prompt_parts.append("2. **Fetch relevant data** (PR changes, telemetry, etc.)")
            prompt_parts.append("3. **Apply skill guidelines** from the sections below")
            prompt_parts.append("4. **Provide feedback** following the skill's format\n")

        # Add full skill content as instructions
        for _skill_name, skill in persona.skills.items():
            if skill.content:
                prompt_parts.append(f"\n### {skill.metadata.display_name}\n{skill.content}")

    return "\n".join(prompt_parts)
