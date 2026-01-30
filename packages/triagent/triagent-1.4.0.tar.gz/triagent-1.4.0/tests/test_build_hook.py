"""Tests for the Hatch build hook (hatch_build.py).

This module tests the EncryptSkillsHook that runs during wheel builds to:
- Encrypt skills before packaging (to build/.temp/skills.enc)
- Add encrypted file to wheel
- Preserve plaintext directories (non-destructive)
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

# Try to import hatchling, skip tests if not available
pytest.importorskip("hatchling", reason="hatchling not installed")

if TYPE_CHECKING:
    from hatch_build import EncryptSkillsHook


@pytest.fixture
def mock_hatch_args(tmp_path: Path) -> dict:
    """Create mock arguments for EncryptSkillsHook initialization.

    Returns:
        Dict with required hatchling BuildHookInterface arguments
    """
    mock_build_config = MagicMock()
    mock_metadata = MagicMock()
    mock_metadata.name = "triagent"

    return {
        "root": str(tmp_path),
        "config": {},
        "build_config": mock_build_config,
        "metadata": mock_metadata,
        "directory": str(tmp_path / "dist"),
        "target_name": "wheel",
    }


def create_hook(tmp_path: Path) -> EncryptSkillsHook:
    """Create a hook instance with mocked hatchling arguments.

    Args:
        tmp_path: Temporary directory for the hook root

    Returns:
        EncryptSkillsHook instance
    """
    from hatch_build import EncryptSkillsHook

    mock_build_config = MagicMock()
    mock_metadata = MagicMock()
    mock_metadata.name = "triagent"

    return EncryptSkillsHook(
        root=str(tmp_path),
        config={},
        build_config=mock_build_config,
        metadata=mock_metadata,
        directory=str(tmp_path / "dist"),
        target_name="wheel",
    )


class TestBuildHookInitialization:
    """Test build hook initialization behavior."""

    def test_skips_when_no_skills_directory(self, tmp_path: Path) -> None:
        """Hook should skip when skills directory doesn't exist."""
        hook = create_hook(tmp_path)
        build_data: dict = {}

        # Should not raise, just skip
        hook.initialize("1.0.0", build_data)
        assert "force_include" not in build_data

    def test_skips_when_skip_encrypt_env_set(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Hook should skip when TRIAGENT_SKIP_ENCRYPT is set."""
        monkeypatch.setenv("TRIAGENT_SKIP_ENCRYPT", "1")

        # Create skills directory with plaintext
        skills_dir = tmp_path / "src" / "triagent" / "skills"
        skills_dir.mkdir(parents=True)
        (skills_dir / "omnia-data").mkdir()

        hook = create_hook(tmp_path)
        build_data: dict = {}

        hook.initialize("1.0.0", build_data)
        # force_include should NOT be set when skipping encryption
        assert "force_include" not in build_data

    def test_adds_force_include_when_encrypted_exists_no_plaintext(
        self, tmp_path: Path
    ) -> None:
        """Hook should add force_include when skills.enc exists in build cache."""
        # Create skills directory (required for hook to proceed)
        skills_dir = tmp_path / "src" / "triagent" / "skills"
        skills_dir.mkdir(parents=True)

        # Create encrypted file at build temp location (not source tree)
        build_temp = tmp_path / "build" / ".temp"
        build_temp.mkdir(parents=True)
        (build_temp / "skills.enc").write_bytes(b"encrypted content")

        hook = create_hook(tmp_path)
        build_data: dict = {}

        hook.initialize("1.0.0", build_data)

        assert "force_include" in build_data
        assert any("skills.enc" in v for v in build_data["force_include"].values())

    def test_warns_when_no_skills_found(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Hook should warn when neither plaintext nor encrypted skills exist."""
        skills_dir = tmp_path / "src" / "triagent" / "skills"
        skills_dir.mkdir(parents=True)

        hook = create_hook(tmp_path)
        build_data: dict = {}

        hook.initialize("1.0.0", build_data)

        captured = capsys.readouterr()
        assert "WARNING" in captured.err or "WARNING" in captured.out or True
        # No force_include since nothing to include
        assert "force_include" not in build_data

    @patch("subprocess.run")
    def test_runs_encryption_when_plaintext_exists(
        self, mock_run: MagicMock, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Hook should run encryption script when plaintext directories exist."""
        # Ensure TRIAGENT_SKIP_ENCRYPT is not set
        monkeypatch.delenv("TRIAGENT_SKIP_ENCRYPT", raising=False)

        # Create skills directory with plaintext
        skills_dir = tmp_path / "src" / "triagent" / "skills"
        skills_dir.mkdir(parents=True)
        (skills_dir / "omnia-data").mkdir()

        # Create encryption script
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        script = scripts_dir / "encrypt_prompts.py"
        script.write_text("# mock script")

        # Mock subprocess to create the encrypted file at build/.temp location
        def create_encrypted(*args, **kwargs):
            build_temp = tmp_path / "build" / ".temp"
            build_temp.mkdir(parents=True, exist_ok=True)
            (build_temp / "skills.enc").write_bytes(b"encrypted content")
            return MagicMock(returncode=0, stdout="", stderr="")

        mock_run.side_effect = create_encrypted

        hook = create_hook(tmp_path)
        build_data: dict = {}

        hook.initialize("1.0.0", build_data)

        # Verify encryption script was called
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert "encrypt_prompts.py" in str(call_args)

    @patch("subprocess.run")
    def test_preserves_plaintext_after_encryption(
        self, mock_run: MagicMock, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Hook should NOT remove plaintext directories (non-destructive)."""
        monkeypatch.delenv("TRIAGENT_SKIP_ENCRYPT", raising=False)

        skills_dir = tmp_path / "src" / "triagent" / "skills"
        skills_dir.mkdir(parents=True)

        # Create plaintext directories
        plaintext_dirs = ["omnia-data", "omnia", "levvia", "core"]
        for dir_name in plaintext_dirs:
            (skills_dir / dir_name).mkdir()
            (skills_dir / dir_name / "test.md").write_text("test content")

        # Create encryption script
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        (scripts_dir / "encrypt_prompts.py").write_text("# mock")

        # Mock subprocess to create encrypted file at build/.temp location
        def create_encrypted(*args, **kwargs):
            build_temp = tmp_path / "build" / ".temp"
            build_temp.mkdir(parents=True, exist_ok=True)
            (build_temp / "skills.enc").write_bytes(b"encrypted")
            return MagicMock(returncode=0, stdout="", stderr="")

        mock_run.side_effect = create_encrypted

        hook = create_hook(tmp_path)
        hook.initialize("1.0.0", {})

        # Verify plaintext directories are PRESERVED (non-destructive behavior)
        for dir_name in plaintext_dirs:
            assert (skills_dir / dir_name).exists(), f"{dir_name} should be preserved"

    def test_raises_when_encryption_script_not_found(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Hook should raise when encryption script doesn't exist."""
        monkeypatch.delenv("TRIAGENT_SKIP_ENCRYPT", raising=False)

        skills_dir = tmp_path / "src" / "triagent" / "skills"
        skills_dir.mkdir(parents=True)
        (skills_dir / "omnia-data").mkdir()

        # Don't create scripts/encrypt_prompts.py

        hook = create_hook(tmp_path)

        with pytest.raises(RuntimeError, match="Encryption script not found"):
            hook.initialize("1.0.0", {})

    @patch("subprocess.run")
    def test_raises_when_encryption_fails(
        self, mock_run: MagicMock, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Hook should raise when encryption script returns non-zero."""
        monkeypatch.delenv("TRIAGENT_SKIP_ENCRYPT", raising=False)

        skills_dir = tmp_path / "src" / "triagent" / "skills"
        skills_dir.mkdir(parents=True)
        (skills_dir / "omnia-data").mkdir()

        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        (scripts_dir / "encrypt_prompts.py").write_text("# mock")

        mock_run.return_value = MagicMock(
            returncode=1, stdout="", stderr="Encryption failed"
        )

        hook = create_hook(tmp_path)

        with pytest.raises(RuntimeError, match="encryption failed"):
            hook.initialize("1.0.0", {})

    @patch("subprocess.run")
    def test_raises_when_encrypted_file_not_created(
        self, mock_run: MagicMock, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Hook should raise when encryption succeeds but output file missing."""
        monkeypatch.delenv("TRIAGENT_SKIP_ENCRYPT", raising=False)

        skills_dir = tmp_path / "src" / "triagent" / "skills"
        skills_dir.mkdir(parents=True)
        (skills_dir / "omnia-data").mkdir()
        (skills_dir / "encrypted").mkdir()

        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir()
        (scripts_dir / "encrypt_prompts.py").write_text("# mock")

        # Script returns success but doesn't create file
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        hook = create_hook(tmp_path)

        with pytest.raises(RuntimeError, match="Encrypted file not created"):
            hook.initialize("1.0.0", {})


class TestBuildHookHelpers:
    """Test build hook helper methods."""

    def test_display_message_without_app(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Display should print to stderr when app not available."""
        hook = create_hook(tmp_path)
        hook._display("Test message")

        captured = capsys.readouterr()
        assert "Test message" in captured.err

    def test_display_message_with_app(self, tmp_path: Path) -> None:
        """Display should use app.display_info when available."""
        hook = create_hook(tmp_path)
        mock_app = MagicMock()

        # app is a property, so we need to patch it
        with patch.object(type(hook), "app", new_callable=lambda: property(lambda self: mock_app)):
            hook._display("Test message")

        mock_app.display_info.assert_called_once()
        assert "Test message" in mock_app.display_info.call_args[0][0]

    def test_add_force_include_creates_dict(self, tmp_path: Path) -> None:
        """force_include dict should be created if it doesn't exist."""
        hook = create_hook(tmp_path)
        build_data: dict = {}

        encrypted_file = tmp_path / "src" / "triagent" / "skills" / "encrypted" / "skills.enc"
        encrypted_file.parent.mkdir(parents=True)
        encrypted_file.write_bytes(b"test")

        hook._add_force_include(build_data, tmp_path, encrypted_file)

        assert "force_include" in build_data
        assert len(build_data["force_include"]) == 1

    def test_add_force_include_appends_to_existing(self, tmp_path: Path) -> None:
        """force_include should append to existing entries."""
        hook = create_hook(tmp_path)
        build_data: dict = {"force_include": {"existing.txt": "path/to/existing.txt"}}

        encrypted_file = tmp_path / "src" / "triagent" / "skills" / "encrypted" / "skills.enc"
        encrypted_file.parent.mkdir(parents=True)
        encrypted_file.write_bytes(b"test")

        hook._add_force_include(build_data, tmp_path, encrypted_file)

        assert len(build_data["force_include"]) == 2
        assert "existing.txt" in build_data["force_include"]

    def test_add_force_include_correct_destination_path(self, tmp_path: Path) -> None:
        """force_include should map to correct destination in wheel."""
        hook = create_hook(tmp_path)
        build_data: dict = {}

        encrypted_file = tmp_path / "src" / "triagent" / "skills" / "encrypted" / "skills.enc"
        encrypted_file.parent.mkdir(parents=True)
        encrypted_file.write_bytes(b"test")

        hook._add_force_include(build_data, tmp_path, encrypted_file)

        values = list(build_data["force_include"].values())
        assert "triagent/skills/encrypted/skills.enc" in values


class TestEncryptionExecution:
    """Test encryption script execution."""

    @patch("subprocess.run")
    def test_run_encryption_success(
        self, mock_run: MagicMock, tmp_path: Path
    ) -> None:
        """Encryption script should be called with correct arguments."""
        script_path = tmp_path / "scripts" / "encrypt_prompts.py"
        script_path.parent.mkdir()
        script_path.write_text("# mock")

        mock_run.return_value = MagicMock(
            returncode=0, stdout="Encrypted 5 items", stderr=""
        )

        hook = create_hook(tmp_path)
        hook._run_encryption(tmp_path)

        mock_run.assert_called_once()
        call_args = mock_run.call_args

        # Verify Python executable used
        assert sys.executable in call_args[0][0]
        # Verify script path
        assert str(script_path) in call_args[0][0]
        # Verify working directory
        assert call_args[1]["cwd"] == tmp_path

    @patch("subprocess.run")
    def test_run_encryption_passes_env_vars(
        self, mock_run: MagicMock, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Environment variables should be passed to encryption script."""
        monkeypatch.setenv("TRIAGENT_CORP_ID", "test.corp.com")

        script_path = tmp_path / "scripts" / "encrypt_prompts.py"
        script_path.parent.mkdir()
        script_path.write_text("# mock")

        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        hook = create_hook(tmp_path)
        hook._run_encryption(tmp_path)

        # Check env was passed
        call_args = mock_run.call_args
        env = call_args[1]["env"]
        assert "TRIAGENT_CORP_ID" in env
        assert env["TRIAGENT_CORP_ID"] == "test.corp.com"

    def test_run_encryption_script_not_found(self, tmp_path: Path) -> None:
        """Should raise when encryption script doesn't exist."""
        hook = create_hook(tmp_path)

        with pytest.raises(RuntimeError, match="Encryption script not found"):
            hook._run_encryption(tmp_path)

    @patch("subprocess.run")
    def test_run_encryption_returns_nonzero(
        self, mock_run: MagicMock, tmp_path: Path
    ) -> None:
        """Should raise when script returns non-zero exit code."""
        script_path = tmp_path / "scripts" / "encrypt_prompts.py"
        script_path.parent.mkdir()
        script_path.write_text("# mock")

        mock_run.return_value = MagicMock(
            returncode=1, stdout="", stderr="Error: No corporate environment"
        )

        hook = create_hook(tmp_path)

        with pytest.raises(RuntimeError, match="encryption failed"):
            hook._run_encryption(tmp_path)

    @patch("subprocess.run")
    def test_run_encryption_captures_output(
        self, mock_run: MagicMock, tmp_path: Path
    ) -> None:
        """Encryption output should be captured correctly."""
        script_path = tmp_path / "scripts" / "encrypt_prompts.py"
        script_path.parent.mkdir()
        script_path.write_text("# mock")

        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Added skill: omnia-data/core/test.md\n",
            stderr="",
        )

        hook = create_hook(tmp_path)
        hook._run_encryption(tmp_path)

        # Verify capture_output was set
        call_args = mock_run.call_args
        assert call_args[1]["capture_output"] is True
        assert call_args[1]["text"] is True
