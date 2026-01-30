"""Unit tests for persona switching functionality."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from triagent.skills.loader import get_persona_full_context

if TYPE_CHECKING:
    from triagent.config import ConfigManager


def _can_load_encrypted_skills() -> bool:
    """Check if encrypted skills can be loaded (corporate environment + encryption works)."""
    try:
        from triagent.skills.encrypted_loader import (
            is_encrypted_mode,
            load_encrypted_skills,
        )

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


class TestGetPersonaFullContext:
    """Tests for get_persona_full_context function."""

    @requires_encrypted_skills
    def test_get_developer_context(self) -> None:
        """Test getting full context for developer persona."""
        context = get_persona_full_context("omnia-data", "developer")

        assert context is not None
        assert "display_name" in context
        assert "description" in context
        assert "capabilities" in context
        assert "skill_content" in context
        assert "on_demand_skills" in context
        assert "system_prompt_additions" in context

        # Developer should have capabilities
        assert len(context["capabilities"]) > 0

    @requires_encrypted_skills
    def test_get_support_context(self) -> None:
        """Test getting full context for support persona."""
        context = get_persona_full_context("omnia-data", "support")

        assert context is not None
        assert context["display_name"] == "Support"
        assert len(context["capabilities"]) > 0

    def test_get_invalid_persona_context(self) -> None:
        """Test invalid persona returns None."""
        context = get_persona_full_context("omnia-data", "invalid")
        assert context is None

    def test_get_invalid_team_context(self) -> None:
        """Test invalid team returns None."""
        context = get_persona_full_context("invalid-team", "developer")
        assert context is None

    @requires_encrypted_skills
    def test_skill_content_not_empty(self) -> None:
        """Test that skill content is included."""
        context = get_persona_full_context("omnia-data", "developer")

        assert context is not None
        # Should have some skill content
        assert len(context["skill_content"]) > 0


class TestSwitchPersonaTool:
    """Tests for switch_persona MCP tool."""

    @pytest.fixture
    def temp_config(
        self, isolated_config_manager: ConfigManager
    ) -> ConfigManager:
        """Provide a temp config manager with default settings."""
        from triagent.config import TriagentConfig

        config = TriagentConfig(team="omnia-data", persona="developer")
        isolated_config_manager.save_config(config)
        return isolated_config_manager

    @pytest.mark.asyncio
    @requires_encrypted_skills
    async def test_switch_persona_valid(
        self, temp_config: ConfigManager, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test switching to a valid persona updates config and returns context."""
        from triagent.mcp.tools import switch_persona_tool

        # Mock get_config_manager to return our temp config
        monkeypatch.setattr(
            "triagent.mcp.tools.get_config_manager",
            lambda: temp_config,
        )

        result = await switch_persona_tool({"persona": "support"})

        # Should not be an error
        assert "is_error" not in result or not result["is_error"]

        # Should contain switch confirmation
        text = result["content"][0]["text"]
        assert "Switched to" in text
        assert "Support" in text

        # Verify config was updated
        config = temp_config.load_config()
        assert config.persona == "support"

    @pytest.mark.asyncio
    @requires_encrypted_skills
    async def test_switch_persona_same(
        self, temp_config: ConfigManager, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test switching to current persona shows already using message."""
        from triagent.mcp.tools import switch_persona_tool

        monkeypatch.setattr(
            "triagent.mcp.tools.get_config_manager",
            lambda: temp_config,
        )

        result = await switch_persona_tool({"persona": "developer"})

        text = result["content"][0]["text"]
        assert "Already using" in text
        assert "Developer" in text

    @pytest.mark.asyncio
    @requires_encrypted_skills
    async def test_switch_persona_invalid(
        self, temp_config: ConfigManager, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test switching to invalid persona returns error."""
        from triagent.mcp.tools import switch_persona_tool

        monkeypatch.setattr(
            "triagent.mcp.tools.get_config_manager",
            lambda: temp_config,
        )

        result = await switch_persona_tool({"persona": "admin"})

        assert result.get("is_error") is True
        text = result["content"][0]["text"]
        assert "Invalid persona" in text
        assert "admin" in text

    @pytest.mark.asyncio
    @requires_encrypted_skills
    async def test_switch_persona_case_insensitive(
        self, temp_config: ConfigManager, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test persona names are case insensitive."""
        from triagent.mcp.tools import switch_persona_tool

        monkeypatch.setattr(
            "triagent.mcp.tools.get_config_manager",
            lambda: temp_config,
        )

        result = await switch_persona_tool({"persona": "SUPPORT"})

        # Should not be an error
        assert "is_error" not in result or not result["is_error"]

        # Verify config was updated
        config = temp_config.load_config()
        assert config.persona == "support"

    @pytest.mark.asyncio
    @requires_encrypted_skills
    async def test_switch_persona_includes_capabilities(
        self, temp_config: ConfigManager, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test switch response includes capabilities list."""
        from triagent.mcp.tools import switch_persona_tool

        monkeypatch.setattr(
            "triagent.mcp.tools.get_config_manager",
            lambda: temp_config,
        )

        result = await switch_persona_tool({"persona": "support"})

        text = result["content"][0]["text"]
        assert "Available Capabilities" in text


class TestSystemPromptWithSwitching:
    """Tests for system prompt with persona switching instructions."""

    @requires_encrypted_skills
    def test_system_prompt_includes_switching_instructions(self) -> None:
        """Test that system prompt includes persona switching section."""
        from triagent.skills.system import get_system_prompt

        prompt = get_system_prompt("omnia-data", "developer")

        assert "Persona Switching" in prompt
        assert "switch_persona" in prompt

    @requires_encrypted_skills
    def test_system_prompt_includes_available_personas(self) -> None:
        """Test that system prompt lists available personas."""
        from triagent.skills.system import get_system_prompt

        prompt = get_system_prompt("omnia-data", "developer")

        assert "Available personas" in prompt or "developer" in prompt.lower()


class TestPersonaSwitchIntegration:
    """Integration tests for persona switching."""

    @pytest.fixture
    def isolated_config_with_team(
        self, isolated_config_manager: ConfigManager
    ) -> ConfigManager:
        """Config manager with omnia-data team configured."""
        from triagent.config import TriagentConfig

        config = TriagentConfig(team="omnia-data", persona="developer")
        isolated_config_manager.save_config(config)
        return isolated_config_manager

    @pytest.mark.asyncio
    @requires_encrypted_skills
    async def test_config_persists_after_switch(
        self,
        isolated_config_with_team: ConfigManager,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test config.json is updated and persists after switch."""
        from triagent.mcp.tools import switch_persona_tool

        monkeypatch.setattr(
            "triagent.mcp.tools.get_config_manager",
            lambda: isolated_config_with_team,
        )

        await switch_persona_tool({"persona": "support"})

        # Create new config manager to re-read from disk
        from triagent.config import ConfigManager

        new_manager = ConfigManager(config_dir=isolated_config_with_team.config_dir)
        config = new_manager.load_config()
        assert config.persona == "support"

    @requires_encrypted_skills
    def test_skill_content_in_context(self) -> None:
        """Test that full skill content is included in context."""
        context = get_persona_full_context("omnia-data", "support")

        assert context is not None
        # Should include actual skill instructions
        assert len(context["skill_content"]) > 100  # Should have substantial content
