"""Exit command for Triagent CLI."""

from __future__ import annotations

from rich.console import Console

from triagent.commands.registry import register_command
from triagent.session_logger import log_session_end


@register_command(
    name="exit",
    description="Exit triagent",
    aliases=["quit", "q"],
)
def exit_command(console: Console) -> bool:
    """Exit the triagent CLI.

    Args:
        console: Rich console for output

    Returns:
        False to signal exit
    """
    console.print("[dim]Goodbye![/dim]")
    log_session_end()  # Guard prevents duplicate logging
    return False
