"""Triagent slash commands - auto-loads all commands to populate registry."""

from __future__ import annotations

import importlib
import pkgutil
from pathlib import Path


def load_commands() -> None:
    """Import all command modules to trigger registration.

    This function scans the commands directory and imports all modules
    (except registry.py) which triggers the @register_command decorators.
    """
    package_dir = Path(__file__).parent
    for module_info in pkgutil.iter_modules([str(package_dir)]):
        if module_info.name != "registry":  # Skip registry itself
            importlib.import_module(f"triagent.commands.{module_info.name}")


# Auto-load on import
load_commands()

# Re-export registry functions for convenience
# Legacy exports for backward compatibility
from triagent.commands.clear import clear_command  # noqa: E402
from triagent.commands.config import config_command  # noqa: E402
from triagent.commands.confirm import confirm_command  # noqa: E402
from triagent.commands.exit import exit_command  # noqa: E402
from triagent.commands.help import help_command  # noqa: E402
from triagent.commands.init import init_command  # noqa: E402
from triagent.commands.persona import persona_command  # noqa: E402
from triagent.commands.registry import (  # noqa: E402
    CommandInfo,
    clear_registry,
    get_all_commands,
    get_command,
    get_commands_for_picker,
    register_command,
)
from triagent.commands.team import team_command  # noqa: E402
from triagent.commands.versions import versions_command  # noqa: E402

__all__ = [
    # Registry functions
    "CommandInfo",
    "clear_registry",
    "get_all_commands",
    "get_command",
    "get_commands_for_picker",
    "register_command",
    # Command handlers (legacy exports)
    "clear_command",
    "config_command",
    "confirm_command",
    "exit_command",
    "help_command",
    "init_command",
    "persona_command",
    "team_command",
    "versions_command",
]
