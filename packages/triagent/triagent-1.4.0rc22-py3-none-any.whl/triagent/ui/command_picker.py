"""Command picker menu for slash commands.

This module provides an interactive command picker with arrow key navigation,
showing all available slash commands grouped by category (Triagent vs Claude Code).
"""

from __future__ import annotations

import sys
import time
from dataclasses import dataclass

import readchar
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from triagent.commands import get_commands_for_picker


def _flush_stdin() -> None:
    """Flush stdin to clear any residual input.

    This is needed to prevent the Enter key from the "/" command
    from being read immediately by readchar.
    """
    try:
        import termios

        termios.tcflush(sys.stdin, termios.TCIFLUSH)
    except (ImportError, OSError, AttributeError):
        pass  # Not a TTY, Windows, or other platform issues


@dataclass
class CommandItem:
    """Represents a command in the picker."""

    command: str
    description: str
    category: str  # "triagent" or "claude-code"


class CommandPicker:
    """Interactive command picker with arrow key navigation."""

    def __init__(self, sdk_commands: list[tuple[str, str]] | None = None) -> None:
        """Initialize the command picker.

        Args:
            sdk_commands: List of SDK commands as (name, description) tuples
        """
        self.console = Console()
        self.selected_index = 0
        self.commands: list[CommandItem] = []

        # Get triagent commands from registry (DYNAMIC!)
        for cmd, desc in get_commands_for_picker():
            self.commands.append(CommandItem(cmd, desc, "triagent"))

        # Add SDK commands (from Claude Code)
        if sdk_commands:
            for cmd, desc in sdk_commands:
                full_cmd = f"/{cmd}" if not cmd.startswith("/") else cmd
                self.commands.append(CommandItem(full_cmd, desc, "claude-code"))

    def _render(self) -> Panel:
        """Render the command picker display.

        Returns:
            Rich Panel with the command list
        """
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Command", style="bold")
        table.add_column("Description")

        current_category: str | None = None
        item_index = 0

        for item in self.commands:
            # Add category header when category changes
            if item.category != current_category:
                if current_category is not None:
                    table.add_row("", "")  # Spacer
                current_category = item.category
                header_color = "green" if item.category == "triagent" else "magenta"
                header_text = (
                    "TRIAGENT COMMANDS"
                    if item.category == "triagent"
                    else "CLAUDE CODE COMMANDS"
                )
                table.add_row(
                    Text(f"▸ {header_text}", style=f"bold {header_color}"),
                    "",
                )

            # Render command row
            is_selected = item_index == self.selected_index
            cmd_style = (
                "bold reverse"
                if is_selected
                else ("green" if item.category == "triagent" else "magenta")
            )
            desc_style = "reverse" if is_selected else "dim"

            prefix = "→ " if is_selected else "  "
            table.add_row(
                Text(f"{prefix}{item.command}", style=cmd_style),
                Text(item.description, style=desc_style),
            )
            item_index += 1

        footer = Text("↑↓ Navigate  •  Enter Select  •  ESC Cancel", style="dim")

        return Panel(
            table,
            title="[bold cyan]SLASH COMMAND PICKER[/bold cyan]",
            subtitle=footer,
            border_style="cyan",
        )

    def show(self) -> str | None:
        """Display picker and return selected command or None if cancelled.

        Returns:
            Selected command string or None if cancelled
        """
        if not self.commands:
            self.console.print("[dim]No commands available[/dim]")
            return None

        # Flush stdin to clear any residual input (like Enter key from "/" command)
        _flush_stdin()
        time.sleep(0.05)  # Small delay to let terminal settle

        with Live(self._render(), console=self.console, refresh_per_second=10) as live:
            while True:
                k = readchar.readkey()  # Cross-platform keyboard input

                if k == readchar.key.UP:
                    self.selected_index = (self.selected_index - 1) % len(self.commands)
                elif k == readchar.key.DOWN:
                    self.selected_index = (self.selected_index + 1) % len(self.commands)
                elif k == readchar.key.ENTER or k == "\r" or k == "\n":
                    return self.commands[self.selected_index].command
                elif k == readchar.key.ESCAPE or k == "\x1b":
                    return None

                live.update(self._render())


def show_command_picker(sdk_commands: list[tuple[str, str]] | None = None) -> str | None:
    """Show command picker and return selected command.

    This is a convenience function for quick access to the command picker.

    Args:
        sdk_commands: Optional list of SDK commands as (name, description) tuples

    Returns:
        Selected command string (with leading /) or None if cancelled
    """
    picker = CommandPicker(sdk_commands)
    return picker.show()
