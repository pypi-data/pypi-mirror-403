"""Shared test fixtures for isolated testing."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

if TYPE_CHECKING:
    from collections.abc import Generator

    from triagent.config import ConfigManager


@pytest.fixture(autouse=True, scope="function")
def restore_encrypted_cache() -> Generator[None, None, None]:
    """Restore encrypted skills cache after each test.

    This ensures tests that call clear_cache() don't affect other tests.
    The cache is saved before each test and restored after.
    """
    from triagent.skills import encrypted_loader

    # Save current cache state
    saved_decrypted = encrypted_loader._decrypted_cache
    saved_corp_info = encrypted_loader._corporate_info_cache

    yield

    # Restore cache state after test
    encrypted_loader._decrypted_cache = saved_decrypted
    encrypted_loader._corporate_info_cache = saved_corp_info


@pytest.fixture
def isolated_config_dir() -> Generator[Path, None, None]:
    """Provide isolated temporary config directory.

    Yields:
        Path to temporary .triagent config directory
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir) / ".triagent"
        config_dir.mkdir(parents=True)
        yield config_dir


@pytest.fixture
def clean_environment(monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    """Clean environment without any triagent config.

    Removes sensitive environment variables that might interfere with tests.

    Yields:
        None (context manager)
    """
    # Remove any existing triagent env vars
    env_vars_to_clear = [
        "ANTHROPIC_API_KEY",
        "ANTHROPIC_FOUNDRY_API_KEY",
        "CLAUDE_CODE_USE_FOUNDRY",
        "ANTHROPIC_FOUNDRY_RESOURCE",
        "ANTHROPIC_BASE_URL",
        "ANTHROPIC_AUTH_TOKEN",
        "ADO_PAT",
        "AZURE_DEVOPS_ORG",
        "AZURE_DEVOPS_PROJECT",
    ]
    for var in env_vars_to_clear:
        monkeypatch.delenv(var, raising=False)
    yield


@pytest.fixture
def mock_azure_cli() -> Generator[MagicMock, None, None]:
    """Mock Azure CLI for testing without real Azure.

    Yields:
        Mock subprocess.run function
    """
    with patch("subprocess.run") as mock_run:
        # Default: Azure CLI installed and authenticated
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='{"version": "2.60.0"}',
            stderr="",
        )
        yield mock_run


@pytest.fixture
def mock_azure_cli_not_installed() -> Generator[MagicMock, None, None]:
    """Mock Azure CLI as not installed.

    Yields:
        Mock subprocess.run function that simulates missing Azure CLI
    """
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = FileNotFoundError("az not found")
        yield mock_run


@pytest.fixture
def temp_home_dir(
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[Path, None, None]:
    """Create a temporary home directory for testing.

    This isolates tests from the user's actual home directory.

    Yields:
        Path to temporary home directory
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        home_dir = Path(tmpdir)
        monkeypatch.setenv("HOME", str(home_dir))
        monkeypatch.setenv("USERPROFILE", str(home_dir))  # Windows
        yield home_dir


@pytest.fixture
def clean_env_preserve_home(
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[None, None, None]:
    """Clear environment but preserve home directory variables.

    This fixture clears all environment variables except those needed
    for Path.home() to work (HOME on macOS/Linux, USERPROFILE on Windows).

    Yields:
        None (context manager)
    """
    # Save home dir vars before clearing
    home = os.environ.get("HOME")
    userprofile = os.environ.get("USERPROFILE")

    # Clear all env vars
    for key in list(os.environ.keys()):
        monkeypatch.delenv(key, raising=False)

    # Restore home dir vars (cross-platform)
    if home:
        monkeypatch.setenv("HOME", home)
    if userprofile:
        monkeypatch.setenv("USERPROFILE", userprofile)

    yield


@pytest.fixture
def isolated_config_manager(
    isolated_config_dir: Path,
) -> Generator[ConfigManager, None, None]:
    """Provide an isolated ConfigManager instance.

    Args:
        isolated_config_dir: Temporary config directory fixture

    Yields:
        ConfigManager instance using temporary directory
    """
    from triagent.config import ConfigManager

    manager = ConfigManager(config_dir=isolated_config_dir)
    manager.ensure_dirs()
    yield manager


@pytest.fixture
def mock_skills_directory(tmp_path: Path) -> Path:
    """Create a mock skills directory with test content.

    Creates a complete skill directory structure for testing:
    - Team directories with core and persona skills
    - Persona YAML files
    - Encrypted directory placeholder

    Args:
        tmp_path: Pytest tmp_path fixture

    Returns:
        Path to the skills directory
    """
    skills_dir = tmp_path / "src" / "triagent" / "skills"
    skills_dir.mkdir(parents=True)

    # Create test skill directories for omnia-data team
    team_dir = skills_dir / "omnia-data"
    team_dir.mkdir()

    # Core skills
    core_dir = team_dir / "core"
    core_dir.mkdir()
    (core_dir / "team_context.md").write_text(
        "---\nname: team_context\ndescription: Team context skill\n---\n"
        "# Team Context\nThis is the team context content."
    )
    (core_dir / "telemetry_basics.md").write_text(
        "---\nname: telemetry_basics\ndescription: Telemetry basics\n---\n"
        "# Telemetry\nBasic telemetry instructions."
    )

    # Developer persona skills
    dev_dir = team_dir / "developer"
    dev_dir.mkdir()
    (dev_dir / "code_review.md").write_text(
        "---\nname: code_review\ndescription: Code review skill\n---\n"
        "# Code Review\nCode review guidelines."
    )

    # Support persona skills
    support_dir = team_dir / "support"
    support_dir.mkdir()
    (support_dir / "troubleshooting.md").write_text(
        "---\nname: troubleshooting\ndescription: Troubleshooting skill\n---\n"
        "# Troubleshooting\nTroubleshooting guide."
    )

    # Persona YAML files
    (team_dir / "_persona_developer.yaml").write_text(
        "name: developer\n"
        "display_name: Developer\n"
        "description: Development persona\n"
        "core_skills:\n"
        "  - team_context\n"
        "skills:\n"
        "  - code_review\n"
    )
    (team_dir / "_persona_support.yaml").write_text(
        "name: support\n"
        "display_name: Support\n"
        "description: Support persona\n"
        "core_skills:\n"
        "  - team_context\n"
        "skills:\n"
        "  - troubleshooting\n"
    )

    # Encrypted directory placeholder
    encrypted_dir = skills_dir / "encrypted"
    encrypted_dir.mkdir()
    (encrypted_dir / ".gitkeep").touch()

    return skills_dir


@pytest.fixture
def current_wheel_path() -> Path | None:
    """Get path to most recent wheel in dist/.

    Returns:
        Path to the most recent wheel file, or None if no wheels found
    """
    dist_dir = Path(__file__).parent.parent / "dist"
    if not dist_dir.exists():
        return None
    wheels = list(dist_dir.glob("triagent-*.whl"))
    if not wheels:
        return None
    return max(wheels, key=lambda p: p.stat().st_mtime)


@pytest.fixture
def mock_corporate_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[None, None, None]:
    """Set up mock corporate environment for testing.

    Sets TRIAGENT_CORP_ID to test domain.

    Yields:
        None (context manager)
    """
    monkeypatch.setenv("TRIAGENT_CORP_ID", "test.corporate.domain")
    yield
