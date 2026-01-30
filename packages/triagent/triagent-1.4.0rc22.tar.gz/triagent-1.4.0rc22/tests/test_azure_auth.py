"""Tests for Azure CLI authentication module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from triagent.security.azure_auth import (
    COGNITIVE_SERVICES_SCOPE,
    check_azure_cli_installed,
    check_azure_login_status,
    get_azure_cli_token,
    is_token_valid,
    run_azure_login,
)


class TestCheckAzureCliInstalled:
    """Tests for check_azure_cli_installed function."""

    def test_cli_installed(self) -> None:
        """Test when Azure CLI is installed."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout='azure-cli                         2.81.0\n\ncore                              2.81.0',
                stderr="",
            )

            installed, version = check_azure_cli_installed()

            assert installed is True
            assert version == "2.81.0"

    def test_cli_not_installed(self) -> None:
        """Test when Azure CLI is not installed."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("az not found")

            installed, version = check_azure_cli_installed()

            assert installed is False
            assert version is None

    def test_cli_returns_error(self) -> None:
        """Test when Azure CLI returns an error."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout="",
                stderr="error",
            )

            installed, version = check_azure_cli_installed()

            assert installed is False
            assert version is None

    def test_cli_version_parsing_malformed_output(self) -> None:
        """Test version parsing with malformed output."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="some unexpected output",
                stderr="",
            )

            installed, version = check_azure_cli_installed()

            assert installed is True
            assert version == "unknown"


class TestCheckAzureLoginStatus:
    """Tests for check_azure_login_status function."""

    def test_user_logged_in(self) -> None:
        """Test when user is logged in."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="user@example.com\n",
                stderr="",
            )

            logged_in, user_email = check_azure_login_status()

            assert logged_in is True
            assert user_email == "user@example.com"

    def test_user_not_logged_in(self) -> None:
        """Test when user is not logged in."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout="",
                stderr="Please run 'az login'",
            )

            logged_in, user_email = check_azure_login_status()

            assert logged_in is False
            assert user_email is None

    def test_cli_not_installed(self) -> None:
        """Test when Azure CLI is not installed."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("az not found")

            logged_in, user_email = check_azure_login_status()

            assert logged_in is False
            assert user_email is None


class TestRunAzureLogin:
    """Tests for run_azure_login function."""

    def test_login_success(self) -> None:
        """Test successful Azure login."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            result = run_azure_login()

            assert result is True
            mock_run.assert_called_once_with(["az", "login"], check=False)

    def test_login_failure(self) -> None:
        """Test failed Azure login."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1)

            result = run_azure_login()

            assert result is False

    def test_cli_not_installed(self) -> None:
        """Test when Azure CLI is not installed."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("az not found")

            result = run_azure_login()

            assert result is False

    def test_other_exception(self) -> None:
        """Test handling of unexpected exceptions."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = Exception("Unexpected error")

            result = run_azure_login()

            assert result is False


class TestGetAzureCliToken:
    """Tests for get_azure_cli_token function."""

    def test_token_acquired_successfully(self) -> None:
        """Test successful token acquisition."""
        mock_token = MagicMock()
        mock_token.token = "test-token-123"

        mock_credential_class = MagicMock()
        mock_credential_class.return_value.get_token.return_value = mock_token

        mock_azure_identity = MagicMock()
        mock_azure_identity.AzureCliCredential = mock_credential_class
        mock_azure_identity.CredentialUnavailableError = Exception

        with patch.dict("sys.modules", {"azure.identity": mock_azure_identity}):
            token = get_azure_cli_token()

            assert token == "test-token-123"
            mock_credential_class.return_value.get_token.assert_called_once_with(
                COGNITIVE_SERVICES_SCOPE
            )

    def test_token_with_custom_scope(self) -> None:
        """Test token acquisition with custom scope."""
        mock_token = MagicMock()
        mock_token.token = "custom-scope-token"

        mock_credential_class = MagicMock()
        mock_credential_class.return_value.get_token.return_value = mock_token

        mock_azure_identity = MagicMock()
        mock_azure_identity.AzureCliCredential = mock_credential_class
        mock_azure_identity.CredentialUnavailableError = Exception

        with patch.dict("sys.modules", {"azure.identity": mock_azure_identity}):
            custom_scope = "https://custom.azure.com/.default"
            token = get_azure_cli_token(scope=custom_scope)

            assert token == "custom-scope-token"
            mock_credential_class.return_value.get_token.assert_called_once_with(
                custom_scope
            )

    def test_credential_unavailable(self) -> None:
        """Test when credential is unavailable."""

        class MockCredentialUnavailableError(Exception):
            """Mock exception for credential unavailable."""

            pass

        mock_credential_class = MagicMock()
        mock_credential_class.return_value.get_token.side_effect = (
            MockCredentialUnavailableError("Azure CLI not logged in")
        )

        mock_azure_identity = MagicMock()
        mock_azure_identity.AzureCliCredential = mock_credential_class
        mock_azure_identity.CredentialUnavailableError = MockCredentialUnavailableError

        with patch.dict("sys.modules", {"azure.identity": mock_azure_identity}):
            token = get_azure_cli_token()

            assert token is None

    def test_import_error(self) -> None:
        """Test when azure-identity is not installed."""
        # Remove azure.identity from sys.modules to simulate it not being installed
        with patch.dict("sys.modules", {"azure.identity": None}):
            token = get_azure_cli_token()

            assert token is None

    def test_other_exception(self) -> None:
        """Test handling of unexpected exceptions."""
        mock_credential_class = MagicMock()
        mock_credential_class.return_value.get_token.side_effect = Exception(
            "Unexpected error"
        )

        mock_azure_identity = MagicMock()
        mock_azure_identity.AzureCliCredential = mock_credential_class
        mock_azure_identity.CredentialUnavailableError = Exception

        with patch.dict("sys.modules", {"azure.identity": mock_azure_identity}):
            token = get_azure_cli_token()

            assert token is None


class TestIsTokenValid:
    """Tests for is_token_valid function."""

    def test_token_is_valid(self) -> None:
        """Test when token is valid and can be acquired."""
        mock_token = MagicMock()
        mock_token.token = "valid-token"

        mock_credential_class = MagicMock()
        mock_credential_class.return_value.get_token.return_value = mock_token

        mock_azure_identity = MagicMock()
        mock_azure_identity.AzureCliCredential = mock_credential_class
        mock_azure_identity.CredentialUnavailableError = Exception

        with patch.dict("sys.modules", {"azure.identity": mock_azure_identity}):
            is_valid = is_token_valid()

            assert is_valid is True

    def test_token_is_invalid(self) -> None:
        """Test when token cannot be acquired."""

        class MockCredentialUnavailableError(Exception):
            """Mock exception for credential unavailable."""

            pass

        mock_credential_class = MagicMock()
        mock_credential_class.return_value.get_token.side_effect = (
            MockCredentialUnavailableError("Azure CLI not logged in")
        )

        mock_azure_identity = MagicMock()
        mock_azure_identity.AzureCliCredential = mock_credential_class
        mock_azure_identity.CredentialUnavailableError = MockCredentialUnavailableError

        with patch.dict("sys.modules", {"azure.identity": mock_azure_identity}):
            is_valid = is_token_valid()

            assert is_valid is False

    def test_token_valid_with_custom_scope(self) -> None:
        """Test token validity check with custom scope."""
        mock_token = MagicMock()
        mock_token.token = "custom-scope-token"

        mock_credential_class = MagicMock()
        mock_credential_class.return_value.get_token.return_value = mock_token

        mock_azure_identity = MagicMock()
        mock_azure_identity.AzureCliCredential = mock_credential_class
        mock_azure_identity.CredentialUnavailableError = Exception

        with patch.dict("sys.modules", {"azure.identity": mock_azure_identity}):
            custom_scope = "https://custom.azure.com/.default"
            is_valid = is_token_valid(scope=custom_scope)

            assert is_valid is True


class TestCognitiveServicesScope:
    """Tests for COGNITIVE_SERVICES_SCOPE constant."""

    def test_scope_value(self) -> None:
        """Test the cognitive services scope value."""
        assert COGNITIVE_SERVICES_SCOPE == "https://cognitiveservices.azure.com/.default"
