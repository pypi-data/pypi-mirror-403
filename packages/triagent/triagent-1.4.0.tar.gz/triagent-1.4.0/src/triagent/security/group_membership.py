"""Azure AD group membership verification.

This module provides checking of Azure AD group membership using Azure CLI.
Results are cached for the session to avoid repeated API calls.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

# Target group for access control
TARGET_GROUP_NAME = "SG-US-Audit Cortex AME Reader Access"

# Cache for membership check results
_membership_cache: GroupMembershipResult | None = None


class MembershipStatus(Enum):
    """Status of Azure AD group membership check."""

    MEMBER = "member"  # User is a member of the group
    NOT_MEMBER = "not_member"  # User is NOT a member of the group
    CLI_NOT_INSTALLED = "cli_not_installed"  # Azure CLI not installed
    NOT_LOGGED_IN = "not_logged_in"  # User not logged in to Azure CLI
    GROUP_NOT_FOUND = "group_not_found"  # Group does not exist
    USER_NOT_FOUND = "user_not_found"  # Could not get current user
    ERROR = "error"  # Other error occurred


@dataclass
class GroupMembershipResult:
    """Result of Azure AD group membership check."""

    status: MembershipStatus
    group_name: str
    group_id: str | None = None
    user_id: str | None = None
    error_message: str | None = None

    @property
    def is_member(self) -> bool:
        """Check if user is confirmed member."""
        return self.status == MembershipStatus.MEMBER

    @property
    def is_authorized(self) -> bool:
        """Check if user is authorized (member of required group)."""
        return self.is_member


def _run_az_command(args: list[str], timeout: int = 30) -> tuple[bool, str, str]:
    """Run an Azure CLI command.

    Args:
        args: Command arguments (without 'az' prefix)
        timeout: Command timeout in seconds

    Returns:
        Tuple of (success, stdout, stderr)
    """
    cmd = ["az"] + args
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except FileNotFoundError:
        return False, "", "Azure CLI not installed"
    except subprocess.TimeoutExpired:
        return False, "", f"Command timed out after {timeout}s"
    except Exception as e:
        return False, "", str(e)


def _check_az_login_status() -> tuple[bool, str]:
    """Check if user is logged in to Azure CLI.

    Returns:
        Tuple of (is_logged_in, error_message_or_user_email)
    """
    success, stdout, stderr = _run_az_command(
        ["account", "show", "--query", "user.name", "-o", "tsv"]
    )
    if not success:
        if "Azure CLI not installed" in stderr:
            return False, stderr
        if "Please run 'az login'" in stderr or "AADSTS" in stderr:
            return False, "Not logged in to Azure CLI"
        return False, stderr
    return True, stdout


def _get_current_user_id() -> tuple[str | None, str]:
    """Get the Object ID of the currently signed-in user.

    Returns:
        Tuple of (user_id or None, error_message)
    """
    success, stdout, stderr = _run_az_command(
        ["ad", "signed-in-user", "show", "--query", "id", "-o", "tsv"]
    )
    if not success:
        return None, stderr or "Failed to get current user"
    return stdout, ""


def _get_group_id(group_name: str) -> tuple[str | None, str]:
    """Get the Object ID of an Azure AD group by display name.

    Args:
        group_name: Display name of the group

    Returns:
        Tuple of (group_id or None, error_message)
    """
    success, stdout, stderr = _run_az_command(
        ["ad", "group", "show", "--group", group_name, "--query", "id", "-o", "tsv"]
    )
    if not success:
        if "Resource" in stderr and "not found" in stderr.lower():
            return None, f"Group not found: {group_name}"
        return None, stderr or f"Failed to find group: {group_name}"
    return stdout, ""


def _check_group_membership(group_id: str, user_id: str) -> tuple[bool | None, str]:
    """Check if a user is a member of a group.

    Args:
        group_id: Object ID of the group
        user_id: Object ID of the user

    Returns:
        Tuple of (is_member or None on error, error_message)
    """
    success, stdout, stderr = _run_az_command(
        [
            "ad",
            "group",
            "member",
            "check",
            "--group",
            group_id,
            "--member-id",
            user_id,
            "--query",
            "value",
            "-o",
            "tsv",
        ]
    )
    if not success:
        return None, stderr or "Failed to check group membership"

    # Output is 'true' or 'false'
    return stdout.lower() == "true", ""


def check_group_membership(
    group_name: str = TARGET_GROUP_NAME,
    use_cache: bool = True,
) -> GroupMembershipResult:
    """Check if current user is a member of the specified Azure AD group.

    This function checks Azure AD group membership using the Azure CLI.
    Results are cached for the session to avoid repeated API calls.

    Args:
        group_name: Display name of the Azure AD group to check
        use_cache: Whether to use cached result (default True)

    Returns:
        GroupMembershipResult with status and details

    Example:
        >>> result = check_group_membership()
        >>> if result.is_member:
        ...     print("Access granted")
        ... else:
        ...     print(f"Access denied: {result.status.value}")
    """
    global _membership_cache

    # Return cached result if available and requested
    if use_cache and _membership_cache is not None:
        if _membership_cache.group_name == group_name:
            return _membership_cache

    # Check if Azure CLI is installed and user is logged in
    is_logged_in, login_info = _check_az_login_status()
    if not is_logged_in:
        if "not installed" in login_info.lower():
            result = GroupMembershipResult(
                status=MembershipStatus.CLI_NOT_INSTALLED,
                group_name=group_name,
                error_message=(
                    "Azure CLI is not installed. "
                    "Install from: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
                ),
            )
        else:
            result = GroupMembershipResult(
                status=MembershipStatus.NOT_LOGGED_IN,
                group_name=group_name,
                error_message="Please run 'az login' to authenticate with Azure AD.",
            )
        _membership_cache = result
        return result

    # Get current user ID
    user_id, user_error = _get_current_user_id()
    if not user_id:
        result = GroupMembershipResult(
            status=MembershipStatus.USER_NOT_FOUND,
            group_name=group_name,
            error_message=user_error or "Could not determine current user",
        )
        _membership_cache = result
        return result

    # Get group ID
    group_id, group_error = _get_group_id(group_name)
    if not group_id:
        result = GroupMembershipResult(
            status=MembershipStatus.GROUP_NOT_FOUND,
            group_name=group_name,
            user_id=user_id,
            error_message=group_error or f"Group not found: {group_name}",
        )
        _membership_cache = result
        return result

    # Check membership
    is_member, member_error = _check_group_membership(group_id, user_id)
    if is_member is None:
        result = GroupMembershipResult(
            status=MembershipStatus.ERROR,
            group_name=group_name,
            group_id=group_id,
            user_id=user_id,
            error_message=member_error or "Failed to check group membership",
        )
    elif is_member:
        result = GroupMembershipResult(
            status=MembershipStatus.MEMBER,
            group_name=group_name,
            group_id=group_id,
            user_id=user_id,
        )
    else:
        result = GroupMembershipResult(
            status=MembershipStatus.NOT_MEMBER,
            group_name=group_name,
            group_id=group_id,
            user_id=user_id,
            error_message=f"User is not a member of group: {group_name}",
        )

    _membership_cache = result
    return result


def clear_cache() -> None:
    """Clear the membership cache (useful for testing)."""
    global _membership_cache
    _membership_cache = None


def get_cached_result() -> GroupMembershipResult | None:
    """Get the cached membership result without making API calls.

    Returns:
        Cached GroupMembershipResult or None if not cached
    """
    return _membership_cache
