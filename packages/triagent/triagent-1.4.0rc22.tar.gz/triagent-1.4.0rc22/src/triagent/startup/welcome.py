"""Welcome flow and prerequisite checks for triagent.

This module provides the startup welcome banner and prerequisite checking
functionality including Azure CLI, login status, AD group membership, and
token availability checks.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from rich.console import Console
from rich.panel import Panel

if TYPE_CHECKING:
    pass

# Constants
MAC_REQUEST_URL = "https://mac.us.deloitte.com/home.jsf"
AD_GROUP_NAME = "SG-US-Audit Cortex AME Reader Access"


@dataclass
class PrerequisiteCheck:
    """Result of a single prerequisite check."""

    name: str
    passed: bool
    status_message: str
    error_message: str | None = None
    help_url: str | None = None
    help_instructions: list[str] | None = None


@dataclass
class PrerequisiteReport:
    """Complete prerequisite check report."""

    checks: list[PrerequisiteCheck] = field(default_factory=list)
    can_proceed: bool = True
    authentication_mode: str = "none"  # "azure_cli_token" | "api_key" | "none"


def display_welcome_banner(console: Console) -> None:
    """Display welcome banner with mascot.

    Shows:
    - Bot mascot ASCII art
    - Triagent title with version
    - Current working directory

    Args:
        console: Rich console for output
    """
    from triagent import __version__
    from triagent.ui.banner import display_banner

    display_banner(console, __version__)


def display_prerequisite_results(
    console: Console,
    report: PrerequisiteReport,
) -> None:
    """Display prerequisite check results with Rich formatting.

    Shows:
    - Green OK for passed checks
    - Yellow WARN for non-critical issues
    - Red FAIL for blocking issues

    Args:
        console: Rich console for output
        report: Prerequisite report with all check results
    """
    console.print()
    console.print("[dim]Checking prerequisites...[/dim]")
    console.print()

    for check in report.checks:
        if check.passed:
            icon = "[green]OK[/green]"
        else:
            icon = "[red]FAIL[/red]"

        console.print(f"  {icon}   {check.name}: {check.status_message}")

        # Show help instructions for failures
        if not check.passed and check.help_instructions:
            for instruction in check.help_instructions:
                console.print(f"        [dim]{instruction}[/dim]")
            if check.help_url:
                console.print(f"        [blue]{check.help_url}[/blue]")


def display_access_denied_panel(
    console: Console,
    group_name: str = AD_GROUP_NAME,
    mac_url: str = MAC_REQUEST_URL,
) -> None:
    """Display prominent access denied panel with MAC request instructions.

    Shows a red-bordered panel with:
    - Required group name
    - MAC URL
    - Step-by-step navigation instructions
    - Alternative /init option

    Args:
        console: Rich console for output
        group_name: Name of required AD group
        mac_url: URL for access request portal
    """
    content = (
        f"[bold red]ACCESS DENIED[/bold red]\n\n"
        f"You are not a member of the required AD group:\n"
        f"[bold]{group_name}[/bold]\n\n"
        f"[bold]Request access:[/bold]\n"
        f"  1. Go to: [blue]{mac_url}[/blue]\n"
        f"  2. Click 'Access Requests'\n"
        f"  3. Search for '{group_name}'\n"
        f"  4. Submit request\n\n"
        f"[dim]Alternative:[/dim] Run [cyan]/init[/cyan] to configure API keys manually"
    )

    console.print()
    console.print(
        Panel(
            content,
            border_style="red",
            title="[red]Action Required[/red]",
        )
    )


def display_ready_message(console: Console) -> None:
    """Display final ready message.

    Args:
        console: Rich console for output
    """
    console.print()
    console.print("[green]Ready![/green] Type [cyan]/help[/cyan] for commands.")
    console.print()


async def run_prerequisite_checks(console: Console) -> PrerequisiteReport:
    """Run all prerequisite checks and return consolidated report.

    Checks run in order:
    1. Azure CLI installation
    2. Azure login status
    3. AD group membership
    4. Token availability

    Args:
        console: Rich console for output (used for any interactive prompts)

    Returns:
        PrerequisiteReport with all check results and authentication mode decision
    """
    from triagent.security.azure_auth import (
        check_azure_cli_installed,
        check_azure_login_status,
        get_last_token_error,
        is_token_valid,
    )
    from triagent.security.group_membership import (
        MembershipStatus,
        check_group_membership,
    )

    checks: list[PrerequisiteCheck] = []
    auth_mode = "none"

    # Check 1: Azure CLI installed
    cli_installed, cli_version = check_azure_cli_installed()
    checks.append(
        PrerequisiteCheck(
            name="Azure CLI",
            passed=cli_installed,
            status_message=f"Installed ({cli_version})" if cli_installed else "Not installed",
            error_message=None if cli_installed else "Azure CLI required for auto-authentication",
            help_url="https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
            if not cli_installed
            else None,
            help_instructions=[
                "macOS: brew install azure-cli",
                "Windows: Download from https://aka.ms/installazurecliwindows",
                "Linux: curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash",
            ]
            if not cli_installed
            else None,
        )
    )

    if not cli_installed:
        # Can still proceed with /init for API key
        return PrerequisiteReport(
            checks=checks,
            can_proceed=True,
            authentication_mode="api_key",
        )

    # Check 2: Azure login status
    logged_in, user_email = check_azure_login_status()
    checks.append(
        PrerequisiteCheck(
            name="Azure Login",
            passed=logged_in,
            status_message=(user_email or "Logged in") if logged_in else "Not logged in",
            error_message=None if logged_in else "Run 'az login' to authenticate",
            help_instructions=["Run: az login"] if not logged_in else None,
        )
    )

    if not logged_in:
        return PrerequisiteReport(
            checks=checks,
            can_proceed=True,
            authentication_mode="api_key",
        )

    # Check 3: AD Group membership
    membership = check_group_membership()
    is_member = membership.status == MembershipStatus.MEMBER

    # Determine status message based on membership status
    if is_member:
        group_status = AD_GROUP_NAME
    elif membership.status == MembershipStatus.GROUP_NOT_FOUND:
        group_status = "Group not found"
    elif membership.status == MembershipStatus.USER_NOT_FOUND:
        group_status = "User not found"
    elif membership.status == MembershipStatus.ERROR:
        group_status = "Check failed"
    else:
        group_status = "Not a member"

    checks.append(
        PrerequisiteCheck(
            name="AD Group",
            passed=is_member,
            status_message=group_status,
            error_message=membership.error_message if not is_member else None,
            help_url=MAC_REQUEST_URL if not is_member else None,
            help_instructions=[
                "Navigate to: Access Requests",
                f"Search for: {AD_GROUP_NAME}",
                "Submit access request",
            ]
            if not is_member
            else None,
        )
    )

    if not is_member:
        return PrerequisiteReport(
            checks=checks,
            can_proceed=True,
            authentication_mode="api_key",
        )

    # Check 4: Token availability
    token_valid = is_token_valid()
    token_error = get_last_token_error() if not token_valid else None
    checks.append(
        PrerequisiteCheck(
            name="Authentication",
            passed=token_valid,
            status_message="Token acquired" if token_valid else f"Token error: {token_error or 'Unknown'}",
            error_message=token_error,
        )
    )

    auth_mode = "azure_cli_token" if token_valid else "api_key"

    return PrerequisiteReport(
        checks=checks,
        can_proceed=True,
        authentication_mode=auth_mode,
    )
