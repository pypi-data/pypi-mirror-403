"""Status indicators for Triagent CLI.

This module provides visual indicators for:
- "esc to stop" hint during operations
- Operation status messages
- Progress indicators
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.text import Text

from triagent.ui.theme import (
    BRAILLE_SPINNER,
    HINT_ESC_TO_STOP,
    STATUS_HINT,
    STATUS_RUNNING,
)

if TYPE_CHECKING:
    from rich.console import Console


class StatusIndicator:
    """Animated status indicator with hint text.

    This class provides a status line that shows:
    - Spinner animation
    - Current operation message
    - "esc to stop" hint on the right side
    """

    def __init__(
        self,
        message: str = "Processing",
        show_hint: bool = True,
        color: str = STATUS_RUNNING,
    ) -> None:
        """Initialize the status indicator.

        Args:
            message: The status message to display
            show_hint: Whether to show "esc to stop" hint
            color: Color for the spinner and message
        """
        self.message = message
        self.show_hint = show_hint
        self.color = color
        self._spinner_idx = 0

    def get_spinner_char(self) -> str:
        """Get the next spinner character.

        Returns:
            Current spinner character
        """
        char = BRAILLE_SPINNER[self._spinner_idx % len(BRAILLE_SPINNER)]
        self._spinner_idx += 1
        return char

    def __rich__(self) -> Text:
        """Render the status indicator as Rich Text.

        Returns:
            Formatted status line
        """
        spinner = self.get_spinner_char()
        text = Text()
        text.append(f"{spinner} {self.message}...", style=self.color)

        if self.show_hint:
            # Add spacing and hint on the right
            # Use a reasonable fixed width for alignment
            text.append("  ")
            text.append(HINT_ESC_TO_STOP, style=STATUS_HINT)

        return text


class EscToStopHint:
    """Simple "esc to stop" hint text.

    This class renders just the hint text, useful for combining
    with other status displays.
    """

    def __rich__(self) -> Text:
        """Render the hint as Rich Text.

        Returns:
            Formatted hint text
        """
        return Text(HINT_ESC_TO_STOP, style=STATUS_HINT)


def show_esc_hint(console: Console) -> None:
    """Display the "esc to stop" hint.

    Args:
        console: Rich console for output
    """
    console.print(f"[{STATUS_HINT}]{HINT_ESC_TO_STOP}[/{STATUS_HINT}]", end="")


def clear_esc_hint(console: Console) -> None:
    """Clear the "esc to stop" hint from the line.

    Args:
        console: Rich console for output
    """
    # Move cursor back and clear the hint
    hint_length = len(HINT_ESC_TO_STOP)
    console.print("\r" + " " * hint_length + "\r", end="")
