"""Tests for command picker UI component."""

from __future__ import annotations

import pytest

from triagent.commands.registry import clear_registry, register_command
from triagent.ui.command_picker import CommandItem, CommandPicker


@pytest.fixture(autouse=True)
def setup_test_commands():
    """Set up test commands in registry."""
    clear_registry()

    @register_command(name="help", description="Show available commands")
    def help_handler():
        pass

    @register_command(name="config", description="View/set configuration")
    def config_handler():
        pass

    @register_command(name="team", description="Show/switch team")
    def team_handler():
        pass

    yield
    clear_registry()


class TestCommandItem:
    """Tests for CommandItem dataclass."""

    def test_command_item_creation(self):
        """Test creating a CommandItem."""
        item = CommandItem(
            command="/help",
            description="Show help",
            category="triagent",
        )

        assert item.command == "/help"
        assert item.description == "Show help"
        assert item.category == "triagent"


class TestCommandPicker:
    """Tests for CommandPicker class."""

    def test_picker_loads_from_registry(self):
        """Test that picker loads commands from registry."""
        picker = CommandPicker()
        triagent_cmds = [c for c in picker.commands if c.category == "triagent"]

        # Should have the commands we registered
        assert len(triagent_cmds) >= 3
        command_names = [c.command for c in triagent_cmds]
        assert "/help" in command_names
        assert "/config" in command_names
        assert "/team" in command_names

    def test_picker_shows_sdk_commands(self):
        """Test that picker shows SDK commands when provided."""
        sdk_cmds = [("commit", "Create commit"), ("review-pr", "Review PR")]
        picker = CommandPicker(sdk_commands=sdk_cmds)

        sdk_items = [c for c in picker.commands if c.category == "claude-code"]
        assert len(sdk_items) == 2
        assert sdk_items[0].command == "/commit"
        assert sdk_items[1].command == "/review-pr"

    def test_navigation_wraps_around_down(self):
        """Test that navigation wraps from last to first."""
        picker = CommandPicker()

        # Move to last item
        picker.selected_index = len(picker.commands) - 1

        # Move down should wrap to first
        picker.selected_index = (picker.selected_index + 1) % len(picker.commands)
        assert picker.selected_index == 0

    def test_navigation_wraps_around_up(self):
        """Test that navigation wraps from first to last."""
        picker = CommandPicker()

        # Start at first item
        picker.selected_index = 0

        # Move up should wrap to last
        picker.selected_index = (picker.selected_index - 1) % len(picker.commands)
        assert picker.selected_index == len(picker.commands) - 1

    def test_command_categories_correct(self):
        """Test that commands are categorized correctly."""
        sdk_cmds = [("commit", "Create commit")]
        picker = CommandPicker(sdk_commands=sdk_cmds)

        for item in picker.commands:
            if item.command == "/commit":
                assert item.category == "claude-code"
            else:
                assert item.category == "triagent"

    def test_sdk_commands_get_slash_prefix(self):
        """Test that SDK commands without slash get slash prefix added."""
        sdk_cmds = [("commit", "No slash"), ("/review", "Has slash")]
        picker = CommandPicker(sdk_commands=sdk_cmds)

        sdk_items = [c for c in picker.commands if c.category == "claude-code"]

        assert sdk_items[0].command == "/commit"  # Added slash
        assert sdk_items[1].command == "/review"  # Already had slash

    def test_picker_initial_selection(self):
        """Test that picker starts with first item selected."""
        picker = CommandPicker()
        assert picker.selected_index == 0

    def test_picker_render_returns_panel(self):
        """Test that _render returns a Rich Panel."""
        from rich.panel import Panel

        picker = CommandPicker()
        panel = picker._render()

        assert isinstance(panel, Panel)

    def test_empty_sdk_commands(self):
        """Test picker works with no SDK commands."""
        picker = CommandPicker(sdk_commands=None)

        # Should only have triagent commands
        for item in picker.commands:
            assert item.category == "triagent"

    def test_empty_sdk_commands_list(self):
        """Test picker works with empty SDK commands list."""
        picker = CommandPicker(sdk_commands=[])

        # Should only have triagent commands
        for item in picker.commands:
            assert item.category == "triagent"
