"""Tests for Azure AD group membership checking."""

from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, patch

from triagent.security.group_membership import (
    TARGET_GROUP_NAME,
    GroupMembershipResult,
    MembershipStatus,
    check_group_membership,
    clear_cache,
)


class TestMembershipStatus:
    """Tests for MembershipStatus enum."""

    def test_all_statuses_defined(self) -> None:
        """Test all expected statuses are defined."""
        assert MembershipStatus.MEMBER.value == "member"
        assert MembershipStatus.NOT_MEMBER.value == "not_member"
        assert MembershipStatus.CLI_NOT_INSTALLED.value == "cli_not_installed"
        assert MembershipStatus.NOT_LOGGED_IN.value == "not_logged_in"
        assert MembershipStatus.GROUP_NOT_FOUND.value == "group_not_found"
        assert MembershipStatus.USER_NOT_FOUND.value == "user_not_found"
        assert MembershipStatus.ERROR.value == "error"


class TestGroupMembershipResult:
    """Tests for GroupMembershipResult dataclass."""

    def test_default_values(self) -> None:
        """Test default values for optional fields."""
        result = GroupMembershipResult(
            status=MembershipStatus.MEMBER,
            group_name="test-group",
        )
        assert result.group_id is None
        assert result.user_id is None
        assert result.error_message is None

    def test_all_fields(self) -> None:
        """Test all fields can be set."""
        result = GroupMembershipResult(
            status=MembershipStatus.MEMBER,
            group_name="test-group",
            group_id="group-123",
            user_id="user-456",
            error_message=None,
        )
        assert result.status == MembershipStatus.MEMBER
        assert result.group_name == "test-group"
        assert result.group_id == "group-123"
        assert result.user_id == "user-456"


class TestCheckGroupMembership:
    """Tests for check_group_membership function."""

    def setup_method(self) -> None:
        """Clear cache before each test."""
        clear_cache()

    def teardown_method(self) -> None:
        """Clear cache after each test."""
        clear_cache()

    def test_azure_cli_not_installed(self) -> None:
        """Test handling when Azure CLI is not installed."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("az not found")

            result = check_group_membership(use_cache=False)

            assert result.status == MembershipStatus.CLI_NOT_INSTALLED
            assert "Azure CLI is not installed" in (result.error_message or "")

    def test_azure_cli_not_logged_in(self) -> None:
        """Test handling when user is not logged in."""
        with patch("subprocess.run") as mock_run:
            # First call - az account show fails (not logged in)
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout="",
                stderr="Please run 'az login'",
            )

            result = check_group_membership(use_cache=False)

            assert result.status == MembershipStatus.NOT_LOGGED_IN
            assert "az login" in (result.error_message or "").lower()

    def test_user_is_member(self) -> None:
        """Test successful group membership check."""
        with patch("subprocess.run") as mock_run:
            def mock_subprocess(args: list[str], **kwargs) -> MagicMock:
                cmd = " ".join(args)
                if "az account show" in cmd:
                    return MagicMock(returncode=0, stdout="user@example.com\n", stderr="")
                elif "az ad signed-in-user show" in cmd:
                    return MagicMock(returncode=0, stdout="user-id-123\n", stderr="")
                elif "az ad group show" in cmd:
                    return MagicMock(returncode=0, stdout="group-id-456\n", stderr="")
                elif "az ad group member check" in cmd:
                    return MagicMock(returncode=0, stdout="true\n", stderr="")
                return MagicMock(returncode=1, stdout="", stderr="Unknown command")

            mock_run.side_effect = mock_subprocess

            result = check_group_membership(use_cache=False)

            assert result.status == MembershipStatus.MEMBER
            assert result.group_name == TARGET_GROUP_NAME
            assert result.group_id == "group-id-456"
            assert result.user_id == "user-id-123"

    def test_user_is_not_member(self) -> None:
        """Test when user is not a member of the group."""
        with patch("subprocess.run") as mock_run:
            def mock_subprocess(args: list[str], **kwargs) -> MagicMock:
                cmd = " ".join(args)
                if "az account show" in cmd:
                    return MagicMock(returncode=0, stdout="user@example.com\n", stderr="")
                elif "az ad signed-in-user show" in cmd:
                    return MagicMock(returncode=0, stdout="user-id-123\n", stderr="")
                elif "az ad group show" in cmd:
                    return MagicMock(returncode=0, stdout="group-id-456\n", stderr="")
                elif "az ad group member check" in cmd:
                    return MagicMock(returncode=0, stdout="false\n", stderr="")
                return MagicMock(returncode=1, stdout="", stderr="Unknown command")

            mock_run.side_effect = mock_subprocess

            result = check_group_membership(use_cache=False)

            assert result.status == MembershipStatus.NOT_MEMBER

    def test_group_not_found(self) -> None:
        """Test when AD group does not exist."""
        with patch("subprocess.run") as mock_run:
            def mock_subprocess(args: list[str], **kwargs) -> MagicMock:
                cmd = " ".join(args)
                if "az account show" in cmd:
                    return MagicMock(returncode=0, stdout="user@example.com\n", stderr="")
                elif "az ad signed-in-user show" in cmd:
                    return MagicMock(returncode=0, stdout="user-id-123\n", stderr="")
                elif "az ad group show" in cmd:
                    return MagicMock(returncode=1, stdout="", stderr="Resource not found")
                return MagicMock(returncode=1, stdout="", stderr="Unknown command")

            mock_run.side_effect = mock_subprocess

            result = check_group_membership(use_cache=False)

            assert result.status == MembershipStatus.GROUP_NOT_FOUND

    def test_user_not_found(self) -> None:
        """Test when signed-in user cannot be found in AD."""
        with patch("subprocess.run") as mock_run:
            def mock_subprocess(args: list[str], **kwargs) -> MagicMock:
                cmd = " ".join(args)
                if "az account show" in cmd:
                    return MagicMock(returncode=0, stdout="user@example.com\n", stderr="")
                elif "az ad signed-in-user show" in cmd:
                    return MagicMock(returncode=1, stdout="", stderr="User not found")
                return MagicMock(returncode=1, stdout="", stderr="Unknown command")

            mock_run.side_effect = mock_subprocess

            result = check_group_membership(use_cache=False)

            assert result.status == MembershipStatus.USER_NOT_FOUND

    def test_caching_enabled(self) -> None:
        """Test that caching works correctly."""
        call_count = 0

        with patch("subprocess.run") as mock_run:
            def mock_subprocess(args: list[str], **kwargs) -> MagicMock:
                nonlocal call_count
                call_count += 1
                cmd = " ".join(args)
                if "az account show" in cmd:
                    return MagicMock(returncode=0, stdout="user@example.com\n", stderr="")
                elif "az ad signed-in-user show" in cmd:
                    return MagicMock(returncode=0, stdout="user-id-123\n", stderr="")
                elif "az ad group show" in cmd:
                    return MagicMock(returncode=0, stdout="group-id-456\n", stderr="")
                elif "az ad group member check" in cmd:
                    return MagicMock(returncode=0, stdout="true\n", stderr="")
                return MagicMock(returncode=1, stdout="", stderr="Unknown command")

            mock_run.side_effect = mock_subprocess

            # First call - should execute
            result1 = check_group_membership(use_cache=True)
            first_call_count = call_count

            # Second call - should use cache
            result2 = check_group_membership(use_cache=True)

            assert result1.status == MembershipStatus.MEMBER
            assert result2.status == MembershipStatus.MEMBER
            # Call count should not increase significantly on second call
            assert call_count == first_call_count

    def test_caching_disabled(self) -> None:
        """Test that caching can be disabled."""
        call_count = 0

        with patch("subprocess.run") as mock_run:
            def mock_subprocess(args: list[str], **kwargs) -> MagicMock:
                nonlocal call_count
                call_count += 1
                cmd = " ".join(args)
                if "az account show" in cmd:
                    return MagicMock(returncode=0, stdout="user@example.com\n", stderr="")
                elif "az ad signed-in-user show" in cmd:
                    return MagicMock(returncode=0, stdout="user-id-123\n", stderr="")
                elif "az ad group show" in cmd:
                    return MagicMock(returncode=0, stdout="group-id-456\n", stderr="")
                elif "az ad group member check" in cmd:
                    return MagicMock(returncode=0, stdout="true\n", stderr="")
                return MagicMock(returncode=1, stdout="", stderr="Unknown command")

            mock_run.side_effect = mock_subprocess

            # First call
            result1 = check_group_membership(use_cache=False)
            first_call_count = call_count

            # Second call - should not use cache
            result2 = check_group_membership(use_cache=False)

            assert result1.status == MembershipStatus.MEMBER
            assert result2.status == MembershipStatus.MEMBER
            # Call count should increase on second call
            assert call_count > first_call_count

    def test_custom_group_name(self) -> None:
        """Test checking membership with custom group name."""
        with patch("subprocess.run") as mock_run:
            def mock_subprocess(args: list[str], **kwargs) -> MagicMock:
                cmd = " ".join(args)
                if "az account show" in cmd:
                    return MagicMock(returncode=0, stdout="user@example.com\n", stderr="")
                elif "az ad signed-in-user show" in cmd:
                    return MagicMock(returncode=0, stdout="user-id-123\n", stderr="")
                elif "az ad group show" in cmd:
                    # Check that custom group name is used
                    assert "Custom-Group-Name" in cmd
                    return MagicMock(returncode=0, stdout="group-id-789\n", stderr="")
                elif "az ad group member check" in cmd:
                    return MagicMock(returncode=0, stdout="true\n", stderr="")
                return MagicMock(returncode=1, stdout="", stderr="Unknown command")

            mock_run.side_effect = mock_subprocess

            result = check_group_membership(group_name="Custom-Group-Name", use_cache=False)

            assert result.status == MembershipStatus.MEMBER
            assert result.group_name == "Custom-Group-Name"

    def test_subprocess_timeout(self) -> None:
        """Test handling of subprocess timeout."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("az", 30)

            result = check_group_membership(use_cache=False)

            # Timeout during login check results in NOT_LOGGED_IN status
            # since the _check_az_login_status function returns False on timeout
            assert result.status == MembershipStatus.NOT_LOGGED_IN


class TestClearMembershipCache:
    """Tests for clear_cache function."""

    def test_clear_cache(self) -> None:
        """Test that cache can be cleared."""
        with patch("subprocess.run") as mock_run:
            def mock_subprocess(args: list[str], **kwargs) -> MagicMock:
                cmd = " ".join(args)
                if "az account show" in cmd:
                    return MagicMock(returncode=0, stdout="user@example.com\n", stderr="")
                elif "az ad signed-in-user show" in cmd:
                    return MagicMock(returncode=0, stdout="user-id-123\n", stderr="")
                elif "az ad group show" in cmd:
                    return MagicMock(returncode=0, stdout="group-id-456\n", stderr="")
                elif "az ad group member check" in cmd:
                    return MagicMock(returncode=0, stdout="true\n", stderr="")
                return MagicMock(returncode=1, stdout="", stderr="Unknown command")

            mock_run.side_effect = mock_subprocess

            # First call - populate cache
            check_group_membership(use_cache=True)

            # Clear cache
            clear_cache()

            # Next call should execute fresh (we can verify by changing mock behavior)
            mock_run.side_effect = FileNotFoundError("az not found")
            result = check_group_membership(use_cache=True)

            assert result.status == MembershipStatus.CLI_NOT_INSTALLED
