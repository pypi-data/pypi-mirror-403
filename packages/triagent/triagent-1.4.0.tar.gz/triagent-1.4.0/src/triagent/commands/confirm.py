"""Confirm command for Triagent CLI."""

from __future__ import annotations

from rich.console import Console

from triagent.commands.registry import register_command
from triagent.config import ConfigManager


@register_command(
    name="confirm",
    description="Toggle write confirmations",
)
def confirm_command(
    console: Console,
    config_manager: ConfigManager,
    args: list[str] | None = None,
) -> bool:
    """Toggle write operation confirmations.

    Usage:
        /confirm       - Show current status
        /confirm on    - Enable confirmations
        /confirm off   - Disable confirmations (auto-approve)

    Args:
        console: Rich console for output
        config_manager: Config manager instance
        args: Command arguments (on/off)

    Returns:
        True to continue
    """
    config = config_manager.load_config()
    arg = args[0].lower() if args else ""

    if arg == "off":
        config.auto_approve_writes = True
        config_manager.save_config(config)
        console.print("[green]✓ Write confirmations DISABLED[/green]")
        console.print("[dim]  ADO/Git write operations will auto-approve[/dim]")
    elif arg == "on":
        config.auto_approve_writes = False
        config_manager.save_config(config)
        console.print("[green]✓ Write confirmations ENABLED[/green]")
        console.print("[dim]  You'll be asked to confirm write operations[/dim]")
    else:
        status = "[red]OFF[/red] (auto-approve)" if config.auto_approve_writes else "[green]ON[/green] (confirm)"
        console.print(f"[bold]Write confirmations:[/bold] {status}")
        console.print()
        console.print("[dim]Usage: /confirm on|off[/dim]")
        console.print("[dim]  on  - Ask for confirmation before write operations[/dim]")
        console.print("[dim]  off - Auto-approve write operations[/dim]")

    return True
