"""Azure CLI authentication utilities.

This module provides functions for checking Azure CLI installation,
login status, and acquiring tokens for Azure AI Foundry.
"""

from __future__ import annotations

import re
import subprocess
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

# Token scope for Azure AI Foundry / Cognitive Services
COGNITIVE_SERVICES_SCOPE = "https://cognitiveservices.azure.com/.default"

# Module-level variable to capture last token error for debugging
_last_token_error: str | None = None


def check_azure_cli_installed() -> tuple[bool, str | None]:
    """Check if Azure CLI is installed and return version.

    Returns:
        Tuple of (installed: bool, version: str | None)

    Example:
        >>> installed, version = check_azure_cli_installed()
        >>> if installed:
        ...     print(f"Azure CLI {version} is installed")
    """
    try:
        result = subprocess.run(
            ["az", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            # Parse version from output: "azure-cli 2.64.0"
            match = re.search(r"azure-cli\s+(\d+\.\d+\.\d+)", result.stdout)
            version = match.group(1) if match else "unknown"
            return True, version
        return False, None
    except FileNotFoundError:
        return False, None
    except subprocess.TimeoutExpired:
        return False, None
    except Exception:
        return False, None


def check_azure_login_status() -> tuple[bool, str | None]:
    """Check if user is logged into Azure CLI.

    Returns:
        Tuple of (logged_in: bool, user_email: str | None)

    Example:
        >>> logged_in, email = check_azure_login_status()
        >>> if logged_in:
        ...     print(f"Logged in as {email}")
    """
    try:
        result = subprocess.run(
            ["az", "account", "show", "--query", "user.name", "-o", "tsv"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            return True, result.stdout.strip()
        return False, None
    except FileNotFoundError:
        return False, None
    except subprocess.TimeoutExpired:
        return False, None
    except Exception:
        return False, None


def run_azure_login() -> bool:
    """Run az login interactively.

    Executes `az login` which will open a browser for authentication
    or provide a device code for terminal authentication.

    Returns:
        True if login succeeded, False otherwise

    Example:
        >>> if run_azure_login():
        ...     print("Login successful")
    """
    try:
        result = subprocess.run(
            ["az", "login"],
            check=False,
            # Don't capture output - let az login use the terminal
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False
    except Exception:
        return False


def get_azure_cli_token(
    scope: str = COGNITIVE_SERVICES_SCOPE,
) -> str | None:
    """Get Azure AD token using Azure CLI credentials.

    Uses the azure-identity library's AzureCliCredential to acquire
    a token for the specified scope.

    Args:
        scope: Token scope (default: cognitive services)

    Returns:
        Token string if successful, None otherwise

    Example:
        >>> token = get_azure_cli_token()
        >>> if token:
        ...     print("Token acquired successfully")
    """
    global _last_token_error
    _last_token_error = None

    try:
        from azure.identity import AzureCliCredential, CredentialUnavailableError

        credential = AzureCliCredential()
        token = credential.get_token(scope)
        return token.token
    except ImportError:
        _last_token_error = "azure-identity package not installed"
        return None
    except CredentialUnavailableError as e:
        _last_token_error = f"Credential unavailable: {e}"
        return None
    except Exception as e:
        _last_token_error = f"{type(e).__name__}: {e}"
        return None


def get_last_token_error() -> str | None:
    """Get the last token acquisition error for debugging.

    Returns:
        Error message string if last token acquisition failed, None otherwise

    Example:
        >>> if not is_token_valid():
        ...     error = get_last_token_error()
        ...     print(f"Token failed: {error}")
    """
    return _last_token_error


def is_token_valid(scope: str = COGNITIVE_SERVICES_SCOPE) -> bool:
    """Check if Azure CLI token is available and valid.

    Args:
        scope: Token scope to check (default: cognitive services)

    Returns:
        True if token can be acquired, False otherwise

    Example:
        >>> if is_token_valid():
        ...     print("Ready to authenticate")
    """
    return get_azure_cli_token(scope) is not None


def get_token_expiry(scope: str = COGNITIVE_SERVICES_SCOPE) -> int | None:
    """Get token expiry timestamp.

    Args:
        scope: Token scope (default: cognitive services)

    Returns:
        Unix timestamp of token expiry, or None if token unavailable

    Example:
        >>> expiry = get_token_expiry()
        >>> if expiry:
        ...     from datetime import datetime
        ...     print(f"Token expires: {datetime.fromtimestamp(expiry)}")
    """
    try:
        from azure.identity import AzureCliCredential, CredentialUnavailableError

        credential = AzureCliCredential()
        token = credential.get_token(scope)
        return token.expires_on
    except ImportError:
        return None
    except CredentialUnavailableError:
        return None
    except Exception:
        return None
