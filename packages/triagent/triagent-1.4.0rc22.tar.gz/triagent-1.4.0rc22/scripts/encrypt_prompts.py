#!/usr/bin/env python3
"""Encrypt triagent prompts for distribution.

This script must be run on a corporate-managed device OR
with the TRIAGENT_CORP_ID environment variable set.
The encrypted prompts will only be decryptable on machines
in the SAME corporate environment.

Usage:
    python scripts/encrypt_prompts.py

Environment Variables:
    TRIAGENT_CORP_ID: Corporate identifier to use for encryption.
                      If set, skips auto-detection (useful for CI/CD).
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from triagent.security.corporate_detect import CorporateInfo, detect_corporate_environment
from triagent.security.crypto import derive_key, encrypt_data


def collect_prompts() -> dict:
    """Collect all prompts into a dictionary.

    Returns:
        Dictionary with keys: skills, personas, subagents, data
    """
    base_path = Path(__file__).parent.parent / "src" / "triagent"
    skills_path = base_path / "skills"

    prompts: dict = {"skills": {}, "personas": {}, "subagents": {}, "data": {}}

    if not skills_path.exists():
        print(f"  Warning: Skills directory not found: {skills_path}")
        return prompts

    # Collect skill files (.md files)
    for skill_file in skills_path.rglob("*.md"):
        # Skip hidden files and README
        if skill_file.name.startswith(".") or skill_file.name.lower() == "readme.md":
            continue

        rel_path = str(skill_file.relative_to(skills_path))
        prompts["skills"][rel_path] = skill_file.read_text(encoding="utf-8")
        print(f"  Added skill: {rel_path}")

    # Collect persona files (_persona_*.yaml)
    for persona_file in skills_path.rglob("_persona_*.yaml"):
        rel_path = str(persona_file.relative_to(skills_path))
        prompts["personas"][rel_path] = persona_file.read_text(encoding="utf-8")
        print(f"  Added persona: {rel_path}")

    # Collect subagent files from _subagents directories
    for subagent_dir in skills_path.rglob("_subagents"):
        if not subagent_dir.is_dir():
            continue
        for subagent_file in subagent_dir.iterdir():
            if subagent_file.suffix in (".yaml", ".yml", ".py"):
                rel_path = str(subagent_file.relative_to(skills_path))
                prompts["subagents"][rel_path] = subagent_file.read_text(
                    encoding="utf-8"
                )
                print(f"  Added subagent: {rel_path}")

    # Collect data files (.json, .tsv) from data directory
    data_dir = skills_path / "data"
    if data_dir.exists():
        for data_file in data_dir.iterdir():
            if data_file.suffix in (".json", ".tsv"):
                rel_path = str(data_file.relative_to(skills_path))
                prompts["data"][rel_path] = data_file.read_text(encoding="utf-8")
                print(f"  Added data: {rel_path}")

    return prompts


def main() -> int:
    """Main encryption function.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    print("=" * 60)
    print("  TRIAGENT PROMPT ENCRYPTION")
    print("=" * 60)
    print()

    # Step 1: Detect corporate environment
    print("Step 1: Detecting corporate environment...")

    # Check for environment variable override (for CI/CD)
    env_corp_id = os.environ.get("TRIAGENT_CORP_ID")
    if env_corp_id:
        corp_info = CorporateInfo(
            type="env_var",
            identifier=env_corp_id.strip(),
            platform=sys.platform,
        )
        print(f"  Using TRIAGENT_CORP_ID environment variable: {env_corp_id}")
    else:
        corp_info = detect_corporate_environment()

    if corp_info is None:
        print()
        print("ERROR: This script must be run on a corporate device.")
        print()
        print("Ensure you are:")
        print("  - Connected to corporate network")
        print("  - Have active Kerberos tickets (kinit)")
        print("  - On an Azure AD / AD joined device")
        print()
        print("Alternatively, set TRIAGENT_CORP_ID environment variable:")
        print("  export TRIAGENT_CORP_ID=your-corporate-domain.com")
        print()
        return 1

    print("  Corporate environment detected:")
    print(f"    Type: {corp_info.type}")
    print(f"    Identifier: {corp_info.identifier}")
    print()

    # Step 2: Collect prompts
    print("Step 2: Collecting prompts...")
    prompts = collect_prompts()
    total_skills = len(prompts["skills"])
    total_personas = len(prompts["personas"])
    total_subagents = len(prompts["subagents"])
    total_data = len(prompts["data"])
    total_items = total_skills + total_personas + total_subagents + total_data
    print(f"  Skills: {total_skills}")
    print(f"  Personas: {total_personas}")
    print(f"  Subagents: {total_subagents}")
    print(f"  Data files: {total_data}")
    print(f"  Total items: {total_items}")
    print()

    if total_items == 0:
        print("WARNING: No prompts found to encrypt!")
        print()
        return 1

    # Step 3: Encrypt
    print("Step 3: Encrypting...")
    key = derive_key(corp_info.identifier)
    prompts_json = json.dumps(prompts, indent=2)
    encrypted = encrypt_data(prompts_json.encode("utf-8"), key)
    print(f"  Plaintext size: {len(prompts_json):,} bytes")
    print(f"  Encrypted size: {len(encrypted):,} bytes")
    print()

    # Step 4: Write output to build temp directory (non-destructive)
    output_path = Path(__file__).parent.parent / "build" / ".temp" / "skills.enc"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(encrypted)

    print(f"Step 4: Output written to {output_path}")
    print()
    print("=" * 60)
    print("  ENCRYPTION COMPLETE")
    print("=" * 60)
    print()
    print(f"Encrypted {total_items} items for: {corp_info.identifier}")
    print()
    print("IMPORTANT: These prompts will ONLY decrypt on devices")
    print(f"in the '{corp_info.identifier}' corporate environment.")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
