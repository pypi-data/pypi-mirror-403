"""Unit tests for system prompt construction."""

import pytest

from triagent.skills.loader import load_persona
from triagent.skills.system import get_system_prompt


def _can_load_encrypted_skills() -> bool:
    """Check if encrypted skills can be loaded (corporate environment + encryption works)."""
    try:
        from triagent.skills.encrypted_loader import is_encrypted_mode, load_encrypted_skills

        if not is_encrypted_mode():
            return False
        skills = load_encrypted_skills()
        return skills is not None and len(skills.get("skills", [])) > 0
    except Exception:
        return False


requires_encrypted_skills = pytest.mark.skipif(
    not _can_load_encrypted_skills(),
    reason="Requires corporate environment with encrypted skills",
)


@requires_encrypted_skills
class TestSystemPromptConstruction:
    """Tests for system prompt construction with different personas."""

    def test_developer_persona_includes_core_skills(self) -> None:
        """Test that developer persona system prompt includes all core skills."""
        prompt = get_system_prompt("omnia-data", "developer")

        # Verify BASE_SYSTEM_PROMPT content
        assert "You are Triagent" in prompt
        assert "Azure DevOps automation" in prompt

        # Verify team context
        assert "Omnia Data" in prompt
        assert "Audit Cortex 2" in prompt

        # Verify active persona
        assert "Active Persona: Developer" in prompt

        # Verify core skills are listed
        assert "Azure DevOps Basics" in prompt
        assert "Telemetry Basics" in prompt
        assert "ADO LSI/Defect Creation" in prompt

        # Verify core skill CONTENT is included (not just names)
        assert "az boards work-item show" in prompt  # From ado_basics.md
        assert "AppExceptions" in prompt  # From telemetry_basics.md
        assert "Service to Team Mapping" in prompt  # From ado_lsi_defect.md

    def test_support_persona_includes_core_skills(self) -> None:
        """Test that support persona system prompt includes all core skills."""
        prompt = get_system_prompt("omnia-data", "support")

        # Verify active persona
        assert "Active Persona: Support" in prompt

        # Verify core skills content
        assert "Azure DevOps Basics" in prompt
        assert "Telemetry Basics" in prompt
        assert "ADO LSI/Defect Creation" in prompt

        # Verify telemetry-specific content is present
        assert "Log Analytics Workspace Reference" in prompt
        assert "Subscription Switching" in prompt

    def test_developer_persona_includes_persona_specific_skills(self) -> None:
        """Test that developer persona includes developer-specific skills."""
        prompt = get_system_prompt("omnia-data", "developer")

        # Verify developer-specific skills listed
        assert "Developer Skills" in prompt

        # Verify developer skill content included
        # (These may vary based on actual skill files)
        persona = load_persona("omnia-data", "developer")
        for skill_name in persona.definition.skills:
            if skill_name in persona.skills:
                skill = persona.skills[skill_name]
                assert skill.metadata.display_name in prompt

    def test_support_persona_includes_persona_specific_skills(self) -> None:
        """Test that support persona includes support-specific skills."""
        prompt = get_system_prompt("omnia-data", "support")

        # Verify support-specific skills listed
        assert "Support Skills" in prompt

        # Verify support skill content included
        persona = load_persona("omnia-data", "support")
        for skill_name in persona.definition.skills:
            if skill_name in persona.skills:
                skill = persona.skills[skill_name]
                assert skill.metadata.display_name in prompt

    def test_system_prompt_includes_organization_context(self) -> None:
        """Test that system prompt includes correct ADO organization context."""
        prompt = get_system_prompt("omnia-data", "developer")

        assert "symphonyvsts" in prompt
        assert "Audit Cortex 2" in prompt

    def test_ado_basics_content_in_prompt(self) -> None:
        """Test that ado_basics skill content is fully embedded."""
        prompt = get_system_prompt("omnia-data", "developer")

        # Verify key sections from ado_basics.md
        assert "Organization Context" in prompt
        assert "https://dev.azure.com/symphonyvsts" in prompt
        assert "Work Item Operations" in prompt
        assert "Repository Reference" in prompt
        assert "workpaper-service" in prompt  # From repo table
        assert "REST API (For HTML Content)" in prompt

    def test_telemetry_basics_content_in_prompt(self) -> None:
        """Test that telemetry_basics skill content is fully embedded."""
        prompt = get_system_prompt("omnia-data", "developer")

        # Verify key sections from telemetry_basics.md
        assert "Log Analytics Workspace Reference" in prompt
        assert "874aa8fb-6d29-4521-920f-63ac7168404e" in prompt  # AME Non-Prod workspace ID
        assert "ed9e6912-0544-405b-921b-f2d6aad2155e" in prompt  # AME Prod workspace ID
        assert "Subscription Switching" in prompt
        assert "az account set" in prompt
        assert "Service AppRoleName Reference" in prompt
        assert "WorkpaperService" in prompt  # From AppRoleName table

    def test_ado_lsi_defect_content_in_prompt(self) -> None:
        """Test that ado_lsi_defect skill content is fully embedded."""
        prompt = get_system_prompt("omnia-data", "developer")

        # Verify key sections from ado_lsi_defect.md
        assert "Service to Team Mapping" in prompt
        assert "HTML Field Templates" in prompt
        assert "Work Item Creation Workflow" in prompt
        assert "AskUserQuestion" in prompt  # Prompting guidance


@requires_encrypted_skills
class TestCoreSkillsLoading:
    """Tests for core skills loading from team-specific directory."""

    def test_core_skills_loaded_for_developer(self) -> None:
        """Test that all core skills are loaded for developer persona."""
        persona = load_persona("omnia-data", "developer")

        assert persona is not None
        assert "ado_basics" in persona.skills
        assert "telemetry_basics" in persona.skills
        assert "ado_lsi_defect" in persona.skills

    def test_core_skills_loaded_for_support(self) -> None:
        """Test that all core skills are loaded for support persona."""
        persona = load_persona("omnia-data", "support")

        assert persona is not None
        assert "ado_basics" in persona.skills
        assert "telemetry_basics" in persona.skills
        assert "ado_lsi_defect" in persona.skills

    def test_core_skill_content_not_empty(self) -> None:
        """Test that loaded core skills have non-empty content."""
        persona = load_persona("omnia-data", "developer")

        for skill_name in ["ado_basics", "telemetry_basics", "ado_lsi_defect"]:
            assert skill_name in persona.skills
            skill = persona.skills[skill_name]
            assert skill.content, f"{skill_name} has empty content"
            assert len(skill.content) > 100, f"{skill_name} content too short"

    def test_core_skill_metadata_complete(self) -> None:
        """Test that core skills have complete metadata."""
        persona = load_persona("omnia-data", "developer")

        for skill_name in ["ado_basics", "telemetry_basics", "ado_lsi_defect"]:
            skill = persona.skills[skill_name]
            assert skill.metadata.name == skill_name
            assert skill.metadata.display_name, f"{skill_name} missing display_name"
            assert skill.metadata.description, f"{skill_name} missing description"
            assert skill.metadata.version, f"{skill_name} missing version"


@requires_encrypted_skills
class TestTeamSpecificCoreSkills:
    """Tests for team-specific core skill loading (after migration)."""

    def test_omnia_data_core_skills_accessible(self) -> None:
        """Test that omnia-data core skills are accessible (file or encrypted)."""
        from triagent.skills.encrypted_loader import get_skill_content, is_encrypted_mode

        # In encrypted mode, skills should be loadable from encrypted bundle
        # In non-encrypted mode, skills should be loadable from files
        if is_encrypted_mode():
            # Verify skills are accessible via encrypted loader
            ado_basics = get_skill_content("omnia-data/core/ado_basics.md")
            assert ado_basics is not None, "ado_basics.md should be accessible in encrypted bundle"
            assert len(ado_basics) > 100, "ado_basics.md should have content"
        else:
            # Verify skills are accessible via file system
            from triagent.skills.loader import SKILLS_DIR

            team_core_dir = SKILLS_DIR / "omnia-data" / "core"
            assert team_core_dir.exists(), "omnia-data/core/ directory should exist"
            assert (team_core_dir / "ado_basics.md").exists(), "ado_basics.md should exist"
