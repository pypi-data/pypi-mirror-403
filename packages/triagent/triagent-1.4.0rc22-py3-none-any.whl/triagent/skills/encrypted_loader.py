"""Load and decrypt encrypted skills at runtime.

This module provides runtime decryption of encrypted skill bundles,
with caching to avoid repeated decryption.
"""

from __future__ import annotations

import json
from pathlib import Path

from cryptography.fernet import InvalidToken

from triagent.security.corporate_detect import (
    CorporateInfo,
    detect_corporate_environment,
)
from triagent.security.crypto import decrypt_data, derive_key
from triagent.security.exceptions import (
    CorporateDeviceRequired,
    DecryptionFailed,
    UnauthorizedEnvironment,
)

# Cache for decrypted skills
_decrypted_cache: dict | None = None
_corporate_info_cache: CorporateInfo | None = None

# Path to encrypted skills bundle
ENCRYPTED_SKILLS_PATH = Path(__file__).parent / "encrypted" / "skills.enc"


def is_encrypted_mode() -> bool:
    """Check if encrypted skills bundle exists.

    Returns:
        True if skills.enc exists and should use encrypted mode
    """
    return ENCRYPTED_SKILLS_PATH.exists()


def load_encrypted_skills() -> dict:
    """Load and decrypt the skills bundle.

    Returns:
        Dictionary with keys: "skills", "personas", "subagents", "data"

    Raises:
        CorporateDeviceRequired: If not on corporate device
        UnauthorizedEnvironment: If corporate but wrong environment
        DecryptionFailed: If decryption fails for other reasons
    """
    global _decrypted_cache, _corporate_info_cache

    if _decrypted_cache is not None:
        return _decrypted_cache

    corp_info = detect_corporate_environment()
    if corp_info is None:
        raise CorporateDeviceRequired(
            "Triagent requires a corporate-managed device.\n\n"
            "Your device must be:\n"
            "  - Connected to corporate network, OR\n"
            "  - Joined to Azure AD / Active Directory, OR\n"
            "  - Enrolled in MDM (Intune)\n\n"
            "Run 'triagent --check-device' for diagnostic information."
        )

    _corporate_info_cache = corp_info

    if not ENCRYPTED_SKILLS_PATH.exists():
        raise DecryptionFailed(
            f"Encrypted skills not found: {ENCRYPTED_SKILLS_PATH}\n"
            "The package may be corrupted or skills not encrypted."
        )

    key = derive_key(corp_info.identifier)

    try:
        encrypted_data = ENCRYPTED_SKILLS_PATH.read_bytes()
        decrypted_data = decrypt_data(encrypted_data, key)
        _decrypted_cache = json.loads(decrypted_data.decode("utf-8"))
        return _decrypted_cache
    except InvalidToken:
        raise UnauthorizedEnvironment(
            f"Failed to decrypt skills.\n\n"
            f"Detected corporate environment:\n"
            f"  Type: {corp_info.type}\n"
            f"  Identifier: {corp_info.identifier}\n\n"
            "This may not be an authorized corporate environment."
        ) from None
    except json.JSONDecodeError as e:
        raise DecryptionFailed(f"Decrypted data is not valid JSON: {e}") from e


def get_skill_content(rel_path: str) -> str | None:
    """Get skill markdown content by relative path.

    Args:
        rel_path: Relative path from skills directory (e.g., "omnia-data/developer/skill.md")

    Returns:
        Skill content string or None if not found
    """
    skills = load_encrypted_skills()
    return skills.get("skills", {}).get(rel_path)


def get_persona_content(rel_path: str) -> str | None:
    """Get persona YAML content by relative path.

    Args:
        rel_path: Relative path from skills directory (e.g., "omnia-data/_persona_developer.yaml")

    Returns:
        Persona content string or None if not found
    """
    skills = load_encrypted_skills()
    return skills.get("personas", {}).get(rel_path)


def get_subagent_content(rel_path: str) -> str | None:
    """Get subagent config content by relative path.

    Args:
        rel_path: Relative path from skills directory

    Returns:
        Subagent content string or None if not found
    """
    skills = load_encrypted_skills()
    return skills.get("subagents", {}).get(rel_path)


def get_data_content(rel_path: str) -> str | None:
    """Get data file content by relative path.

    Args:
        rel_path: Relative path from skills directory (e.g., "data/team-config.json")

    Returns:
        Data file content string or None if not found
    """
    skills = load_encrypted_skills()
    return skills.get("data", {}).get(rel_path)


def get_corporate_info() -> CorporateInfo | None:
    """Get cached corporate info (for diagnostics).

    Returns:
        CorporateInfo if detection has run, None otherwise
    """
    return _corporate_info_cache


def clear_cache() -> None:
    """Clear the decrypted skills cache (for testing)."""
    global _decrypted_cache, _corporate_info_cache
    _decrypted_cache = None
    _corporate_info_cache = None
