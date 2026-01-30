"""Versions command for Triagent CLI."""

from __future__ import annotations

from rich.console import Console

from triagent.commands.registry import register_command
from triagent.versions import (
    AZURE_EXTENSION_VERSIONS,
    CLAUDE_CODE_VERSION,
    MCP_AZURE_DEVOPS_VERSION,
    __version__,
)


@register_command(
    name="versions",
    description="Show installed tool versions",
)
def versions_command(console: Console) -> None:
    """Display installed and pinned tool versions.

    Args:
        console: Rich console for output
    """
    from triagent.mcp.setup import (
        check_azure_cli_installed,
        check_claude_code_installed,
        check_nodejs_installed,
    )

    console.print()
    console.print("[bold cyan]Triagent Tool Versions[/bold cyan]")
    console.print()

    # Triagent version
    console.print(f"  [bold]Triagent CLI:[/bold]         v{__version__}")
    console.print()

    # Detected installed versions
    console.print("[bold]Installed Tools:[/bold]")
    az_installed, az_version = check_azure_cli_installed()
    node_installed, node_version = check_nodejs_installed()
    claude_installed, claude_version = check_claude_code_installed()

    az_display = az_version if az_installed else "[red]Not installed[/red]"
    node_display = node_version if node_installed else "[red]Not installed[/red]"
    claude_display = claude_version if claude_installed else "[red]Not installed[/red]"

    console.print(f"  Azure CLI:             {az_display}")
    console.print(f"  Node.js:               {node_display}")
    console.print(f"  Claude Code CLI:       {claude_display}")
    console.print()

    # Pinned versions (used by /init)
    console.print("[bold]Pinned Versions (used by /init):[/bold]")
    console.print(f"  Claude Code:           v{CLAUDE_CODE_VERSION}")
    console.print(f"  MCP Azure DevOps:      v{MCP_AZURE_DEVOPS_VERSION}")
    for ext_name, ext_version in AZURE_EXTENSION_VERSIONS.items():
        console.print(f"  az ext {ext_name}:  v{ext_version}")
    console.print()
