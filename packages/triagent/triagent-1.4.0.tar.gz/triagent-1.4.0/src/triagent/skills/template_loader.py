"""HTML template loading and rendering for skill-generated reports.

This module provides utilities for:
- Loading HTML templates from skill directories
- Rendering templates with data placeholders
- Saving rendered templates to files
- Managing template paths for different skill types
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any

# Base paths for templates
SKILLS_DIR = Path(__file__).parent
OMNIA_DATA_DIR = SKILLS_DIR / "omnia-data"
TEMPLATES_DIR = OMNIA_DATA_DIR / "templates"
FINOPS_TEMPLATES_DIR = OMNIA_DATA_DIR / "finops" / "templates"

# Template name to file path mapping
TEMPLATE_MAP: dict[str, Path] = {
    "pr-report": TEMPLATES_DIR / "pr-report-template.html",
    "finops-report": FINOPS_TEMPLATES_DIR / "finops-report-template.html",
}

# CSS file mapping
CSS_MAP: dict[str, Path] = {
    "deloitte-omnia": TEMPLATES_DIR / "deloitte-omnia.css",
    "deloitte-omnia-finops": FINOPS_TEMPLATES_DIR / "deloitte-omnia-finops.css",
}


def load_template(template_name: str) -> str | None:
    """Load an HTML template by name.

    Args:
        template_name: Name of the template (e.g., "pr-report", "finops-report")

    Returns:
        Template content as string, or None if not found

    Example:
        >>> template = load_template("pr-report")
        >>> if template:
        ...     rendered = render_template(template, {"title": "PR Report"})
    """
    template_path = TEMPLATE_MAP.get(template_name)

    if template_path is None:
        # Try to find by file name in templates directories
        for templates_dir in [TEMPLATES_DIR, FINOPS_TEMPLATES_DIR]:
            potential_path = templates_dir / f"{template_name}.html"
            if potential_path.exists():
                template_path = potential_path
                break
            # Also try with -template suffix
            potential_path = templates_dir / f"{template_name}-template.html"
            if potential_path.exists():
                template_path = potential_path
                break

    if template_path is None or not template_path.exists():
        return None

    try:
        return template_path.read_text(encoding="utf-8")
    except Exception:
        return None


def load_css(css_name: str) -> str | None:
    """Load a CSS file by name.

    Args:
        css_name: Name of the CSS file (e.g., "deloitte-omnia")

    Returns:
        CSS content as string, or None if not found
    """
    css_path = CSS_MAP.get(css_name)

    if css_path is None:
        # Try to find by file name
        for templates_dir in [TEMPLATES_DIR, FINOPS_TEMPLATES_DIR]:
            potential_path = templates_dir / f"{css_name}.css"
            if potential_path.exists():
                css_path = potential_path
                break

    if css_path is None or not css_path.exists():
        return None

    try:
        return css_path.read_text(encoding="utf-8")
    except Exception:
        return None


def render_template(template: str, data: dict[str, Any]) -> str:
    """Render a template by replacing placeholders with data values.

    Supports multiple placeholder formats:
    - {{key}} - Standard placeholder
    - ${key} - Alternative placeholder
    - {key} - Simple placeholder

    Args:
        template: Template string with placeholders
        data: Dict mapping placeholder keys to values

    Returns:
        Rendered template with placeholders replaced

    Example:
        >>> template = "<h1>{{title}}</h1><p>{{content}}</p>"
        >>> render_template(template, {"title": "Hello", "content": "World"})
        "<h1>Hello</h1><p>World</p>"
    """
    result = template

    for key, value in data.items():
        # Convert value to string
        str_value = _format_value(value)

        # Replace {{key}} format
        result = result.replace(f"{{{{{key}}}}}", str_value)

        # Replace ${key} format
        result = result.replace(f"${{{key}}}", str_value)

        # Replace {key} format (be careful with CSS/JS)
        # Only replace if not inside curly braces (not CSS)
        pattern = rf"(?<![{{]){{{key}}}(?![}}])"
        result = re.sub(pattern, str_value, result)

    return result


def _format_value(value: Any) -> str:
    """Format a value for template insertion.

    Args:
        value: Value to format

    Returns:
        Formatted string representation
    """
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(value, list):
        return ", ".join(str(v) for v in value)
    if isinstance(value, dict):
        # For dicts, return JSON-like string
        import json

        return json.dumps(value)
    return str(value)


def render_template_with_css(
    template: str,
    data: dict[str, Any],
    css_name: str | None = None,
) -> str:
    """Render a template and optionally inline CSS.

    Args:
        template: Template string with placeholders
        data: Dict mapping placeholder keys to values
        css_name: Optional CSS file name to inline

    Returns:
        Rendered template with CSS inlined if specified
    """
    rendered = render_template(template, data)

    if css_name:
        css_content = load_css(css_name)
        if css_content:
            # Insert CSS in <head> section
            css_tag = f"<style>\n{css_content}\n</style>"
            if "<head>" in rendered:
                rendered = rendered.replace("<head>", f"<head>\n{css_tag}")
            elif "<html>" in rendered:
                rendered = rendered.replace("<html>", f"<html>\n<head>{css_tag}</head>")
            else:
                rendered = f"{css_tag}\n{rendered}"

    return rendered


def save_rendered_template(
    content: str,
    output_path: str | Path,
    create_dirs: bool = True,
) -> bool:
    """Save rendered template content to a file.

    Args:
        content: Rendered HTML content
        output_path: Path to save the file
        create_dirs: Whether to create parent directories if they don't exist

    Returns:
        True if saved successfully, False otherwise

    Example:
        >>> content = render_template(template, data)
        >>> save_rendered_template(content, "/path/to/report.html")
        True
    """
    try:
        path = Path(output_path)

        if create_dirs:
            path.parent.mkdir(parents=True, exist_ok=True)

        path.write_text(content, encoding="utf-8")
        return True
    except Exception:
        return False


def get_available_templates() -> dict[str, dict[str, Any]]:
    """Get information about all available templates.

    Returns:
        Dict mapping template names to their metadata
    """
    templates: dict[str, dict[str, Any]] = {}

    # Check registered templates
    for name, path in TEMPLATE_MAP.items():
        if path.exists():
            templates[name] = {
                "name": name,
                "path": str(path),
                "exists": True,
                "size": path.stat().st_size,
            }

    # Also scan template directories for additional templates
    for templates_dir in [TEMPLATES_DIR, FINOPS_TEMPLATES_DIR]:
        if templates_dir.exists():
            for html_file in templates_dir.glob("*.html"):
                name = html_file.stem.replace("-template", "")
                if name not in templates:
                    templates[name] = {
                        "name": name,
                        "path": str(html_file),
                        "exists": True,
                        "size": html_file.stat().st_size,
                    }

    return templates


def create_report_from_template(
    template_name: str,
    data: dict[str, Any],
    output_path: str | Path | None = None,
    css_name: str | None = None,
) -> tuple[str, str | None]:
    """Create a complete report from a template.

    Convenience function that loads, renders, and optionally saves a report.

    Args:
        template_name: Name of the template to use
        data: Data to render into the template
        output_path: Optional path to save the rendered report
        css_name: Optional CSS file to inline

    Returns:
        Tuple of (rendered_content, output_path or None)

    Example:
        >>> content, path = create_report_from_template(
        ...     "pr-report",
        ...     {"title": "PR Report", "prs": pr_data},
        ...     output_path="/tmp/report.html",
        ...     css_name="deloitte-omnia"
        ... )
    """
    # Load template
    template = load_template(template_name)
    if template is None:
        raise ValueError(f"Template not found: {template_name}")

    # Add default data
    default_data = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "generator": "Triagent Skills System",
    }
    merged_data = {**default_data, **data}

    # Render
    if css_name:
        rendered = render_template_with_css(template, merged_data, css_name)
    else:
        rendered = render_template(template, merged_data)

    # Save if path provided
    saved_path: str | None = None
    if output_path:
        if save_rendered_template(rendered, output_path):
            saved_path = str(output_path)

    return rendered, saved_path
