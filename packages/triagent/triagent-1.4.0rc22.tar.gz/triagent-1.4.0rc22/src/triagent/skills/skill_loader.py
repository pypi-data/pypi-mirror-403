"""Dynamic skill loading based on triggers and user queries.

This module provides utilities for:
- Matching user queries against skill trigger patterns
- Detecting programming language from file extensions
- Loading sub-skills on demand (code-review, pipeline, etc.)
- Managing skill search paths for hierarchical skill organization
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .loader import SKILLS_DIR, load_skill, parse_frontmatter

# File extension to language mapping for code review detection
EXTENSION_LANGUAGE_MAP: dict[str, str] = {
    # .NET / C#
    ".cs": "dotnet",
    ".csproj": "dotnet",
    ".sln": "dotnet",
    ".vb": "dotnet",
    ".fs": "dotnet",
    # Python
    ".py": "python",
    ".pyi": "python",
    # PySpark (Jupyter notebooks)
    ".ipynb": "pyspark",
    # SQL (often reviewed with .NET)
    ".sql": "dotnet",
}

# Spark-related imports that indicate PySpark code
PYSPARK_INDICATORS = [
    "from pyspark",
    "import pyspark",
    "from delta",
    "import delta",
    "SparkSession",
    "DataFrame",
    "spark.read",
    "spark.sql",
]

# Extended search paths for skill loading
SKILL_SEARCH_PATHS = [
    "{team}/developer/{skill}.md",
    "{team}/developer/code-review/{skill}.md",
    "{team}/developer/pipeline/{skill}.md",
    "{team}/support/{skill}.md",
    "{team}/po-bsa/{skill}.md",
    "{team}/finops/{skill}.md",
    "{team}/core/{skill}.md",
    "core/{skill}.md",
    "reference/{skill}.md",
]


def match_skill_trigger(query: str, triggers: list[str]) -> bool:
    """Check if user query matches any of the skill trigger patterns.

    Args:
        query: User's input query/message
        triggers: List of regex patterns to match against

    Returns:
        True if query matches any trigger pattern, False otherwise

    Example:
        >>> match_skill_trigger("Review PR #12345", ["review.*PR", "code review"])
        True
        >>> match_skill_trigger("Hello world", ["review.*PR"])
        False
    """
    if not triggers:
        return False

    query_lower = query.lower()
    for trigger in triggers:
        try:
            if re.search(trigger, query_lower, re.IGNORECASE):
                return True
        except re.error:
            # Invalid regex pattern, skip it
            continue
    return False


def detect_code_review_language(
    files: list[str],
    file_contents: dict[str, str] | None = None,
) -> str | list[str]:
    """Detect the appropriate code review language based on file extensions.

    For Python files, also checks content for PySpark indicators to
    distinguish between Python and PySpark reviews.

    Args:
        files: List of file paths to analyze
        file_contents: Optional dict mapping file paths to their contents
                      (used for PySpark detection in .py files)

    Returns:
        Single language string if all files are same language,
        or list of languages if mixed

    Example:
        >>> detect_code_review_language(["main.py", "utils.py"])
        "python"
        >>> detect_code_review_language(["Service.cs", "Model.cs"])
        "dotnet"
        >>> detect_code_review_language(["main.py", "Service.cs"])
        ["python", "dotnet"]
    """
    if not files:
        return "python"  # Default to Python

    language_counts: dict[str, int] = {}
    file_contents = file_contents or {}

    for file_path in files:
        ext = Path(file_path).suffix.lower()
        language = EXTENSION_LANGUAGE_MAP.get(ext)

        if language is None:
            continue

        # For .py files, check if it's PySpark
        if language == "python" and file_path in file_contents:
            content = file_contents[file_path]
            if _is_pyspark_content(content):
                language = "pyspark"

        language_counts[language] = language_counts.get(language, 0) + 1

    if not language_counts:
        return "python"  # Default

    # If single language, return as string
    if len(language_counts) == 1:
        return list(language_counts.keys())[0]

    # Multiple languages - return sorted list by count (most common first)
    sorted_languages = sorted(
        language_counts.keys(),
        key=lambda x: language_counts[x],
        reverse=True,
    )
    return sorted_languages


def _is_pyspark_content(content: str) -> bool:
    """Check if Python file content contains PySpark indicators.

    Args:
        content: File content to analyze

    Returns:
        True if content appears to be PySpark code
    """
    for indicator in PYSPARK_INDICATORS:
        if indicator in content:
            return True
    return False


def load_sub_skill(
    skill_path: str,
    team: str = "omnia-data",
) -> str | None:
    """Load sub-skill content by relative path.

    Sub-skills are organized in subdirectories under persona directories:
    - developer/code-review/dotnet_code_review.md
    - developer/pipeline/release_investigation.md
    - support/telemetry_investigation.md

    Args:
        skill_path: Relative path like "code-review/dotnet_code_review"
                   or full path like "developer/code-review/dotnet_code_review"
        team: Team identifier (default: "omnia-data")

    Returns:
        Skill content as string, or None if not found
    """
    # Normalize the skill path - only normalize the file name, not directory
    # Directories use hyphens (code-review), files use underscores (dotnet_code_review)
    parts = skill_path.split("/")
    if len(parts) > 1:
        # Normalize only the last part (filename)
        parts[-1] = parts[-1].replace("-", "_")
        skill_path = "/".join(parts)
    else:
        skill_path = skill_path.replace("-", "_")

    # Add .md extension if not present
    if not skill_path.endswith(".md"):
        skill_path = f"{skill_path}.md"

    # Try various search paths
    search_paths = [
        SKILLS_DIR / team / skill_path,
        SKILLS_DIR / team / "developer" / skill_path,
        SKILLS_DIR / team / "support" / skill_path,
        SKILLS_DIR / team / "po-bsa" / skill_path,
        SKILLS_DIR / team / "finops" / skill_path,
        SKILLS_DIR / "core" / skill_path,
    ]

    for path in search_paths:
        if path.exists():
            skill = load_skill(path)
            if skill:
                # Return content with optional header
                if skill.metadata.display_name:
                    return f"# {skill.metadata.display_name}\n\n{skill.content}"
                return skill.content

    return None


def load_skill_by_language(
    language: str,
    team: str = "omnia-data",
) -> str | None:
    """Load code review skill for a specific language.

    Args:
        language: Language identifier ("dotnet", "python", "pyspark")
        team: Team identifier

    Returns:
        Skill content as string, or None if not found
    """
    # Skills consolidated to root developer directory
    skill_map = {
        "dotnet": "dotnet_code_review",
        "python": "python_code_review",
        "pyspark": "pyspark_code_review",
    }

    skill_path = skill_map.get(language)
    if not skill_path:
        return None

    return load_sub_skill(skill_path, team)


def get_skill_for_query(
    query: str,
    available_skills: dict[str, dict[str, Any]],
) -> str | None:
    """Find the most appropriate skill for a user query.

    Matches query against skill triggers to find the best match.

    Args:
        query: User's input query
        available_skills: Dict mapping skill names to their metadata
                         (must include "triggers" key)

    Returns:
        Name of the matching skill, or None if no match
    """
    for skill_name, metadata in available_skills.items():
        triggers = metadata.get("triggers", [])
        if match_skill_trigger(query, triggers):
            return skill_name
    return None


def load_skill_with_dependencies(
    skill_name: str,
    team: str = "omnia-data",
    loaded_skills: set[str] | None = None,
) -> dict[str, str]:
    """Load a skill and all its dependencies recursively.

    Args:
        skill_name: Name of the skill to load
        team: Team identifier
        loaded_skills: Set of already loaded skill names (prevents cycles)

    Returns:
        Dict mapping skill names to their content
    """
    if loaded_skills is None:
        loaded_skills = set()

    if skill_name in loaded_skills:
        return {}

    result: dict[str, str] = {}

    # Try to load the skill
    content = load_sub_skill(skill_name, team)
    if content is None:
        return result

    loaded_skills.add(skill_name)
    result[skill_name] = content

    # Parse frontmatter to get dependencies
    # Note: We need to re-read the file to get frontmatter
    for search_pattern in SKILL_SEARCH_PATHS:
        path_str = search_pattern.format(team=team, skill=skill_name)
        path = SKILLS_DIR / path_str
        if path.exists():
            try:
                raw_content = path.read_text(encoding="utf-8")
                frontmatter, _ = parse_frontmatter(raw_content)
                requires = frontmatter.get("requires", [])
                for dep in requires:
                    dep_content = load_skill_with_dependencies(
                        dep, team, loaded_skills
                    )
                    result.update(dep_content)
            except Exception:
                pass
            break

    return result


def get_available_on_demand_skills(
    persona_name: str,
    team: str = "omnia-data",
) -> dict[str, dict[str, Any]]:
    """Get metadata for all on-demand skills available to a persona.

    On-demand skills are loaded dynamically based on user queries
    rather than being included in the system prompt.

    Args:
        persona_name: Name of the persona ("developer", "support", etc.)
        team: Team identifier

    Returns:
        Dict mapping skill names to their metadata
    """
    import yaml

    on_demand_skills: dict[str, dict[str, Any]] = {}

    # Load persona definition to get on_demand_skills list
    persona_file = SKILLS_DIR / team / f"_persona_{persona_name}.yaml"
    if not persona_file.exists():
        return on_demand_skills

    try:
        persona_data = yaml.safe_load(persona_file.read_text(encoding="utf-8"))
        skill_names = persona_data.get("on_demand_skills", [])
    except Exception:
        return on_demand_skills

    # Load metadata for each on-demand skill
    for skill_name in skill_names:
        for search_pattern in SKILL_SEARCH_PATHS:
            path_str = search_pattern.format(team=team, skill=skill_name)
            path = SKILLS_DIR / path_str
            if path.exists():
                try:
                    raw_content = path.read_text(encoding="utf-8")
                    frontmatter, _ = parse_frontmatter(raw_content)
                    on_demand_skills[skill_name] = {
                        "name": frontmatter.get("name", skill_name),
                        "display_name": frontmatter.get("display_name", skill_name),
                        "description": frontmatter.get("description", ""),
                        "triggers": frontmatter.get("triggers", []),
                        "version": frontmatter.get("version", "1.0.0"),
                    }
                except Exception:
                    pass
                break

    return on_demand_skills
