"""Triagent UI components.

This module provides UI components for the Triagent CLI including:
- ASCII banner with bot mascot
- Async prompt with ESC cancellation
- Status indicators
- Theme constants
"""

from triagent.ui.banner import (
    create_banner_content,
    display_banner,
    display_banner_panel,
    get_mascot_lines,
)
from triagent.ui.indicators import (
    EscToStopHint,
    StatusIndicator,
    clear_esc_hint,
    show_esc_hint,
)
from triagent.ui.prompt import (
    SLASH_COMMAND_MARKER,
    AsyncPrompt,
    CancellationContext,
    async_input_with_cancel,
    create_simple_prompt,
    display_cancel_message,
)
from triagent.ui.theme import (
    BRAILLE_SPINNER,
    CANCEL_MESSAGE,
    HINT_ESC_TO_STOP,
    PROMPT_SYMBOL,
)

__all__ = [
    # Banner
    "create_banner_content",
    "display_banner",
    "display_banner_panel",
    "get_mascot_lines",
    # Prompt
    "AsyncPrompt",
    "CancellationContext",
    "SLASH_COMMAND_MARKER",
    "async_input_with_cancel",
    "create_simple_prompt",
    "display_cancel_message",
    # Indicators
    "EscToStopHint",
    "StatusIndicator",
    "clear_esc_hint",
    "show_esc_hint",
    # Theme constants
    "BRAILLE_SPINNER",
    "CANCEL_MESSAGE",
    "HINT_ESC_TO_STOP",
    "PROMPT_SYMBOL",
]
