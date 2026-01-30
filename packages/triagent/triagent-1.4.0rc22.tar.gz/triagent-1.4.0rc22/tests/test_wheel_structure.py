"""Tests for validating built wheel structure.

This module tests the structure and contents of built wheels to ensure:
- Encrypted skills file is present
- Plaintext skill directories are NOT present
- System prompts can be generated from encrypted bundle
- Bundle can be decrypted with corporate key
"""

from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

if TYPE_CHECKING:
    from collections.abc import Generator


@pytest.fixture
def wheel_path() -> Path:
    """Get the most recent wheel for testing.

    Returns:
        Path to the most recent wheel file

    Raises:
        pytest.skip: If no wheel found in dist/
    """
    dist_dir = Path(__file__).parent.parent / "dist"
    if not dist_dir.exists():
        pytest.skip("No dist/ directory - run 'python -m build' first")

    wheels = list(dist_dir.glob("triagent-*.whl"))
    if not wheels:
        pytest.skip("No wheel found in dist/ - run 'python -m build' first")

    # Return most recently modified wheel
    return max(wheels, key=lambda p: p.stat().st_mtime)


class TestWheelContents:
    """Validate wheel contains correct files."""

    def test_wheel_contains_encrypted_skills_file(self, wheel_path: Path) -> None:
        """Wheel should contain skills.enc in encrypted directory."""
        with zipfile.ZipFile(wheel_path, "r") as whl:
            names = whl.namelist()
            has_encrypted = any("skills/encrypted/skills.enc" in n for n in names)
            assert has_encrypted, f"skills.enc not found in wheel. Contents: {names[:20]}..."

    def test_wheel_does_not_contain_plaintext_skills(self, wheel_path: Path) -> None:
        """Wheel should NOT contain plaintext skill directories."""
        with zipfile.ZipFile(wheel_path, "r") as whl:
            names = whl.namelist()

            plaintext_patterns = [
                "skills/omnia-data/",
                "skills/omnia/",
                "skills/levvia/",
            ]

            for pattern in plaintext_patterns:
                plaintext_files = [n for n in names if pattern in n]
                assert not plaintext_files, (
                    f"Plaintext directory {pattern} found in wheel: {plaintext_files}"
                )

    def test_wheel_contains_encrypted_loader(self, wheel_path: Path) -> None:
        """Wheel should contain encrypted_loader.py."""
        with zipfile.ZipFile(wheel_path, "r") as whl:
            names = whl.namelist()
            has_loader = any("skills/encrypted_loader.py" in n for n in names)
            assert has_loader, "encrypted_loader.py not found in wheel"

    def test_wheel_contains_loader_with_encryption_support(
        self, wheel_path: Path
    ) -> None:
        """loader.py should contain is_encrypted_mode integration."""
        with zipfile.ZipFile(wheel_path, "r") as whl:
            # Find loader.py
            loader_path = None
            for name in whl.namelist():
                if name.endswith("skills/loader.py"):
                    loader_path = name
                    break

            assert loader_path is not None, "loader.py not found in wheel"

            loader_content = whl.read(loader_path).decode("utf-8")
            assert "is_encrypted_mode" in loader_content, (
                "loader.py missing encrypted mode integration"
            )
            # Should have multiple references for full integration
            refs = loader_content.count("is_encrypted_mode")
            assert refs >= 5, f"loader.py should have at least 5 refs to is_encrypted_mode, found {refs}"

    def test_encrypted_file_size_reasonable(self, wheel_path: Path) -> None:
        """Encrypted file should have reasonable size (not empty, not huge)."""
        with zipfile.ZipFile(wheel_path, "r") as whl:
            for info in whl.infolist():
                if "skills.enc" in info.filename:
                    # Should be between 1KB and 1MB
                    min_size = 1_000
                    max_size = 1_000_000
                    assert min_size < info.file_size < max_size, (
                        f"skills.enc size {info.file_size} bytes outside expected range "
                        f"({min_size}-{max_size})"
                    )
                    return

        pytest.fail("skills.enc not found in wheel")

    def test_wheel_contains_security_modules(self, wheel_path: Path) -> None:
        """Wheel should contain security modules (crypto, corporate_detect)."""
        with zipfile.ZipFile(wheel_path, "r") as whl:
            names = whl.namelist()

            has_crypto = any("security/crypto.py" in n for n in names)
            has_detect = any("security/corporate_detect.py" in n for n in names)
            has_group = any("security/group_membership.py" in n for n in names)

            assert has_crypto, "security/crypto.py not found in wheel"
            assert has_detect, "security/corporate_detect.py not found in wheel"
            assert has_group, "security/group_membership.py not found in wheel"

    def test_wheel_metadata_correct(self, wheel_path: Path) -> None:
        """Wheel should have correct metadata."""
        with zipfile.ZipFile(wheel_path, "r") as whl:
            # Find METADATA file
            metadata_files = [n for n in whl.namelist() if "METADATA" in n]
            assert metadata_files, "No METADATA file in wheel"

            metadata = whl.read(metadata_files[0]).decode("utf-8")
            assert "Name: triagent" in metadata
            assert "Requires-Python:" in metadata


class TestEncryptedBundleValidity:
    """Validate encrypted bundle can be decrypted and has correct structure."""

    def test_bundle_decrypts_with_correct_key(self, wheel_path: Path) -> None:
        """Bundle should decrypt successfully with corporate key."""
        from triagent.security.crypto import decrypt_data, derive_key

        with zipfile.ZipFile(wheel_path, "r") as whl:
            # Find skills.enc
            enc_path = None
            for name in whl.namelist():
                if "skills.enc" in name:
                    enc_path = name
                    break

            assert enc_path is not None, "skills.enc not found in wheel"
            encrypted_data = whl.read(enc_path)

        # Use the corporate ID used during build
        key = derive_key("us.deloitte.com")
        decrypted = decrypt_data(encrypted_data, key)
        bundle = json.loads(decrypted.decode("utf-8"))

        assert "skills" in bundle
        assert "personas" in bundle
        assert "subagents" in bundle

    def test_bundle_contains_expected_personas(self, wheel_path: Path) -> None:
        """Bundle should contain known personas."""
        from triagent.security.crypto import decrypt_data, derive_key

        with zipfile.ZipFile(wheel_path, "r") as whl:
            enc_path = next(n for n in whl.namelist() if "skills.enc" in n)
            encrypted_data = whl.read(enc_path)

        key = derive_key("us.deloitte.com")
        decrypted = decrypt_data(encrypted_data, key)
        bundle = json.loads(decrypted.decode("utf-8"))

        personas = bundle.get("personas", {})
        # Should have at least omnia-data personas
        assert any("omnia-data" in path and "_persona_developer" in path for path in personas), (
            f"Developer persona not found. Personas: {list(personas.keys())}"
        )
        assert any("omnia-data" in path and "_persona_support" in path for path in personas), (
            f"Support persona not found. Personas: {list(personas.keys())}"
        )

    def test_bundle_contains_expected_skills(self, wheel_path: Path) -> None:
        """Bundle should contain expected skill files."""
        from triagent.security.crypto import decrypt_data, derive_key

        with zipfile.ZipFile(wheel_path, "r") as whl:
            enc_path = next(n for n in whl.namelist() if "skills.enc" in n)
            encrypted_data = whl.read(enc_path)

        key = derive_key("us.deloitte.com")
        decrypted = decrypt_data(encrypted_data, key)
        bundle = json.loads(decrypted.decode("utf-8"))

        skills = bundle.get("skills", {})
        assert len(skills) > 0, "No skills in bundle"

        # Skills should have .md extension
        for path in skills:
            assert path.endswith(".md"), f"Non-markdown skill path: {path}"

    def test_bundle_skill_count_matches_expectation(self, wheel_path: Path) -> None:
        """Bundle should have a reasonable number of skills."""
        from triagent.security.crypto import decrypt_data, derive_key

        with zipfile.ZipFile(wheel_path, "r") as whl:
            enc_path = next(n for n in whl.namelist() if "skills.enc" in n)
            encrypted_data = whl.read(enc_path)

        key = derive_key("us.deloitte.com")
        decrypted = decrypt_data(encrypted_data, key)
        bundle = json.loads(decrypted.decode("utf-8"))

        skill_count = len(bundle.get("skills", {}))
        persona_count = len(bundle.get("personas", {}))

        # Should have at least some skills and personas
        assert skill_count >= 5, f"Too few skills: {skill_count}"
        assert persona_count >= 2, f"Too few personas: {persona_count}"


class TestSystemPromptFromWheel:
    """Validate system prompts work with wheel's encrypted bundle."""

    @pytest.fixture
    def setup_encrypted_mode(
        self, wheel_path: Path, tmp_path: Path
    ) -> Generator[None, None, None]:
        """Extract and use wheel's encrypted bundle for testing.

        Yields:
            None (sets up patched environment)
        """
        # Extract skills.enc from wheel
        with zipfile.ZipFile(wheel_path, "r") as whl:
            enc_path = next(n for n in whl.namelist() if "skills.enc" in n)
            enc_data = whl.read(enc_path)

        enc_file = tmp_path / "skills.enc"
        enc_file.write_bytes(enc_data)

        # Patch the path and corporate detection
        with patch("triagent.skills.encrypted_loader.ENCRYPTED_SKILLS_PATH", enc_file):
            with patch(
                "triagent.skills.encrypted_loader.detect_corporate_environment"
            ) as mock_detect:
                from triagent.security.corporate_detect import CorporateInfo

                mock_detect.return_value = CorporateInfo(
                    type="DNS", identifier="us.deloitte.com", platform="darwin"
                )
                # Clear cache to ensure fresh load
                from triagent.skills.encrypted_loader import clear_cache

                clear_cache()
                yield
                clear_cache()

    def test_system_prompt_length_reasonable(
        self, wheel_path: Path, setup_encrypted_mode: None
    ) -> None:
        """System prompt should be substantial (contains skills)."""
        from triagent.skills.system import get_system_prompt

        prompt = get_system_prompt("omnia-data", "developer")

        # Should be at least 5KB with skills content
        min_length = 5_000
        assert len(prompt) > min_length, (
            f"Prompt too short: {len(prompt)} chars (expected > {min_length})"
        )

    def test_system_prompt_contains_persona_header(
        self, wheel_path: Path, setup_encrypted_mode: None
    ) -> None:
        """System prompt should indicate active persona."""
        from triagent.skills.system import get_system_prompt

        prompt = get_system_prompt("omnia-data", "developer")

        assert "Developer" in prompt or "developer" in prompt.lower()

    def test_system_prompt_contains_skill_content(
        self, wheel_path: Path, setup_encrypted_mode: None
    ) -> None:
        """System prompt should contain actual skill content."""
        from triagent.skills.system import get_system_prompt

        prompt = get_system_prompt("omnia-data", "developer")

        # Check for content that would be in skills
        # These are generic patterns that should be in most skill sets
        has_relevant_content = (
            "Azure" in prompt
            or "DevOps" in prompt
            or "code review" in prompt.lower()
            or "pipeline" in prompt.lower()
        )
        assert has_relevant_content, "Prompt missing expected skill content"

    def test_developer_persona_loads_correctly(
        self, wheel_path: Path, setup_encrypted_mode: None
    ) -> None:
        """Developer persona should load with its skills."""
        from triagent.skills.loader import load_persona

        persona = load_persona("omnia-data", "developer")
        assert persona is not None, "Failed to load developer persona"
        assert persona.definition.name == "developer"
        assert len(persona.skills) > 0, "Developer persona has no skills"

    def test_support_persona_loads_correctly(
        self, wheel_path: Path, setup_encrypted_mode: None
    ) -> None:
        """Support persona should load with its skills."""
        from triagent.skills.loader import load_persona

        persona = load_persona("omnia-data", "support")
        assert persona is not None, "Failed to load support persona"
        assert persona.definition.name == "support"
        assert len(persona.skills) > 0, "Support persona has no skills"


class TestWheelInstallation:
    """Test wheel can be used after installation."""

    def test_wheel_is_valid_zipfile(self, wheel_path: Path) -> None:
        """Wheel should be a valid ZIP file."""
        assert zipfile.is_zipfile(wheel_path), f"{wheel_path} is not a valid ZIP file"

    def test_wheel_has_required_entry_points(self, wheel_path: Path) -> None:
        """Wheel should define CLI entry point."""
        with zipfile.ZipFile(wheel_path, "r") as whl:
            # Modern wheels use console_scripts in WHEEL metadata
            # Check for triagent in the distribution
            has_cli = False
            for name in whl.namelist():
                if "cli.py" in name or "triagent" in name.lower():
                    has_cli = True
                    break

            assert has_cli, "CLI module not found in wheel"

    def test_all_python_files_syntactically_valid(self, wheel_path: Path) -> None:
        """All Python files in wheel should be syntactically valid."""
        import ast

        with zipfile.ZipFile(wheel_path, "r") as whl:
            for name in whl.namelist():
                if name.endswith(".py"):
                    content = whl.read(name).decode("utf-8")
                    try:
                        ast.parse(content)
                    except SyntaxError as e:
                        pytest.fail(f"Syntax error in {name}: {e}")
