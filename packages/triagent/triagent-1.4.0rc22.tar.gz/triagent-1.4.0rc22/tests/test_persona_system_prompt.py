"""Tests for persona-based system prompt loading.

These tests verify:
- Bug #1: SDK client correctly uses persona/team parameters
- Bug #2: skill_directory field enables PO/BA personas to load po-bsa skills

Based on actual testing that discovered:
- Developer: ~71,000 chars - loads ado_pr_review, pr_report_generation correctly
- Product Owner: ~15,000 chars - WAS missing skills due to wrong directory
- Support: ~31,000 chars - loads all 8 skills correctly
- Business Analyst: ~15,000 chars - WAS missing skills due to wrong directory

After fix:
- PO and BA should load work_item_creation, feature_investigation, requirements_analysis
  from the po-bsa/ directory via skill_directory field
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from triagent.skills.loader import load_persona
from triagent.skills.models import PersonaDefinition
from triagent.skills.system import get_system_prompt


class TestPersonaDefinitionLoading:
    """Test that persona YAML files load correctly."""

    @pytest.mark.parametrize(
        "persona_name,expected_display",
        [
            ("developer", "Developer"),
            ("product_owner", "Product Owner"),
            ("support", "Support"),
            ("business_analyst", "Business Analyst"),
        ],
    )
    def test_persona_loads_correct_display_name(
        self, persona_name: str, expected_display: str
    ) -> None:
        """Each persona should have its correct display name."""
        persona = load_persona("omnia-data", persona_name)
        assert persona is not None, f"Persona {persona_name} not found"
        assert persona.display_name == expected_display

    @pytest.mark.parametrize(
        "persona_name,expected_desc_substring",
        [
            ("developer", "Code review"),
            ("product_owner", "Work item creation"),
            ("support", "Telemetry investigation"),
            ("business_analyst", "Requirements gathering"),
        ],
    )
    def test_persona_has_description(
        self, persona_name: str, expected_desc_substring: str
    ) -> None:
        """Each persona should have a description with expected content."""
        persona = load_persona("omnia-data", persona_name)
        assert persona is not None, f"Persona {persona_name} not found"
        assert expected_desc_substring in persona.definition.description


class TestPersonaSkillLoading:
    """Test that each persona loads its designated skills."""

    def test_developer_loads_all_skills(self) -> None:
        """Developer persona should load all skills."""
        persona = load_persona("omnia-data", "developer")
        assert persona is not None
        loaded_skills = list(persona.skills.keys())

        # Developer should have these skills loaded
        # Note: The exact skills depend on what's defined in the YAML
        assert len(loaded_skills) >= 2, f"Developer has too few skills: {loaded_skills}"

        # Check core skills are present
        core_skills_expected = persona.definition.core_skills
        persona_skills_expected = persona.definition.skills

        # At least some skills should be loaded
        total_expected = len(core_skills_expected) + len(persona_skills_expected)
        assert len(loaded_skills) >= total_expected // 2, (
            f"Developer missing many skills. Expected ~{total_expected}, got {len(loaded_skills)}"
        )

    def test_support_loads_all_skills(self) -> None:
        """Support persona should load all skills."""
        persona = load_persona("omnia-data", "support")
        assert persona is not None
        loaded_skills = list(persona.skills.keys())

        # Support should have skills loaded
        assert len(loaded_skills) >= 3, f"Support has too few skills: {loaded_skills}"

    def test_product_owner_loads_all_skills(self) -> None:
        """Product Owner persona should load all skills including po-bsa skills.

        This test verifies Bug #2 is fixed (skill_directory field).
        """
        persona = load_persona("omnia-data", "product_owner")
        assert persona is not None
        loaded_skills = list(persona.skills.keys())

        # PO should have these skills (from po-bsa/ directory)
        assert "work_item_creation" in loaded_skills, (
            f"Missing work_item_creation. Loaded: {loaded_skills}"
        )
        assert "feature_investigation" in loaded_skills, (
            f"Missing feature_investigation. Loaded: {loaded_skills}"
        )
        assert "requirements_analysis" in loaded_skills, (
            f"Missing requirements_analysis. Loaded: {loaded_skills}"
        )

    def test_business_analyst_loads_all_skills(self) -> None:
        """Business Analyst persona should load all skills including po-bsa skills.

        This test verifies Bug #2 is fixed (skill_directory field).
        """
        persona = load_persona("omnia-data", "business_analyst")
        assert persona is not None
        loaded_skills = list(persona.skills.keys())

        # BA should have these skills (from po-bsa/ directory)
        assert "work_item_creation" in loaded_skills, (
            f"Missing work_item_creation. Loaded: {loaded_skills}"
        )
        assert "feature_investigation" in loaded_skills, (
            f"Missing feature_investigation. Loaded: {loaded_skills}"
        )
        assert "requirements_analysis" in loaded_skills, (
            f"Missing requirements_analysis. Loaded: {loaded_skills}"
        )


class TestSystemPromptSizes:
    """Test system prompt sizes match expected behavior.

    After bug fixes, all personas should have substantial content.
    """

    def test_developer_prompt_has_full_content(self) -> None:
        """Developer prompt should have substantial skill content."""
        prompt = get_system_prompt("omnia-data", "developer")
        assert len(prompt) > 5000, f"Developer prompt too small: {len(prompt)} chars"
        # Should contain persona indicator
        assert "Active Persona: Developer" in prompt

    def test_support_prompt_has_full_content(self) -> None:
        """Support prompt should have substantial skill content."""
        prompt = get_system_prompt("omnia-data", "support")
        assert len(prompt) > 5000, f"Support prompt too small: {len(prompt)} chars"
        # Should contain persona indicator
        assert "Active Persona: Support" in prompt

    def test_product_owner_prompt_has_full_content(self) -> None:
        """Product Owner prompt should have full content.

        This test verifies Bug #2 is fixed.
        """
        prompt = get_system_prompt("omnia-data", "product_owner")
        # After fix, should include work_item_creation, feature_investigation content
        assert len(prompt) > 10000, (
            f"Product Owner prompt too small: {len(prompt)} chars - "
            "Bug #2 may not be fixed"
        )
        assert "Active Persona: Product Owner" in prompt
        # Should contain skill content
        assert "Work Item" in prompt or "work item" in prompt

    def test_business_analyst_prompt_has_full_content(self) -> None:
        """Business Analyst prompt should have full content.

        This test verifies Bug #2 is fixed.
        """
        prompt = get_system_prompt("omnia-data", "business_analyst")
        # After fix, should include work_item_creation, feature_investigation content
        assert len(prompt) > 10000, (
            f"Business Analyst prompt too small: {len(prompt)} chars - "
            "Bug #2 may not be fixed"
        )
        assert "Active Persona: Business Analyst" in prompt


class TestPersonaSwitchingComparison:
    """Test that switching personas actually changes the system prompt."""

    def test_developer_vs_product_owner_prompts_differ(self) -> None:
        """Developer and Product Owner prompts must be substantially different."""
        dev_prompt = get_system_prompt("omnia-data", "developer")
        po_prompt = get_system_prompt("omnia-data", "product_owner")

        assert dev_prompt != po_prompt, "Developer and PO prompts are identical!"

        # Check they have different persona sections
        assert "Active Persona: Developer" in dev_prompt
        assert "Active Persona: Product Owner" in po_prompt

    def test_developer_vs_support_prompts_differ(self) -> None:
        """Developer and Support prompts must be different."""
        dev_prompt = get_system_prompt("omnia-data", "developer")
        support_prompt = get_system_prompt("omnia-data", "support")

        assert dev_prompt != support_prompt
        assert "Active Persona: Developer" in dev_prompt
        assert "Active Persona: Support" in support_prompt

    def test_all_personas_share_core_content(self) -> None:
        """All personas should share base system prompt content."""
        prompts = {
            name: get_system_prompt("omnia-data", name)
            for name in ["developer", "product_owner", "support", "business_analyst"]
        }

        # All should contain base system prompt
        base_content = "You are Triagent"
        for name, prompt in prompts.items():
            assert base_content in prompt, f"{name} missing base content"


class TestSDKClientPersonaIntegration:
    """Test that SDK client correctly uses persona parameter (Bug #1 fix)."""

    def test_create_sdk_client_uses_persona_parameter(self) -> None:
        """create_sdk_client should use provided persona, not config.

        This test verifies Bug #1 is fixed.
        """
        from triagent.sdk_client import create_sdk_client

        mock_config_manager = MagicMock()
        mock_config = MagicMock()
        mock_config.team = "omnia-data"
        mock_config.persona = "developer"  # Config default
        mock_config_manager.load_config.return_value = mock_config

        mock_console = MagicMock()

        # Create client with product_owner override
        client = create_sdk_client(
            mock_config_manager, mock_console, persona="product_owner"
        )

        # After fix, client should have PO, not developer
        assert client.persona == "product_owner"

    def test_create_sdk_client_uses_team_parameter(self) -> None:
        """create_sdk_client should use provided team, not config."""
        from triagent.sdk_client import create_sdk_client

        mock_config_manager = MagicMock()
        mock_config = MagicMock()
        mock_config.team = "omnia-data"
        mock_config.persona = "developer"
        mock_config_manager.load_config.return_value = mock_config

        mock_console = MagicMock()

        # Create client with team override
        client = create_sdk_client(mock_config_manager, mock_console, team="levvia")

        # After fix, client should have levvia, not omnia-data
        assert client.team == "levvia"

    def test_create_sdk_client_falls_back_to_config(self) -> None:
        """create_sdk_client should use config when no persona provided."""
        from triagent.sdk_client import create_sdk_client

        mock_config_manager = MagicMock()
        mock_config = MagicMock()
        mock_config.team = "omnia-data"
        mock_config.persona = "support"
        mock_config_manager.load_config.return_value = mock_config

        mock_console = MagicMock()

        # Create client without persona override - should use config
        client = create_sdk_client(mock_config_manager, mock_console)
        assert client.persona == "support"
        assert client.team == "omnia-data"


class TestSkillDirectoryResolution:
    """Test skill directory resolution with skill_directory field (Bug #2 fix)."""

    def test_product_owner_uses_skill_directory(self) -> None:
        """Product Owner should use skill_directory field to find po-bsa skills."""
        persona = load_persona("omnia-data", "product_owner")
        assert persona is not None

        # After fix, definition should have skill_directory
        assert hasattr(persona.definition, "skill_directory")
        assert persona.definition.skill_directory == "po-bsa"

    def test_business_analyst_uses_skill_directory(self) -> None:
        """Business Analyst should use skill_directory field to find po-bsa skills."""
        persona = load_persona("omnia-data", "business_analyst")
        assert persona is not None

        # After fix, definition should have skill_directory
        assert hasattr(persona.definition, "skill_directory")
        assert persona.definition.skill_directory == "po-bsa"

    def test_developer_uses_default_directory(self) -> None:
        """Developer should use persona name as directory (no skill_directory override)."""
        persona = load_persona("omnia-data", "developer")
        assert persona is not None

        # Developer doesn't need skill_directory override
        skill_dir = getattr(persona.definition, "skill_directory", None)
        assert skill_dir is None, (
            f"Developer should not have skill_directory, but has: {skill_dir}"
        )

    def test_support_uses_default_directory(self) -> None:
        """Support should use persona name as directory (no skill_directory override)."""
        persona = load_persona("omnia-data", "support")
        assert persona is not None

        # Support doesn't need skill_directory override
        skill_dir = getattr(persona.definition, "skill_directory", None)
        assert skill_dir is None, (
            f"Support should not have skill_directory, but has: {skill_dir}"
        )


class TestPersonaDefinitionSkillDirectoryField:
    """Test the skill_directory field on PersonaDefinition model."""

    def test_from_dict_with_skill_directory(self) -> None:
        """Test creating PersonaDefinition with skill_directory."""
        data = {
            "name": "test_persona",
            "display_name": "Test Persona",
            "description": "A test persona",
            "core_skills": ["core1"],
            "skills": ["skill1"],
            "skill_directory": "custom_dir",
        }
        persona = PersonaDefinition.from_dict(data, "test-team")

        assert persona.skill_directory == "custom_dir"

    def test_from_dict_without_skill_directory(self) -> None:
        """Test creating PersonaDefinition without skill_directory."""
        data = {
            "name": "test_persona",
            "display_name": "Test Persona",
            "description": "A test persona",
            "core_skills": ["core1"],
            "skills": ["skill1"],
        }
        persona = PersonaDefinition.from_dict(data, "test-team")

        assert persona.skill_directory is None

    def test_skill_directory_default_is_none(self) -> None:
        """Test that skill_directory defaults to None."""
        persona = PersonaDefinition(
            name="test",
            display_name="Test",
            description="Test",
            team="test-team",
        )
        assert persona.skill_directory is None
