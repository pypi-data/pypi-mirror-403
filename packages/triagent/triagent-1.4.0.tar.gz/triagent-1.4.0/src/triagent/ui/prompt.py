"""Async prompt with ESC cancellation and "/" command picker support for Triagent CLI.

This module provides the AsyncPrompt class that enables:
- Command-line style prompt (❯)
- ESC key to gracefully cancel operations
- "/" key to trigger command picker immediately
- Enter to send message immediately
- Session preservation after cancellation
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import TYPE_CHECKING

from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.patch_stdout import patch_stdout

from triagent.ui.theme import (
    CANCEL_MESSAGE,
    DIM_COLOR,
    PROMPT_SYMBOL,
    PROMPT_SYMBOL_COLOR,
)

if TYPE_CHECKING:
    from rich.console import Console

# Special marker returned when "/" is pressed to trigger command picker
SLASH_COMMAND_MARKER = "__SLASH_COMMAND__"


class CancellationContext:
    """Context for managing cancellation state across operations.

    This class provides a shared cancellation event that can be checked
    by long-running operations to gracefully stop when ESC is pressed.
    """

    def __init__(self) -> None:
        """Initialize cancellation context."""
        self._cancel_event = asyncio.Event()
        self._is_processing = False

    @property
    def is_cancelled(self) -> bool:
        """Check if cancellation has been requested."""
        return self._cancel_event.is_set()

    @property
    def is_processing(self) -> bool:
        """Check if an operation is currently in progress."""
        return self._is_processing

    def request_cancel(self) -> None:
        """Request cancellation of current operation."""
        self._cancel_event.set()

    def clear(self) -> None:
        """Clear the cancellation state."""
        self._cancel_event.clear()

    def start_processing(self) -> None:
        """Mark that processing has started."""
        self._is_processing = True

    def stop_processing(self) -> None:
        """Mark that processing has stopped."""
        self._is_processing = False
        self.clear()


class AsyncPrompt:
    """Async prompt with ESC cancellation and command-line styling.

    This class wraps prompt-toolkit to provide:
    - Async input with event loop integration
    - ESC key binding to cancel operations
    - Styled prompt symbol (❯)
    - Integration with Rich console for output
    """

    def __init__(
        self,
        console: Console,
        cancel_context: CancellationContext | None = None,
    ) -> None:
        """Initialize the async prompt.

        Args:
            console: Rich console for output
            cancel_context: Shared cancellation context (created if not provided)
        """
        self.console = console
        self.cancel_context = cancel_context or CancellationContext()
        self._on_cancel_callback: Callable[[], None] | None = None

        # Set up key bindings
        self._kb = KeyBindings()
        self._setup_keybindings()

        # Create prompt session with bindings
        self._session = PromptSession(key_bindings=self._kb)

    def _setup_keybindings(self) -> None:
        """Set up key bindings for the prompt."""

        @self._kb.add("escape")
        def handle_escape(event: object) -> None:
            """Handle ESC key press."""
            if self.cancel_context.is_processing:
                self.cancel_context.request_cancel()
                if self._on_cancel_callback:
                    self._on_cancel_callback()

        @self._kb.add("tab")
        def handle_tab(event: object) -> None:
            """Handle Tab key press - trigger command picker.

            When Tab is pressed at the start of input (empty buffer), exit
            immediately with a special marker so the caller can show the
            command picker.
            """
            # Only trigger if input buffer is empty (at start of input)
            if not event.app.current_buffer.text:  # type: ignore[union-attr]
                event.app.exit(result=SLASH_COMMAND_MARKER)  # type: ignore[union-attr]
            # If there's text, Tab does nothing (no autocomplete implemented)

    def set_cancel_callback(self, callback: Callable[[], None]) -> None:
        """Set a callback to be called when ESC is pressed during processing.

        Args:
            callback: Function to call on cancellation
        """
        self._on_cancel_callback = callback

    def get_prompt_text(self) -> FormattedText:
        """Get the formatted prompt text.

        Returns:
            FormattedText with styled prompt symbol
        """
        return FormattedText(
            [
                (f"fg:{PROMPT_SYMBOL_COLOR}", f"{PROMPT_SYMBOL} "),
            ]
        )

    async def prompt_async(self, message: str | None = None) -> str | None:
        """Get user input asynchronously.

        Args:
            message: Optional custom prompt message (uses default if not provided)

        Returns:
            User input string, or None if cancelled/empty
        """
        prompt_text = message if message else self.get_prompt_text()

        try:
            with patch_stdout():
                result = await self._session.prompt_async(prompt_text)
                return result.strip() if result else None
        except (EOFError, KeyboardInterrupt):
            return None

    async def prompt_with_cancel_check(
        self,
        message: str | None = None,
    ) -> tuple[str | None, bool]:
        """Get user input with cancellation check.

        This method checks if cancellation was requested during input.

        Args:
            message: Optional custom prompt message

        Returns:
            Tuple of (user_input, was_cancelled)
        """
        self.cancel_context.clear()
        result = await self.prompt_async(message)

        if self.cancel_context.is_cancelled:
            return None, True

        return result, False


def create_simple_prompt() -> str:
    """Create a simple non-async prompt string.

    Returns:
        Formatted prompt string for use with input()
    """
    return f"{PROMPT_SYMBOL} "


async def async_input_with_cancel(
    prompt: str,
    cancel_event: asyncio.Event,
    check_interval: float = 0.1,
) -> str | None:
    """Get input asynchronously with cancellation support.

    This is a simpler alternative that doesn't require prompt-toolkit,
    using run_in_executor for the blocking input.

    Args:
        prompt: The prompt string to display
        cancel_event: Event to check for cancellation
        check_interval: How often to check for cancellation (seconds)

    Returns:
        User input string, or None if cancelled
    """
    loop = asyncio.get_event_loop()

    # Create a future for the input
    input_future = loop.run_in_executor(None, input, prompt)

    while True:
        # Check if cancelled
        if cancel_event.is_set():
            input_future.cancel()
            return None

        # Check if input is ready
        try:
            result = await asyncio.wait_for(
                asyncio.shield(input_future),
                timeout=check_interval,
            )
            return result.strip() if result else None
        except TimeoutError:
            continue
        except (EOFError, KeyboardInterrupt):
            return None


def display_cancel_message(console: Console) -> None:
    """Display the cancellation message.

    Args:
        console: Rich console for output
    """
    console.print(f"\n[{DIM_COLOR}]{CANCEL_MESSAGE}[/{DIM_COLOR}]")
