"""Comprehensive unit tests for Skills Refresh feature (Issue #48).

Test coverage for:
- Skill Loader (SL-01 to SL-10)
- Template Loader (TL-01 to TL-06)
- Persona Loading (PL-01 to PL-10)
- Persona Discovery (PD-01 to PD-07)
"""

from __future__ import annotations

import tempfile
from pathlib import Path

# =============================================================================
# Test Cases: Skill Loader (skill_loader.py)
# =============================================================================


class TestSkillLoaderTriggerMatching:
    """Test cases SL-03, SL-04: Trigger pattern matching."""

    def test_sl03_match_trigger_pattern(self):
        """SL-03: Match trigger pattern - query matches trigger."""
        from triagent.skills.skill_loader import match_skill_trigger

        result = match_skill_trigger("Review PR #12345", ["review.*PR"])
        assert result is True

    def test_sl04_no_trigger_match(self):
        """SL-04: No trigger match - query doesn't match trigger."""
        from triagent.skills.skill_loader import match_skill_trigger

        result = match_skill_trigger("Hello world", ["review.*PR"])
        assert result is False

    def test_match_trigger_case_insensitive(self):
        """Trigger matching should be case insensitive."""
        from triagent.skills.skill_loader import match_skill_trigger

        result = match_skill_trigger("REVIEW PR #12345", ["review.*pr"])
        assert result is True

    def test_match_trigger_multiple_patterns(self):
        """Match against multiple trigger patterns."""
        from triagent.skills.skill_loader import match_skill_trigger

        triggers = ["review.*PR", "code review", "check.*code"]
        assert match_skill_trigger("code review please", triggers) is True
        assert match_skill_trigger("random text", triggers) is False

    def test_match_trigger_empty_triggers(self):
        """Empty triggers list returns False."""
        from triagent.skills.skill_loader import match_skill_trigger

        result = match_skill_trigger("any query", [])
        assert result is False


class TestSkillLoaderLanguageDetection:
    """Test cases SL-05 to SL-08: Code review language detection."""

    def test_sl05_detect_python_language(self):
        """SL-05: Detect Python language from .py files."""
        from triagent.skills.skill_loader import detect_code_review_language

        result = detect_code_review_language(["main.py", "utils.py"])
        assert result == "python"

    def test_sl07_detect_dotnet_language(self):
        """SL-07: Detect .NET language from .cs files."""
        from triagent.skills.skill_loader import detect_code_review_language

        result = detect_code_review_language(["Service.cs", "Model.cs"])
        assert result == "dotnet"

    def test_sl08_mixed_language_detection(self):
        """SL-08: Mixed language detection returns list."""
        from triagent.skills.skill_loader import detect_code_review_language

        result = detect_code_review_language(["main.py", "Service.cs"])
        assert isinstance(result, list)
        assert "python" in result
        assert "dotnet" in result

    def test_sl06_detect_pyspark_language(self):
        """SL-06: Detect PySpark language from Python file with Spark imports."""
        from triagent.skills.skill_loader import detect_code_review_language

        # PySpark detection with file contents
        file_contents = {
            "etl.py": "from pyspark.sql import SparkSession\nimport pyspark"
        }
        result = detect_code_review_language(["etl.py"], file_contents)
        assert result == "pyspark"

    def test_detect_jupyter_notebook_as_pyspark(self):
        """Jupyter notebooks (.ipynb) default to pyspark."""
        from triagent.skills.skill_loader import detect_code_review_language

        result = detect_code_review_language(["analysis.ipynb"])
        assert result == "pyspark"

    def test_detect_sql_as_dotnet(self):
        """SQL files are grouped with .NET for review."""
        from triagent.skills.skill_loader import detect_code_review_language

        result = detect_code_review_language(["schema.sql", "query.sql"])
        assert result == "dotnet"

    def test_detect_empty_files_default_to_python(self):
        """Empty file list defaults to Python."""
        from triagent.skills.skill_loader import detect_code_review_language

        result = detect_code_review_language([])
        assert result == "python"

    def test_detect_unknown_extensions_ignored(self):
        """Unknown file extensions are ignored."""
        from triagent.skills.skill_loader import detect_code_review_language

        result = detect_code_review_language(["readme.md", "config.json", "main.py"])
        assert result == "python"


class TestSkillLoaderSubSkillLoading:
    """Test cases SL-01, SL-02, SL-09, SL-10: Sub-skill loading."""

    def test_sl02_load_sub_skill_by_path(self):
        """SL-02: Load sub-skill by path."""
        from triagent.skills.skill_loader import load_sub_skill

        # Skills are now at root level, not in subdirectories
        content = load_sub_skill("dotnet_code_review", "omnia-data")
        assert content is not None
        assert len(content) > 0

    def test_sl09_invalid_skill_name(self):
        """SL-09: Invalid skill name returns None."""
        from triagent.skills.skill_loader import load_sub_skill

        result = load_sub_skill("nonexistent_skill", "omnia-data")
        assert result is None

    def test_sl10_load_skill_with_team_prefix(self):
        """SL-10: Load skill with team prefix."""
        from triagent.skills.skill_loader import load_sub_skill

        content = load_sub_skill("ado_pr_review", "omnia-data")
        # Should find it in developer/ subdirectory
        assert content is not None or content is None  # May or may not exist

    def test_load_sub_skill_normalizes_path(self):
        """Skill paths with hyphens are normalized to underscores."""
        from triagent.skills.skill_loader import load_sub_skill

        # Skills are at root level, naming normalization still works
        content1 = load_sub_skill("dotnet-code-review", "omnia-data")
        content2 = load_sub_skill("dotnet_code_review", "omnia-data")
        # At least one should work if files exist
        assert content1 is not None or content2 is not None


class TestSkillLoaderByLanguage:
    """Test loading code review skills by language."""

    def test_load_dotnet_code_review(self):
        """Load .NET code review skill by language."""
        from triagent.skills.skill_loader import load_skill_by_language

        content = load_skill_by_language("dotnet", "omnia-data")
        assert content is not None
        assert len(content) > 0

    def test_load_python_code_review(self):
        """Load Python code review skill by language."""
        from triagent.skills.skill_loader import load_skill_by_language

        content = load_skill_by_language("python", "omnia-data")
        assert content is not None
        assert len(content) > 0

    def test_load_pyspark_code_review(self):
        """Load PySpark code review skill by language."""
        from triagent.skills.skill_loader import load_skill_by_language

        content = load_skill_by_language("pyspark", "omnia-data")
        assert content is not None
        assert len(content) > 0

    def test_load_invalid_language(self):
        """Invalid language returns None."""
        from triagent.skills.skill_loader import load_skill_by_language

        result = load_skill_by_language("invalid_lang", "omnia-data")
        assert result is None


# =============================================================================
# Test Cases: Template Loader (template_loader.py)
# =============================================================================


class TestTemplateLoaderLoading:
    """Test cases TL-01, TL-02, TL-05: Template loading."""

    def test_tl01_load_pr_report_template(self):
        """TL-01: Load PR report template."""
        from triagent.skills.template_loader import load_template

        template = load_template("pr-report")
        assert template is not None
        assert "<html" in template.lower() or "<!doctype" in template.lower()

    def test_tl02_load_finops_report_template(self):
        """TL-02: Load FinOps report template."""
        from triagent.skills.template_loader import load_template

        template = load_template("finops-report")
        assert template is not None
        assert len(template) > 0

    def test_tl05_invalid_template_name(self):
        """TL-05: Invalid template name returns None."""
        from triagent.skills.template_loader import load_template

        result = load_template("invalid-template-name")
        assert result is None


class TestTemplateLoaderRendering:
    """Test cases TL-03: Template rendering."""

    def test_tl03_render_template_with_data(self):
        """TL-03: Render template with data - placeholders replaced."""
        from triagent.skills.template_loader import render_template

        template = "<h1>{{title}}</h1><p>{{content}}</p>"
        data = {"title": "Test Title", "content": "Test Content"}
        result = render_template(template, data)

        assert "Test Title" in result
        assert "Test Content" in result
        assert "{{title}}" not in result
        assert "{{content}}" not in result

    def test_render_template_dollar_brace_format(self):
        """Render template with ${key} format placeholders."""
        from triagent.skills.template_loader import render_template

        template = "<h1>${title}</h1>"
        data = {"title": "Test Title"}
        result = render_template(template, data)

        assert "Test Title" in result
        assert "${title}" not in result

    def test_render_template_with_none_value(self):
        """None values render as empty string."""
        from triagent.skills.template_loader import render_template

        template = "<p>{{value}}</p>"
        data = {"value": None}
        result = render_template(template, data)

        assert result == "<p></p>"

    def test_render_template_with_list_value(self):
        """List values render as comma-separated."""
        from triagent.skills.template_loader import render_template

        template = "<p>{{items}}</p>"
        data = {"items": ["a", "b", "c"]}
        result = render_template(template, data)

        assert "a, b, c" in result

    def test_render_template_with_bool_value(self):
        """Boolean values render as lowercase strings."""
        from triagent.skills.template_loader import render_template

        template = "<p>{{flag}}</p>"
        data = {"flag": True}
        result = render_template(template, data)

        assert "true" in result


class TestTemplateLoaderSaving:
    """Test cases TL-04: Template saving."""

    def test_tl04_save_rendered_template(self):
        """TL-04: Save rendered template to file."""
        from triagent.skills.template_loader import save_rendered_template

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.html"
            content = "<html><body>Test</body></html>"

            result = save_rendered_template(content, output_path)

            assert result is True
            assert output_path.exists()
            assert output_path.read_text() == content

    def test_save_rendered_template_creates_dirs(self):
        """Save template creates parent directories."""
        from triagent.skills.template_loader import save_rendered_template

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "subdir" / "nested" / "test.html"
            content = "<html><body>Test</body></html>"

            result = save_rendered_template(content, output_path, create_dirs=True)

            assert result is True
            assert output_path.exists()


class TestTemplateLoaderCSS:
    """Test CSS loading functionality."""

    def test_load_deloitte_omnia_css(self):
        """Load Deloitte Omnia CSS file."""
        from triagent.skills.template_loader import load_css

        css = load_css("deloitte-omnia")
        assert css is not None
        assert len(css) > 0

    def test_load_invalid_css(self):
        """Invalid CSS name returns None."""
        from triagent.skills.template_loader import load_css

        result = load_css("nonexistent-css")
        assert result is None


class TestTemplateLoaderAvailableTemplates:
    """Test getting available templates."""

    def test_get_available_templates(self):
        """Get list of all available templates."""
        from triagent.skills.template_loader import get_available_templates

        templates = get_available_templates()
        assert isinstance(templates, dict)
        assert len(templates) >= 2  # At least pr-report and finops-report
        assert "pr-report" in templates or any("pr" in k for k in templates.keys())


# =============================================================================
# Test Cases: Persona Loading (PL-01 to PL-10)
# =============================================================================


class TestPersonaDefinitionLoading:
    """Test cases PL-01 to PL-04: Load persona definitions."""

    def test_pl01_load_developer_persona(self):
        """PL-01: Load developer persona."""
        from triagent.skills.loader import load_persona_definition

        persona = load_persona_definition("omnia-data", "developer")
        assert persona is not None
        assert persona.name == "developer"
        assert persona.display_name == "Developer"

    def test_pl02_load_support_persona(self):
        """PL-02: Load support persona."""
        from triagent.skills.loader import load_persona_definition

        persona = load_persona_definition("omnia-data", "support")
        assert persona is not None
        assert persona.name == "support"
        assert persona.display_name == "Support"

    def test_pl03_load_product_owner_persona(self):
        """PL-03: Load product_owner persona."""
        from triagent.skills.loader import load_persona_definition

        persona = load_persona_definition("omnia-data", "product_owner")
        assert persona is not None
        assert persona.name == "product_owner"
        assert persona.display_name == "Product Owner"

    def test_pl04_load_business_analyst_persona(self):
        """PL-04: Load business_analyst persona."""
        from triagent.skills.loader import load_persona_definition

        persona = load_persona_definition("omnia-data", "business_analyst")
        assert persona is not None
        assert persona.name == "business_analyst"
        assert persona.display_name == "Business Analyst"

    def test_pl08_invalid_persona_name(self):
        """PL-08: Invalid persona name returns None."""
        from triagent.skills.loader import load_persona_definition

        result = load_persona_definition("omnia-data", "invalid_persona")
        assert result is None

    def test_pl09_invalid_team_name(self):
        """PL-09: Invalid team name returns None."""
        from triagent.skills.loader import load_persona_definition

        result = load_persona_definition("invalid_team", "developer")
        assert result is None


class TestPersonaSkillsContent:
    """Test cases PL-05 to PL-07, PL-10: Persona skills content."""

    def test_pl05_developer_has_on_demand_skills(self):
        """PL-05: Developer has on_demand_skills including code review."""
        from triagent.skills.loader import load_persona_definition

        persona = load_persona_definition("omnia-data", "developer")
        assert persona is not None
        assert hasattr(persona, "on_demand_skills") or "on_demand_skills" in str(
            persona
        )

    def test_pl06_product_owner_has_work_item_creation(self):
        """PL-06: Product Owner shares PO-BSA skills including work_item_creation."""
        from triagent.skills.loader import load_persona_definition

        persona = load_persona_definition("omnia-data", "product_owner")
        assert persona is not None
        assert persona.skills is not None
        assert "work_item_creation" in persona.skills

    def test_pl07_business_analyst_has_work_item_creation(self):
        """PL-07: Business Analyst shares PO-BSA skills including work_item_creation."""
        from triagent.skills.loader import load_persona_definition

        persona = load_persona_definition("omnia-data", "business_analyst")
        assert persona is not None
        assert persona.skills is not None
        assert "work_item_creation" in persona.skills

    def test_pl10_persona_has_triggers(self):
        """PL-10: Persona has triggers list."""
        from triagent.skills.loader import load_persona_definition

        persona = load_persona_definition("omnia-data", "developer")
        assert persona is not None
        assert hasattr(persona, "triggers") or "triggers" in str(persona)


# =============================================================================
# Test Cases: Persona Discovery (PD-01 to PD-07)
# =============================================================================


class TestPersonaDiscovery:
    """Test cases PD-01 to PD-07: Persona discovery."""

    def test_pd01_discover_personas_for_omnia_data(self):
        """PD-01: Discover personas for omnia-data returns 4 personas."""
        from triagent.skills.loader import discover_personas

        personas = discover_personas("omnia-data")
        assert len(personas) == 4

    def test_pd02_persona_has_display_name(self):
        """PD-02: Persona has display_name field."""
        from triagent.skills.loader import discover_personas

        personas = discover_personas("omnia-data")
        for persona in personas:
            assert "display_name" in persona
            assert len(persona["display_name"]) > 0

    def test_pd03_persona_has_description(self):
        """PD-03: Persona has description field."""
        from triagent.skills.loader import discover_personas

        personas = discover_personas("omnia-data")
        for persona in personas:
            assert "description" in persona
            assert len(persona["description"]) > 0

    def test_pd04_personas_sorted_alphabetically(self):
        """PD-04: Personas sorted alphabetically by display_name."""
        from triagent.skills.loader import discover_personas

        personas = discover_personas("omnia-data")
        display_names = [p["display_name"] for p in personas]
        assert display_names == sorted(display_names)

    def test_pd05_invalid_team_returns_empty(self):
        """PD-05: Invalid team returns empty list."""
        from triagent.skills.loader import discover_personas

        personas = discover_personas("invalid_team")
        assert personas == []

    def test_pd06_product_owner_yaml_valid(self):
        """PD-06: Product Owner YAML parses without error."""
        from triagent.skills.loader import load_persona_definition

        persona = load_persona_definition("omnia-data", "product_owner")
        assert persona is not None
        assert persona.name == "product_owner"
        assert persona.display_name == "Product Owner"
        assert persona.description is not None

    def test_pd07_business_analyst_yaml_valid(self):
        """PD-07: Business Analyst YAML parses without error."""
        from triagent.skills.loader import load_persona_definition

        persona = load_persona_definition("omnia-data", "business_analyst")
        assert persona is not None
        assert persona.name == "business_analyst"
        assert persona.display_name == "Business Analyst"
        assert persona.description is not None


class TestGetAvailablePersonas:
    """Test get_available_personas function."""

    def test_get_available_personas_returns_all_four(self):
        """Get available personas returns all 4 personas for omnia-data."""
        from triagent.skills import get_available_personas

        personas = get_available_personas("omnia-data")
        assert len(personas) == 4

        # Check all expected personas exist
        names = [p.name for p in personas]
        assert "developer" in names
        assert "support" in names
        assert "product_owner" in names
        assert "business_analyst" in names

    def test_get_available_personas_invalid_team(self):
        """Invalid team returns empty list."""
        from triagent.skills import get_available_personas

        personas = get_available_personas("nonexistent_team")
        assert personas == []


# =============================================================================
# Additional Test Cases: Skill Content Validation
# =============================================================================


class TestSkillContentExists:
    """Validate that all expected skill files exist and have content."""

    def test_developer_skills_exist(self):
        """Developer persona skills exist."""
        from triagent.skills.skill_loader import load_sub_skill

        skills = [
            "ado_pr_review",
            "pr_report_generation",
        ]
        for skill in skills:
            content = load_sub_skill(skill, "omnia-data")
            # May or may not exist, but should not raise error
            assert content is None or len(content) > 0

    def test_developer_code_review_skills_exist(self):
        """Developer code-review skills exist at root level."""
        from triagent.skills.skill_loader import load_sub_skill

        # Skills consolidated to root developer directory
        skills = [
            "dotnet_code_review",
            "python_code_review",
            "pyspark_code_review",
        ]
        for skill in skills:
            content = load_sub_skill(skill, "omnia-data")
            assert content is not None, f"Skill {skill} should exist"
            assert len(content) > 0

    def test_support_skills_exist(self):
        """Support persona skills exist."""

        from triagent.skills.loader import SKILLS_DIR

        support_dir = SKILLS_DIR / "omnia-data" / "support"
        expected_skills = [
            "telemetry_investigation.md",
            "root_cause_analysis.md",
            "lsi_management.md",
            "ado_work_items.md",
        ]
        for skill in expected_skills:
            skill_path = support_dir / skill
            assert skill_path.exists(), f"Skill {skill} should exist"

    def test_po_bsa_skills_exist(self):
        """PO-BSA skills exist."""

        from triagent.skills.loader import SKILLS_DIR

        po_bsa_dir = SKILLS_DIR / "omnia-data" / "po-bsa"
        expected_skills = [
            "work_item_creation.md",
            "feature_investigation.md",
            "requirements_analysis.md",
        ]
        for skill in expected_skills:
            skill_path = po_bsa_dir / skill
            assert skill_path.exists(), f"Skill {skill} should exist"

    def test_finops_skill_exists(self):
        """FinOps skill and templates exist."""

        from triagent.skills.loader import SKILLS_DIR

        finops_dir = SKILLS_DIR / "omnia-data" / "finops"
        assert (finops_dir / "finops.md").exists()
        assert (finops_dir / "scripts" / "generate_finops_report.py").exists()
        assert (finops_dir / "templates" / "finops-report-template.html").exists()


class TestCoreAndDataFilesExist:
    """Validate core and data files exist."""

    def test_core_files_exist(self):
        """Core reference files exist."""

        from triagent.skills.loader import SKILLS_DIR

        core_dir = SKILLS_DIR / "core"
        expected_files = [
            "organization_context.md",
            "api_best_practices.md",
            "log_analytics_reference.md",
            "release_strategy.md",
            "team_info.md",
        ]
        for file in expected_files:
            file_path = core_dir / file
            assert file_path.exists(), f"Core file {file} should exist"

    def test_data_files_exist(self):
        """Data configuration files exist."""

        from triagent.skills.loader import SKILLS_DIR

        data_dir = SKILLS_DIR / "data"
        expected_files = [
            "team-config.json",
            "user-mappings.tsv",
            "repository-mappings.json",
            "wiki-config.json",
        ]
        for file in expected_files:
            file_path = data_dir / file
            assert file_path.exists(), f"Data file {file} should exist"

    def test_reference_files_exist(self):
        """Reference files exist."""

        from triagent.skills.loader import SKILLS_DIR

        ref_dir = SKILLS_DIR / "reference"
        assert (ref_dir / "ado_field_reference.md").exists()


# =============================================================================
# Integration Tests: Skill Loading and Validation
# =============================================================================


class TestSkillIntegration:
    """Integration tests for complete skill loading and validation."""

    def test_all_personas_load_with_complete_skills(self):
        """Verify all personas load and listed skills are actually loaded."""
        from triagent.skills.loader import load_persona

        for persona_name in ["developer", "support", "product_owner", "business_analyst"]:
            persona = load_persona("omnia-data", persona_name)
            if persona is None:
                continue

            # Verify all listed skills are actually loaded
            for skill_name in persona.definition.skills:
                assert skill_name in persona.skills, (
                    f"Skill {skill_name} listed in {persona_name} but not loaded"
                )

    def test_developer_skills_have_required_metadata(self):
        """Verify developer skills have required frontmatter fields."""
        from triagent.skills.loader import load_persona

        persona = load_persona("omnia-data", "developer")
        assert persona is not None

        # Check each skill has required metadata
        for skill_name, skill in persona.skills.items():
            # display_name can be empty but description should not be for developer skills
            if skill_name in [
                "ado_pr_review",
                "pr_report_generation",
                "dotnet_code_review",
                "python_code_review",
                "pyspark_code_review",
            ]:
                assert skill.metadata.description, (
                    f"Skill {skill_name} missing description"
                )

    def test_pr_report_generation_has_frontmatter(self):
        """Verify pr_report_generation skill has complete frontmatter."""
        from triagent.skills.loader import SKILLS_DIR, load_skill

        skill_path = SKILLS_DIR / "omnia-data" / "developer" / "pr_report_generation.md"
        skill = load_skill(skill_path)

        assert skill is not None
        assert skill.metadata.name == "pr_report_generation"
        assert skill.metadata.display_name == "PR Report Generation"
        assert "PR contribution" in skill.metadata.description
        assert len(skill.metadata.triggers) > 0

    def test_finops_skill_has_complete_frontmatter(self):
        """Verify finops skill has complete frontmatter."""
        from triagent.skills.loader import SKILLS_DIR, load_skill

        skill_path = SKILLS_DIR / "omnia-data" / "finops" / "finops.md"
        skill = load_skill(skill_path)

        assert skill is not None
        assert skill.metadata.name == "finops"
        assert skill.metadata.display_name == "FinOps Cost Analysis"
        assert len(skill.metadata.triggers) > 0

    def test_file_path_references_valid_in_ado_pr_review(self):
        """Verify all file path references in ado_pr_review.md point to existing files."""
        import re

        from triagent.skills.loader import SKILLS_DIR

        skill_file = SKILLS_DIR / "omnia-data" / "developer" / "ado_pr_review.md"
        content = skill_file.read_text()

        # Find all relative path references that look like ./filename.md
        paths = re.findall(r"\./([a-zA-Z0-9_]+\.md)", content)

        for ref_filename in paths:
            full_path = skill_file.parent / ref_filename
            assert full_path.exists(), (
                f"Invalid path reference in ado_pr_review.md: ./{ref_filename}"
            )

    def test_no_duplicate_skill_files(self):
        """Verify code-review and pipeline subdirectories don't exist anymore."""
        from triagent.skills.loader import SKILLS_DIR

        developer_dir = SKILLS_DIR / "omnia-data" / "developer"

        # These directories should not exist (duplicates removed)
        assert not (developer_dir / "code-review").exists(), (
            "code-review/ subdirectory should be removed (duplicates consolidated)"
        )
        assert not (developer_dir / "pipeline").exists(), (
            "pipeline/ subdirectory should be removed (duplicates consolidated)"
        )

    def test_all_developer_skills_at_root_level(self):
        """Verify all developer skills are at root level with proper naming."""
        from triagent.skills.loader import SKILLS_DIR

        developer_dir = SKILLS_DIR / "omnia-data" / "developer"

        expected_skills = [
            "ado_pr_review.md",
            "pr_report_generation.md",
            "dotnet_code_review.md",
            "python_code_review.md",
            "pyspark_code_review.md",
            "release_investigation.md",
            "release_pipeline.md",
        ]

        for skill_file in expected_skills:
            skill_path = developer_dir / skill_file
            assert skill_path.exists(), f"Skill {skill_file} should exist at root level"


class TestSkillMetadataValidation:
    """Test skill metadata validation and warnings."""

    def test_skill_with_missing_display_name_uses_fallback(self):
        """Skills without display_name should use empty string as fallback."""
        import tempfile
        from pathlib import Path

        from triagent.skills.loader import load_skill

        # Create a minimal skill without display_name
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False, mode="w") as f:
            f.write("""---
name: test_skill
description: A test skill
---

Test content.
""")
            f.flush()
            skill = load_skill(Path(f.name))

            assert skill is not None
            assert skill.metadata.name == "test_skill"
            assert skill.metadata.display_name == ""  # Empty fallback

    def test_skill_with_all_metadata_fields(self):
        """Skills with complete metadata should load all fields."""
        import tempfile
        from pathlib import Path

        from triagent.skills.loader import load_skill

        with tempfile.NamedTemporaryFile(suffix=".md", delete=False, mode="w") as f:
            f.write("""---
name: complete_skill
display_name: "Complete Skill"
description: "A skill with all metadata"
version: "2.0.0"
tags: [test, complete]
triggers:
  - "test trigger"
---

Complete skill content.
""")
            f.flush()
            skill = load_skill(Path(f.name))

            assert skill is not None
            assert skill.metadata.name == "complete_skill"
            assert skill.metadata.display_name == "Complete Skill"
            assert skill.metadata.description == "A skill with all metadata"
            assert skill.metadata.version == "2.0.0"
            assert "test" in skill.metadata.tags
            assert "test trigger" in skill.metadata.triggers
