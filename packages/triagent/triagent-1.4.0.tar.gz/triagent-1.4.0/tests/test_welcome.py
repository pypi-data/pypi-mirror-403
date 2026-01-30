"""Tests for welcome flow and prerequisite checks."""

from __future__ import annotations

from io import StringIO
from unittest.mock import patch

import pytest
from rich.console import Console

from triagent.security.group_membership import MembershipStatus
from triagent.startup.welcome import (
    AD_GROUP_NAME,
    MAC_REQUEST_URL,
    PrerequisiteCheck,
    PrerequisiteReport,
    display_access_denied_panel,
    display_prerequisite_results,
    display_ready_message,
    display_welcome_banner,
    run_prerequisite_checks,
)


class TestPrerequisiteCheck:
    """Tests for PrerequisiteCheck dataclass."""

    def test_default_values(self) -> None:
        """Test default values for optional fields."""
        check = PrerequisiteCheck(
            name="Test Check",
            passed=True,
            status_message="All good",
        )
        assert check.error_message is None
        assert check.help_url is None
        assert check.help_instructions is None

    def test_all_fields(self) -> None:
        """Test all fields can be set."""
        check = PrerequisiteCheck(
            name="Test Check",
            passed=False,
            status_message="Failed",
            error_message="Something went wrong",
            help_url="https://example.com/help",
            help_instructions=["Step 1", "Step 2"],
        )
        assert check.name == "Test Check"
        assert check.passed is False
        assert check.status_message == "Failed"
        assert check.error_message == "Something went wrong"
        assert check.help_url == "https://example.com/help"
        assert check.help_instructions == ["Step 1", "Step 2"]


class TestPrerequisiteReport:
    """Tests for PrerequisiteReport dataclass."""

    def test_default_values(self) -> None:
        """Test default values."""
        report = PrerequisiteReport()
        assert report.checks == []
        assert report.can_proceed is True
        assert report.authentication_mode == "none"

    def test_with_checks(self) -> None:
        """Test report with checks."""
        checks = [
            PrerequisiteCheck(name="Check 1", passed=True, status_message="OK"),
            PrerequisiteCheck(name="Check 2", passed=False, status_message="Failed"),
        ]
        report = PrerequisiteReport(
            checks=checks,
            can_proceed=True,
            authentication_mode="azure_cli_token",
        )
        assert len(report.checks) == 2
        assert report.authentication_mode == "azure_cli_token"


class TestDisplayWelcomeBanner:
    """Tests for display_welcome_banner function."""

    def test_banner_displays_version(self) -> None:
        """Test that banner displays version."""
        output = StringIO()
        console = Console(file=output, force_terminal=True, width=80)

        display_welcome_banner(console)

        output_text = output.getvalue()
        assert "Triagent" in output_text
        assert "Azure DevOps AI Assistant" in output_text
        # Version should be displayed
        assert "v" in output_text

    def test_banner_displays_working_directory(self) -> None:
        """Test that banner displays working directory."""
        output = StringIO()
        console = Console(file=output, force_terminal=True, width=80)

        display_welcome_banner(console)

        output_text = output.getvalue()
        # Banner should display current working directory (or ~ prefix)
        # The banner uses os.getcwd() which will show some path
        assert "~" in output_text or "/" in output_text


class TestDisplayPrerequisiteResults:
    """Tests for display_prerequisite_results function."""

    def test_displays_passed_check(self) -> None:
        """Test display of passed check."""
        output = StringIO()
        console = Console(file=output, force_terminal=True, width=80)

        report = PrerequisiteReport(
            checks=[
                PrerequisiteCheck(
                    name="Azure CLI",
                    passed=True,
                    status_message="Installed (2.81.0)",
                )
            ]
        )

        display_prerequisite_results(console, report)

        output_text = output.getvalue()
        assert "OK" in output_text
        assert "Azure CLI" in output_text
        assert "Installed" in output_text

    def test_displays_failed_check_with_help(self) -> None:
        """Test display of failed check with help instructions."""
        output = StringIO()
        console = Console(file=output, force_terminal=True, width=80)

        report = PrerequisiteReport(
            checks=[
                PrerequisiteCheck(
                    name="Azure CLI",
                    passed=False,
                    status_message="Not installed",
                    help_instructions=["Install with: brew install azure-cli"],
                    help_url="https://docs.microsoft.com/en-us/cli/azure/install-azure-cli",
                )
            ]
        )

        display_prerequisite_results(console, report)

        output_text = output.getvalue()
        assert "FAIL" in output_text
        assert "Azure CLI" in output_text
        assert "Not installed" in output_text
        # Help instructions should be displayed
        assert "brew install" in output_text


class TestDisplayAccessDeniedPanel:
    """Tests for display_access_denied_panel function."""

    def test_displays_group_name(self) -> None:
        """Test that panel displays group name."""
        output = StringIO()
        console = Console(file=output, force_terminal=True, width=80)

        display_access_denied_panel(console)

        output_text = output.getvalue()
        assert AD_GROUP_NAME in output_text

    def test_displays_mac_url(self) -> None:
        """Test that panel displays MAC URL."""
        output = StringIO()
        console = Console(file=output, force_terminal=True, width=80)

        display_access_denied_panel(console)

        output_text = output.getvalue()
        assert MAC_REQUEST_URL in output_text

    def test_displays_access_denied_header(self) -> None:
        """Test that panel displays ACCESS DENIED header."""
        output = StringIO()
        console = Console(file=output, force_terminal=True, width=80)

        display_access_denied_panel(console)

        output_text = output.getvalue()
        assert "ACCESS DENIED" in output_text

    def test_custom_group_name(self) -> None:
        """Test panel with custom group name."""
        output = StringIO()
        console = Console(file=output, force_terminal=True, width=80)

        custom_group = "Custom-AD-Group"
        display_access_denied_panel(console, group_name=custom_group)

        output_text = output.getvalue()
        assert custom_group in output_text


class TestDisplayReadyMessage:
    """Tests for display_ready_message function."""

    def test_displays_ready_and_help(self) -> None:
        """Test that ready message is displayed."""
        output = StringIO()
        console = Console(file=output, force_terminal=True, width=80, color_system=None)

        display_ready_message(console)

        output_text = output.getvalue()
        # Check for key words (Rich may format them with escape codes)
        assert "Ready" in output_text or "ready" in output_text.lower()
        assert "help" in output_text.lower()


class TestRunPrerequisiteChecks:
    """Tests for run_prerequisite_checks function."""

    @pytest.mark.asyncio
    async def test_all_checks_pass(self) -> None:
        """Test when all prerequisite checks pass."""
        from triagent.security.group_membership import GroupMembershipResult

        mock_membership_result = GroupMembershipResult(
            status=MembershipStatus.MEMBER,
            group_name=AD_GROUP_NAME,
            group_id="group-123",
            user_id="user-456",
        )

        with (
            patch(
                "triagent.security.azure_auth.check_azure_cli_installed",
                return_value=(True, "2.81.0"),
            ),
            patch(
                "triagent.security.azure_auth.check_azure_login_status",
                return_value=(True, "user@example.com"),
            ),
            patch(
                "triagent.security.group_membership.check_group_membership",
                return_value=mock_membership_result,
            ),
            patch(
                "triagent.security.azure_auth.is_token_valid",
                return_value=True,
            ),
        ):
            output = StringIO()
            console = Console(file=output, force_terminal=True, width=80)

            report = await run_prerequisite_checks(console)

            assert report.can_proceed is True
            assert report.authentication_mode == "azure_cli_token"
            assert len(report.checks) == 4
            assert all(c.passed for c in report.checks)

    @pytest.mark.asyncio
    async def test_cli_not_installed(self) -> None:
        """Test when Azure CLI is not installed."""
        with patch(
            "triagent.security.azure_auth.check_azure_cli_installed",
            return_value=(False, None),
        ):
            output = StringIO()
            console = Console(file=output, force_terminal=True, width=80)

            report = await run_prerequisite_checks(console)

            assert report.can_proceed is True
            assert report.authentication_mode == "api_key"
            # Only Azure CLI check should be present
            assert len(report.checks) == 1
            assert report.checks[0].name == "Azure CLI"
            assert report.checks[0].passed is False

    @pytest.mark.asyncio
    async def test_not_logged_in(self) -> None:
        """Test when user is not logged in."""
        with (
            patch(
                "triagent.security.azure_auth.check_azure_cli_installed",
                return_value=(True, "2.81.0"),
            ),
            patch(
                "triagent.security.azure_auth.check_azure_login_status",
                return_value=(False, None),
            ),
        ):
            output = StringIO()
            console = Console(file=output, force_terminal=True, width=80)

            report = await run_prerequisite_checks(console)

            assert report.can_proceed is True
            assert report.authentication_mode == "api_key"
            assert len(report.checks) == 2
            assert report.checks[0].passed is True  # CLI installed
            assert report.checks[1].passed is False  # Not logged in

    @pytest.mark.asyncio
    async def test_not_in_group(self) -> None:
        """Test when user is not in AD group."""
        from triagent.security.group_membership import GroupMembershipResult

        mock_membership_result = GroupMembershipResult(
            status=MembershipStatus.NOT_MEMBER,
            group_name=AD_GROUP_NAME,
            error_message="Not a member",
        )

        with (
            patch(
                "triagent.security.azure_auth.check_azure_cli_installed",
                return_value=(True, "2.81.0"),
            ),
            patch(
                "triagent.security.azure_auth.check_azure_login_status",
                return_value=(True, "user@example.com"),
            ),
            patch(
                "triagent.security.group_membership.check_group_membership",
                return_value=mock_membership_result,
            ),
        ):
            output = StringIO()
            console = Console(file=output, force_terminal=True, width=80)

            report = await run_prerequisite_checks(console)

            assert report.can_proceed is True
            assert report.authentication_mode == "api_key"
            assert len(report.checks) == 3
            # AD Group check should fail
            ad_check = next(c for c in report.checks if c.name == "AD Group")
            assert ad_check.passed is False

    @pytest.mark.asyncio
    async def test_token_unavailable(self) -> None:
        """Test when token cannot be acquired."""
        from triagent.security.group_membership import GroupMembershipResult

        mock_membership_result = GroupMembershipResult(
            status=MembershipStatus.MEMBER,
            group_name=AD_GROUP_NAME,
            group_id="group-123",
            user_id="user-456",
        )

        with (
            patch(
                "triagent.security.azure_auth.check_azure_cli_installed",
                return_value=(True, "2.81.0"),
            ),
            patch(
                "triagent.security.azure_auth.check_azure_login_status",
                return_value=(True, "user@example.com"),
            ),
            patch(
                "triagent.security.group_membership.check_group_membership",
                return_value=mock_membership_result,
            ),
            patch(
                "triagent.security.azure_auth.is_token_valid",
                return_value=False,
            ),
        ):
            output = StringIO()
            console = Console(file=output, force_terminal=True, width=80)

            report = await run_prerequisite_checks(console)

            # Still can proceed with api_key
            assert report.can_proceed is True
            assert report.authentication_mode == "api_key"
            # Token check should be present and failed
            auth_check = next(c for c in report.checks if c.name == "Authentication")
            assert auth_check.passed is False


class TestConstants:
    """Tests for module constants."""

    def test_ad_group_name(self) -> None:
        """Test AD group name constant."""
        assert AD_GROUP_NAME == "SG-US-Audit Cortex AME Reader Access"

    def test_mac_request_url(self) -> None:
        """Test MAC request URL constant."""
        assert MAC_REQUEST_URL == "https://mac.us.deloitte.com/home.jsf"
