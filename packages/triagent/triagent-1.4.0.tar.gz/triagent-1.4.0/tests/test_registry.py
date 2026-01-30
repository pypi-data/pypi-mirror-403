"""Tests for command registry."""

from __future__ import annotations

import pytest

from triagent.commands.registry import (
    CommandInfo,
    clear_registry,
    get_all_commands,
    get_command,
    get_commands_for_picker,
    register_command,
)


@pytest.fixture(autouse=True)
def clean_registry():
    """Clear registry before and after each test."""
    clear_registry()
    yield
    clear_registry()


class TestCommandRegistry:
    """Tests for the command registry system."""

    def test_register_command_adds_to_registry(self):
        """Test that @register_command decorator adds command to registry."""

        @register_command(name="test-cmd", description="Test command")
        def test_handler():
            pass

        cmd = get_command("test-cmd")
        assert cmd is not None
        assert cmd.name == "test-cmd"
        assert cmd.description == "Test command"
        assert cmd.handler is test_handler

    def test_aliases_registered(self):
        """Test that command aliases are registered correctly."""

        @register_command(name="quit", description="Exit", aliases=["q", "exit"])
        def quit_handler():
            pass

        # All should return same command
        assert get_command("quit") is not None
        assert get_command("q") is get_command("quit")
        assert get_command("exit") is get_command("quit")

    def test_get_all_commands_no_duplicates(self):
        """Test that get_all_commands returns unique commands only."""

        @register_command(name="cmd1", description="Command 1", aliases=["alias1"])
        def handler1():
            pass

        @register_command(name="cmd2", description="Command 2")
        def handler2():
            pass

        commands = get_all_commands()
        names = [c.name for c in commands]

        assert len(names) == len(set(names))  # No duplicates
        assert "cmd1" in names
        assert "cmd2" in names
        assert "alias1" not in names  # Aliases shouldn't appear as separate entries

    def test_get_commands_for_picker_format(self):
        """Test that get_commands_for_picker returns correct format."""

        @register_command(name="help", description="Show help")
        def help_handler():
            pass

        @register_command(name="config", description="View config")
        def config_handler():
            pass

        commands = get_commands_for_picker()

        assert isinstance(commands, list)
        for cmd, desc in commands:
            assert cmd.startswith("/")  # All have slash prefix
            assert isinstance(desc, str)

        # Check specific commands
        command_dict = dict(commands)
        assert "/help" in command_dict
        assert "/config" in command_dict
        assert command_dict["/help"] == "Show help"

    def test_get_command_returns_none_for_unknown(self):
        """Test that get_command returns None for unknown commands."""
        assert get_command("nonexistent") is None

    def test_command_info_dataclass(self):
        """Test CommandInfo dataclass structure."""
        info = CommandInfo(
            name="test",
            description="Test description",
            handler=lambda: None,
            aliases=["t"],
            category="triagent",
        )

        assert info.name == "test"
        assert info.description == "Test description"
        assert info.aliases == ["t"]
        assert info.category == "triagent"

    def test_clear_registry(self):
        """Test that clear_registry removes all commands."""

        @register_command(name="temp", description="Temporary")
        def temp_handler():
            pass

        assert get_command("temp") is not None

        clear_registry()

        assert get_command("temp") is None
        assert len(get_all_commands()) == 0
