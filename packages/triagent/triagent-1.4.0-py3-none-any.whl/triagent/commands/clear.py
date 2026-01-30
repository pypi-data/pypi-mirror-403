"""Clear command for Triagent CLI."""

from __future__ import annotations

from rich.console import Console

from triagent.commands.registry import register_command


@register_command(
    name="clear",
    description="Clear conversation history",
)
def clear_command(console: Console) -> bool:
    """Clear the conversation history.

    Args:
        console: Rich console for output

    Returns:
        True to continue
    """
    console.print("[dim]Conversation cleared (new session on next message)[/dim]")
    return True
