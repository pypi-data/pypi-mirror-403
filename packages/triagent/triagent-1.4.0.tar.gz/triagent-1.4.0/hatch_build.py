"""Hatch build hook to encrypt skills before packaging.

This hook runs during `python -m build` and:
1. Encrypts all skills from src/triagent/skills/ into build/.temp/skills.enc
2. Packages the encrypted file into the wheel
3. Does NOT modify the source tree (non-destructive)

Environment Variables:
    TRIAGENT_CORP_ID: Corporate identifier for encryption key derivation
    TRIAGENT_SKIP_ENCRYPT: Set to "1" to skip encryption (dev builds / CI tests)
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class EncryptSkillsHook(BuildHookInterface):
    """Build hook that encrypts skills for packaging (non-destructive)."""

    PLUGIN_NAME = "encrypt-skills"

    def initialize(self, version: str, build_data: dict) -> None:
        """Run before build - encrypt skills (non-destructive).

        Args:
            version: The version being built
            build_data: Build configuration data
        """
        root = Path(self.root)
        skills_dir = root / "src" / "triagent" / "skills"

        # Skip encryption if TRIAGENT_SKIP_ENCRYPT is set (for dev builds / CI tests)
        if os.environ.get("TRIAGENT_SKIP_ENCRYPT"):
            self._display("Skipping encryption (TRIAGENT_SKIP_ENCRYPT=1)")
            return

        # Skip if no skills directory
        if not skills_dir.exists():
            self._display("Skills directory not found, skipping encryption")
            return

        # Check for plaintext skill directories
        plaintext_dirs = ["omnia-data", "omnia", "levvia", "core"]
        has_plaintext = any((skills_dir / d).exists() for d in plaintext_dirs)

        # Encrypted file is now in build temp directory (not source tree)
        build_temp = root / "build" / ".temp"
        encrypted_file = build_temp / "skills.enc"

        if not has_plaintext:
            # No plaintext to encrypt, check if already encrypted
            if encrypted_file.exists():
                self._display("Using existing encrypted file from build cache")
                self._add_force_include(build_data, root, encrypted_file)
                return
            else:
                self._display("WARNING: No skills found to encrypt")
                return

        # Run encryption (outputs to build/.temp/skills.enc)
        self._display("Encrypting skills...")
        self._run_encryption(root)

        # Verify encrypted file exists
        if not encrypted_file.exists():
            raise RuntimeError(f"Encrypted file not created: {encrypted_file}")

        # Force include the encrypted file in the build
        # NOTE: We do NOT delete plaintext - source tree stays intact
        self._add_force_include(build_data, root, encrypted_file)
        self._display("Build prepared: skills.enc will be packaged (source unchanged)")

    def _display(self, message: str) -> None:
        """Display a message during build.

        Args:
            message: Message to display
        """
        # Use app display if available, otherwise print
        if hasattr(self, "app") and self.app is not None:
            self.app.display_info(f"[encrypt-skills] {message}")
        else:
            print(f"[encrypt-skills] {message}", file=sys.stderr)

    def _add_force_include(
        self, build_data: dict, root: Path, encrypted_file: Path
    ) -> None:
        """Add encrypted file to force_include for packaging.

        Args:
            build_data: Build configuration data
            root: Project root directory
            encrypted_file: Path to the encrypted skills file
        """
        if "force_include" not in build_data:
            build_data["force_include"] = {}

        encrypted_rel_path = str(encrypted_file.relative_to(root))
        build_data["force_include"][encrypted_rel_path] = (
            "triagent/skills/encrypted/skills.enc"
        )

    def _run_encryption(self, root: Path) -> None:
        """Run the encryption script.

        Args:
            root: Project root directory

        Raises:
            RuntimeError: If encryption fails
        """
        script_path = root / "scripts" / "encrypt_prompts.py"

        if not script_path.exists():
            raise RuntimeError(f"Encryption script not found: {script_path}")

        # Run encryption script
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=root,
            capture_output=True,
            text=True,
            env={**os.environ},  # Pass through environment including TRIAGENT_CORP_ID
        )

        if result.returncode != 0:
            error_msg = result.stderr or result.stdout or "Unknown error"
            raise RuntimeError(f"Skills encryption failed:\n{error_msg}")

        # Show encryption output
        if result.stdout:
            for line in result.stdout.strip().split("\n"):
                self._display(line)
