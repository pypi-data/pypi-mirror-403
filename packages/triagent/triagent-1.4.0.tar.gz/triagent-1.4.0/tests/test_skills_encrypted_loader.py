"""Tests for encrypted skills loader."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from triagent.security.crypto import derive_key, encrypt_data
from triagent.security.exceptions import CorporateDeviceRequired


class TestEncryptedMode:
    """Test encrypted mode detection."""

    def test_is_encrypted_mode_when_file_exists(self, tmp_path) -> None:
        """Should return True when skills.enc exists."""
        from triagent.skills.encrypted_loader import is_encrypted_mode

        # Create a mock encrypted file
        enc_file = tmp_path / "skills.enc"
        enc_file.write_bytes(b"encrypted content")

        with patch(
            "triagent.skills.encrypted_loader.ENCRYPTED_SKILLS_PATH", enc_file
        ):
            assert is_encrypted_mode() is True

    def test_is_encrypted_mode_when_file_missing(self, tmp_path) -> None:
        """Should return False when skills.enc doesn't exist."""
        from triagent.skills.encrypted_loader import is_encrypted_mode

        missing_file = tmp_path / "skills.enc"

        with patch(
            "triagent.skills.encrypted_loader.ENCRYPTED_SKILLS_PATH", missing_file
        ):
            assert is_encrypted_mode() is False


class TestSkillsLoading:
    """Test skills loading with mocked corporate detection."""

    @pytest.fixture
    def mock_corporate_info(self) -> MagicMock:
        """Create mock CorporateInfo."""
        from triagent.security.corporate_detect import CorporateInfo

        return CorporateInfo(
            type="DNS",
            identifier="test.corp.com",
            platform="darwin",
        )

    @pytest.fixture
    def create_encrypted_bundle(self, tmp_path) -> Path:
        """Create a test encrypted bundle."""

        def _create(skills: dict, corporate_id: str = "test.corp.com") -> Path:
            key = derive_key(corporate_id)
            skills_json = json.dumps(skills).encode("utf-8")
            encrypted = encrypt_data(skills_json, key)

            enc_file = tmp_path / "skills.enc"
            enc_file.write_bytes(encrypted)
            return enc_file

        return _create

    def test_load_skills_non_corporate(self, tmp_path) -> None:
        """Should raise exception when not on corporate device."""
        from triagent.skills.encrypted_loader import clear_cache, load_encrypted_skills

        clear_cache()

        enc_file = tmp_path / "skills.enc"
        enc_file.write_bytes(b"fake encrypted content")

        with patch(
            "triagent.skills.encrypted_loader.detect_corporate_environment",
            return_value=None,
        ):
            with patch(
                "triagent.skills.encrypted_loader.ENCRYPTED_SKILLS_PATH", enc_file
            ):
                with pytest.raises(CorporateDeviceRequired):
                    load_encrypted_skills()

    def test_load_skills_success(
        self, mock_corporate_info, create_encrypted_bundle
    ) -> None:
        """Should load skills successfully on corporate device."""
        from triagent.skills.encrypted_loader import clear_cache, load_encrypted_skills

        clear_cache()

        test_skills = {
            "skills": {"omnia-data/core/test.md": "# Test Skill\nContent"},
            "personas": {"omnia-data/_persona_dev.yaml": "name: dev"},
            "subagents": {},
        }

        enc_file = create_encrypted_bundle(test_skills)

        with patch(
            "triagent.skills.encrypted_loader.detect_corporate_environment",
            return_value=mock_corporate_info,
        ):
            with patch(
                "triagent.skills.encrypted_loader.ENCRYPTED_SKILLS_PATH", enc_file
            ):
                result = load_encrypted_skills()

                assert "skills" in result
                assert "personas" in result
                assert "omnia-data/core/test.md" in result["skills"]

    def test_load_skills_caching(
        self, mock_corporate_info, create_encrypted_bundle
    ) -> None:
        """Should cache skills after first load."""
        from triagent.skills.encrypted_loader import clear_cache, load_encrypted_skills

        clear_cache()

        test_skills = {"skills": {}, "personas": {}, "subagents": {}}
        enc_file = create_encrypted_bundle(test_skills)

        with patch(
            "triagent.skills.encrypted_loader.detect_corporate_environment",
            return_value=mock_corporate_info,
        ) as mock_detect:
            with patch(
                "triagent.skills.encrypted_loader.ENCRYPTED_SKILLS_PATH", enc_file
            ):
                # First call
                load_encrypted_skills()
                # Second call should use cache
                load_encrypted_skills()

                # Detection should only be called once
                assert mock_detect.call_count == 1

    def test_clear_cache(self, mock_corporate_info, create_encrypted_bundle) -> None:
        """Should clear cache when requested."""
        from triagent.skills.encrypted_loader import clear_cache, load_encrypted_skills

        clear_cache()

        test_skills = {"skills": {}, "personas": {}, "subagents": {}}
        enc_file = create_encrypted_bundle(test_skills)

        with patch(
            "triagent.skills.encrypted_loader.detect_corporate_environment",
            return_value=mock_corporate_info,
        ) as mock_detect:
            with patch(
                "triagent.skills.encrypted_loader.ENCRYPTED_SKILLS_PATH", enc_file
            ):
                load_encrypted_skills()
                clear_cache()
                load_encrypted_skills()

                # Detection should be called twice after cache clear
                assert mock_detect.call_count == 2


class TestContentAccessors:
    """Test content accessor functions."""

    @pytest.fixture
    def setup_skills(self, tmp_path) -> None:
        """Set up test skills with mocked environment."""
        from triagent.security.corporate_detect import CorporateInfo
        from triagent.skills.encrypted_loader import clear_cache

        clear_cache()

        test_skills = {
            "skills": {
                "omnia-data/developer/my_skill.md": "# My Skill\nContent here",
            },
            "personas": {
                "omnia-data/_persona_developer.yaml": "name: developer",
            },
            "subagents": {
                "core/_subagents/code_reviewer.yaml": "name: code_reviewer",
            },
        }

        mock_corp = CorporateInfo("DNS", "test.corp.com", "darwin")
        key = derive_key(mock_corp.identifier)
        encrypted = encrypt_data(
            json.dumps(test_skills).encode("utf-8"), key
        )

        enc_file = tmp_path / "skills.enc"
        enc_file.write_bytes(encrypted)

        return {
            "enc_file": enc_file,
            "mock_corp": mock_corp,
            "skills": test_skills,
        }

    def test_get_skill_content(self, setup_skills) -> None:
        """Should get skill content by path."""
        from triagent.skills.encrypted_loader import get_skill_content

        with patch(
            "triagent.skills.encrypted_loader.detect_corporate_environment",
            return_value=setup_skills["mock_corp"],
        ):
            with patch(
                "triagent.skills.encrypted_loader.ENCRYPTED_SKILLS_PATH",
                setup_skills["enc_file"],
            ):
                content = get_skill_content("omnia-data/developer/my_skill.md")
                assert content == "# My Skill\nContent here"

    def test_get_skill_content_not_found(self, setup_skills) -> None:
        """Should return None for missing skill."""
        from triagent.skills.encrypted_loader import get_skill_content

        with patch(
            "triagent.skills.encrypted_loader.detect_corporate_environment",
            return_value=setup_skills["mock_corp"],
        ):
            with patch(
                "triagent.skills.encrypted_loader.ENCRYPTED_SKILLS_PATH",
                setup_skills["enc_file"],
            ):
                content = get_skill_content("nonexistent/skill.md")
                assert content is None

    def test_get_persona_content(self, setup_skills) -> None:
        """Should get persona content by path."""
        from triagent.skills.encrypted_loader import get_persona_content

        with patch(
            "triagent.skills.encrypted_loader.detect_corporate_environment",
            return_value=setup_skills["mock_corp"],
        ):
            with patch(
                "triagent.skills.encrypted_loader.ENCRYPTED_SKILLS_PATH",
                setup_skills["enc_file"],
            ):
                content = get_persona_content("omnia-data/_persona_developer.yaml")
                assert content == "name: developer"

    def test_get_subagent_content(self, setup_skills) -> None:
        """Should get subagent content by path."""
        from triagent.skills.encrypted_loader import get_subagent_content

        with patch(
            "triagent.skills.encrypted_loader.detect_corporate_environment",
            return_value=setup_skills["mock_corp"],
        ):
            with patch(
                "triagent.skills.encrypted_loader.ENCRYPTED_SKILLS_PATH",
                setup_skills["enc_file"],
            ):
                content = get_subagent_content("core/_subagents/code_reviewer.yaml")
                assert content == "name: code_reviewer"
