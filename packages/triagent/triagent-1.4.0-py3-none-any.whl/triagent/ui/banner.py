"""ASCII banner and mascot for Triagent CLI.

This module provides the startup banner with the bot mascot,
version information, and working directory display.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from rich.console import Group
from rich.panel import Panel
from rich.text import Text

from triagent.ui.theme import (
    DIM_COLOR,
    MASCOT_EYES,
    MASCOT_FRAME,
    MASCOT_MOUTH,
    PRIMARY_COLOR,
)

if TYPE_CHECKING:
    from rich.console import Console


def get_mascot_lines() -> list[Text]:
    """Generate the bot mascot ASCII art with colors.

    Returns a list of Rich Text objects for each line of the mascot.
    The mascot is a friendly box bot with an antenna.

    Design:
          │
       ┌─────┐
       │ ◉ ◉ │
       │ ─── │
       └─────┘
    """
    lines = []

    # Antenna
    antenna = Text()
    antenna.append("      ", style="default")
    antenna.append("\u2502", style=MASCOT_FRAME)  # │
    lines.append(antenna)

    # Top border
    top = Text()
    top.append("   ", style="default")
    top.append("\u250c\u2500\u2500\u2500\u2500\u2500\u2510", style=MASCOT_FRAME)  # ┌─────┐
    lines.append(top)

    # Eyes row
    eyes = Text()
    eyes.append("   ", style="default")
    eyes.append("\u2502 ", style=MASCOT_FRAME)  # │
    eyes.append("\u25c9 \u25c9", style=MASCOT_EYES)  # ◉ ◉
    eyes.append(" \u2502", style=MASCOT_FRAME)  # │
    lines.append(eyes)

    # Mouth row
    mouth = Text()
    mouth.append("   ", style="default")
    mouth.append("\u2502 ", style=MASCOT_FRAME)  # │
    mouth.append("\u2500\u2500\u2500", style=MASCOT_MOUTH)  # ───
    mouth.append(" \u2502", style=MASCOT_FRAME)  # │
    lines.append(mouth)

    # Bottom border
    bottom = Text()
    bottom.append("   ", style="default")
    bottom.append("\u2514\u2500\u2500\u2500\u2500\u2500\u2518", style=MASCOT_FRAME)  # └─────┘
    lines.append(bottom)

    return lines


def create_banner_content(version: str, cwd: str | None = None) -> Group:
    """Create the full banner content with mascot and info.

    Args:
        version: The triagent version string
        cwd: Current working directory (defaults to os.getcwd())

    Returns:
        Rich Group containing mascot and info text
    """
    if cwd is None:
        cwd = os.getcwd()

    # Shorten home directory to ~
    home = os.path.expanduser("~")
    if cwd.startswith(home):
        cwd = "~" + cwd[len(home):]

    mascot_lines = get_mascot_lines()

    # Info lines to display next to mascot
    info_lines = [
        "",  # Empty for antenna row
        "",  # Empty for top border
        f"[bold {PRIMARY_COLOR}]Triagent[/bold {PRIMARY_COLOR}] v{version}",
        "Azure DevOps AI Assistant",
        f"[{DIM_COLOR}]{cwd}[/{DIM_COLOR}]",
    ]

    # Combine mascot and info side by side
    combined_lines = []
    for i, mascot_line in enumerate(mascot_lines):
        line = Text()
        line.append_text(mascot_line)
        if i < len(info_lines) and info_lines[i]:
            line.append("    ")  # Spacing between mascot and info
            # For Rich markup, we need to use a separate Text or just append
            combined_lines.append(line)
        else:
            combined_lines.append(line)

    # Create the final renderable
    from rich.console import Group as RichGroup

    renderables = []
    for i, mascot_line in enumerate(mascot_lines):
        if i < len(info_lines) and info_lines[i]:
            # Create a combined line with mascot + info
            from rich.text import Text as RichText

            info_text = RichText.from_markup(info_lines[i])
            # Just append info to the mascot line as plain text
            combined = Text()
            combined.append_text(mascot_line)
            combined.append("    ")
            combined.append_text(info_text)
            renderables.append(combined)
        else:
            renderables.append(mascot_line)

    return RichGroup(*renderables)


def display_banner(console: Console, version: str) -> None:
    """Display the startup banner with mascot.

    Args:
        console: Rich console for output
        version: The triagent version string
    """
    content = create_banner_content(version)
    console.print()
    console.print(content)
    console.print()


def display_banner_panel(console: Console, version: str) -> None:
    """Display the startup banner inside a panel.

    Alternative display style with a border around the banner.

    Args:
        console: Rich console for output
        version: The triagent version string
    """
    content = create_banner_content(version)
    console.print()
    console.print(
        Panel(
            content,
            border_style=MASCOT_FRAME,
            padding=(0, 1),
        )
    )
    console.print()
