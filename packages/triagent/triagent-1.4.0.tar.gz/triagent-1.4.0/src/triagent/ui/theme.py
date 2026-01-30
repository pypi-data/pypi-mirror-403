"""Theme constants for Triagent CLI UI.

This module defines color constants and style presets for consistent
visual appearance across the CLI interface.
"""

from __future__ import annotations

# Primary colors
PRIMARY_COLOR = "cyan"
SECONDARY_COLOR = "blue"
ACCENT_COLOR = "green"
WARNING_COLOR = "yellow"
ERROR_COLOR = "red"
DIM_COLOR = "dim"

# Mascot colors
MASCOT_FRAME = "blue"
MASCOT_EYES = "bright_cyan"
MASCOT_MOUTH = "white"

# Prompt colors
PROMPT_SYMBOL_COLOR = "cyan"
PROMPT_ACTIVE_COLOR = "bold cyan"

# Status indicator colors
STATUS_RUNNING = "yellow"
STATUS_SUCCESS = "green"
STATUS_ERROR = "red"
STATUS_HINT = "dim"

# Prompt symbols
PROMPT_SYMBOL = "\u276f"  # ❯ (heavy right-pointing angle quotation mark)
PROMPT_CONTINUATION = "\u2026"  # … (horizontal ellipsis)

# Status messages
CANCEL_MESSAGE = "Stopped"
EXIT_MESSAGE = "Goodbye!"
HINT_ESC_TO_STOP = "esc to stop"

# Spinner characters (braille)
BRAILLE_SPINNER = ["\u280b", "\u2819", "\u2839", "\u2838", "\u283c", "\u2834", "\u2826", "\u2827", "\u2807", "\u280f"]
# ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
