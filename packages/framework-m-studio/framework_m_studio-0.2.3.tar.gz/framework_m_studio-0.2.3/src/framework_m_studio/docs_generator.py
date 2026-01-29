"""Documentation Generator for Framework M.

Generates API documentation from DocTypes and Controllers.
Supports markdown output and MkDocs integration.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen


def format_field_table(fields: list[dict[str, Any]]) -> str:
    """Format fields as a markdown table.

    Args:
        fields: List of field dictionaries.

    Returns:
        Markdown table string.
    """
    if not fields:
        return "_No fields defined._\n"

    lines = [
        "| Field | Type | Required | Description | Validators |",
        "|-------|------|----------|-------------|------------|",
    ]

    for field in fields:
        name = field.get("name", "")
        field_type = field.get("type", "str")
        required = "✓" if field.get("required", True) else ""
        description = field.get("description", "") or "-"

        # Format validators
        validators = field.get("validators", {})
        if validators:
            validator_strs = []
            if validators.get("min_value") is not None:
                validator_strs.append(f"min: {validators['min_value']}")
            if validators.get("max_value") is not None:
                validator_strs.append(f"max: {validators['max_value']}")
            if validators.get("min_length") is not None:
                validator_strs.append(f"minLen: {validators['min_length']}")
            if validators.get("max_length") is not None:
                validator_strs.append(f"maxLen: {validators['max_length']}")
            if validators.get("pattern"):
                validator_strs.append(f"pattern: `{validators['pattern']}`")
            validators_str = ", ".join(validator_strs) if validator_strs else "-"
        else:
            validators_str = "-"

        lines.append(
            f"| {name} | {field_type} | {required} | {description} | {validators_str} |"
        )

    return "\n".join(lines) + "\n"


def format_meta_section(meta: dict[str, Any]) -> str:
    """Format Meta configuration as markdown.

    Args:
        meta: Meta configuration dictionary.

    Returns:
        Markdown string.
    """
    if not meta:
        return ""

    lines = ["## Configuration", "", "| Setting | Value |", "|---------|-------|"]

    settings = [
        ("Table Name", meta.get("tablename")),
        ("Naming Pattern", meta.get("name_pattern")),
        ("Submittable", meta.get("is_submittable")),
        ("Track Changes", meta.get("track_changes")),
    ]

    for setting, value in settings:
        if value is not None:
            lines.append(f"| {setting} | `{value}` |")

    if len(lines) > 4:  # Has at least one setting
        lines.append("")
        return "\n".join(lines)
    return ""


def generate_doctype_markdown(doctype_info: dict[str, Any]) -> str:
    """Generate markdown documentation for a DocType.

    Args:
        doctype_info: DocType information dictionary.

    Returns:
        Markdown string.
    """
    name = doctype_info.get("name", "Unknown")
    docstring = doctype_info.get("docstring", "")
    fields = doctype_info.get("fields", [])
    meta = doctype_info.get("meta", {})

    lines = [
        f"# {name}",
        "",
    ]

    if docstring:
        lines.extend([docstring, ""])

    # Fields section
    lines.extend(
        [
            "## Fields",
            "",
            format_field_table(fields),
        ]
    )

    # Meta configuration section
    meta_section = format_meta_section(meta)
    if meta_section:
        lines.append(meta_section)

    # Controller info placeholder
    lines.extend(
        [
            "## Controller",
            "",
            "Controller hooks are implemented in `*_controller.py` files.",
            "Available lifecycle hooks:",
            "",
            "- `validate()` - Called before save, raise exceptions for validation errors",
            "- `before_insert()` - Called before inserting a new document",
            "- `after_insert()` - Called after successfully inserting",
            "- `before_save()` - Called before saving (insert or update)",
            "- `after_save()` - Called after saving",
            "- `before_delete()` - Called before deleting",
            "- `after_delete()` - Called after deleting",
            "",
        ]
    )

    return "\n".join(lines)


def generate_index(doctypes: list[str]) -> str:
    """Generate index.md with links to all DocTypes.

    Args:
        doctypes: List of DocType names.

    Returns:
        Index markdown string.
    """
    lines = [
        "# API Reference",
        "",
        "## DocTypes",
        "",
    ]

    for name in sorted(doctypes):
        filename = name.lower() + ".md"
        lines.append(f"- [{name}]({filename})")

    lines.append("")
    return "\n".join(lines)


def generate_api_reference(
    doctypes: list[dict[str, Any]],
    output_dir: Path,
) -> None:
    """Generate API reference documentation for all DocTypes.

    Args:
        doctypes: List of DocType info dictionaries.
        output_dir: Output directory for markdown files.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    doctype_names = []

    for doctype in doctypes:
        name = doctype.get("name", "Unknown")
        doctype_names.append(name)

        markdown = generate_doctype_markdown(doctype)
        filename = name.lower() + ".md"
        (output_dir / filename).write_text(markdown)

    # Generate index
    index_md = generate_index(doctype_names)
    (output_dir / "index.md").write_text(index_md)


def export_openapi_json(
    openapi_url: str,
    output_file: Path,
    *,
    timeout: int = 30,
) -> None:
    """Export OpenAPI JSON from a running app.

    Args:
        openapi_url: URL to fetch OpenAPI schema from.
        output_file: Output file path for JSON.
        timeout: Request timeout in seconds.
    """
    request = Request(openapi_url)
    request.add_header("Accept", "application/json")

    with urlopen(request, timeout=timeout) as response:
        schema = json.loads(response.read().decode("utf-8"))

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(schema, indent=2))


def run_docs_generate(
    output: str = "./docs/api",
    project_root: str | None = None,
    openapi_url: str | None = None,
    build_site: bool = False,
) -> None:
    """Run the documentation generator.

    Args:
        output: Output directory for documentation.
        project_root: Project root directory (for DocType discovery).
        openapi_url: Optional OpenAPI URL to export.
        build_site: If True, run mkdocs build if available.
    """
    from framework_m_studio.discovery import doctype_to_dict, scan_doctypes

    output_dir = Path(output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Determine project root
    root = Path(project_root) if project_root else Path.cwd()

    # Scan for DocTypes
    doctypes = scan_doctypes(root)
    doctype_infos = [doctype_to_dict(dt) for dt in doctypes]

    # Generate API reference
    generate_api_reference(doctype_infos, output_dir)

    print(f"📚 Generated documentation for {len(doctypes)} DocTypes")
    print(f"   Output: {output_dir}")

    # Export OpenAPI if URL provided
    if openapi_url:
        openapi_file = output_dir / "openapi.json"
        try:
            export_openapi_json(openapi_url, openapi_file)
            print(f"   OpenAPI: {openapi_file}")
        except Exception as e:
            print(f"   ⚠️  Failed to export OpenAPI: {e}")

    # Run mkdocs build if requested
    if build_site:
        run_mkdocs_build(root)


def run_mkdocs_build(project_root: Path) -> bool:
    """Run mkdocs build if mkdocs is installed.

    Args:
        project_root: Project root directory.

    Returns:
        True if build succeeded, False otherwise.
    """
    import shutil
    import subprocess

    # Check if mkdocs is available
    mkdocs_path = shutil.which("mkdocs")
    if not mkdocs_path:
        print("   [i] mkdocs not found, skipping site build")
        print("      Install with: pip install mkdocs-material")
        return False

    # Check if mkdocs.yml exists
    mkdocs_config = project_root / "mkdocs.yml"
    if not mkdocs_config.exists():
        print("   [i] No mkdocs.yml found, skipping site build")
        return False

    # Run mkdocs build
    print("   🔨 Building documentation site...")
    try:
        result = subprocess.run(
            [mkdocs_path, "build"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            print("   ✅ Site built successfully")
            return True
        else:
            print(f"   ❌ mkdocs build failed: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("   ❌ mkdocs build timed out")
        return False
    except Exception as e:
        print(f"   ❌ mkdocs build error: {e}")
        return False
