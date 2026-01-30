"""Command registry with decorator for self-registration.

This module provides a decorator-based command registration system that allows
commands to self-register with metadata. The registry enables dynamic command
discovery for the command picker and help system.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass
class CommandInfo:
    """Metadata for a registered command."""

    name: str
    description: str
    handler: Callable[..., Any]
    aliases: list[str] = field(default_factory=list)
    category: str = "triagent"  # "triagent" or "claude-code"


# Global registry - populated when command modules are imported
_registry: dict[str, CommandInfo] = {}


def register_command(
    name: str,
    description: str,
    aliases: list[str] | None = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to register a command handler.

    Usage:
        @register_command(name="help", description="Show available commands")
        def help_command(console, config_manager, args):
            ...

    Args:
        name: The primary command name (without leading /)
        description: Brief description shown in help/picker
        aliases: Optional list of alternative names for the command

    Returns:
        Decorator function that registers the handler
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        info = CommandInfo(
            name=name,
            description=description,
            handler=func,
            aliases=aliases or [],
        )
        _registry[name] = info
        # Also register aliases pointing to same command
        for alias in info.aliases:
            _registry[alias] = info
        return func

    return decorator


def get_command(name: str) -> CommandInfo | None:
    """Get a command by name or alias.

    Args:
        name: Command name (without leading /)

    Returns:
        CommandInfo if found, None otherwise
    """
    return _registry.get(name)


def get_all_commands() -> list[CommandInfo]:
    """Get all unique commands (excludes alias duplicates).

    Returns:
        List of unique CommandInfo objects
    """
    seen: set[str] = set()
    commands: list[CommandInfo] = []
    for info in _registry.values():
        if info.name not in seen:
            seen.add(info.name)
            commands.append(info)
    return commands


def get_commands_for_picker() -> list[tuple[str, str]]:
    """Get commands formatted for the command picker.

    Returns:
        List of (command_name_with_slash, description) tuples
    """
    return [(f"/{cmd.name}", cmd.description) for cmd in get_all_commands()]


def clear_registry() -> None:
    """Clear the registry. Used primarily for testing."""
    _registry.clear()
