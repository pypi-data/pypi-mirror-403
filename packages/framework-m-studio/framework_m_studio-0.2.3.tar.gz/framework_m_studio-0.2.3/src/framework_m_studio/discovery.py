"""DocType Discovery Service.

This module provides functionality to scan a project for DocType files.
It delegates parsing to the codegen.parser module to avoid code duplication.

Features:
- Scan directories for *.py files containing DocType classes
- Return structured JSON for Studio UI (list view)

For deep parsing of individual files, use codegen.parser.parse_doctype() directly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from fnmatch import fnmatch
from pathlib import Path
from typing import Any

from framework_m_studio.codegen.parser import parse_doctype

# =============================================================================
# Data Models (lightweight for scanning)
# =============================================================================


@dataclass
class FieldInfo:
    """Parsed field information from a DocType class."""

    name: str
    type: str
    default: str | None = None
    required: bool = True
    description: str | None = None
    label: str | None = None
    validators: dict[str, Any] = field(default_factory=dict)


@dataclass
class DocTypeInfo:
    """Parsed DocType information for list view."""

    name: str
    module: str
    file_path: str
    fields: list[FieldInfo] = field(default_factory=list)
    docstring: str | None = None
    meta: dict[str, Any] = field(default_factory=dict)


# =============================================================================
# Public API
# =============================================================================


def parse_doctype_file(file_path: Path) -> list[DocTypeInfo]:
    """Parse a Python file and extract DocType definitions.

    Delegates to codegen.parser.parse_doctype() and converts to DocTypeInfo.

    Args:
        file_path: Path to the Python file

    Returns:
        List of DocTypeInfo objects found in the file
    """
    try:
        schema = parse_doctype(file_path)
    except (FileNotFoundError, ValueError):
        return []

    # Convert parser schema to DocTypeInfo
    fields = [
        FieldInfo(
            name=f["name"],
            type=f["type"],
            default=f.get("default"),
            required=f.get("required", True),
            description=f.get("description"),
            label=f.get("label"),
            validators=f.get("validators", {}),
        )
        for f in schema.get("fields", [])
    ]

    doctype = DocTypeInfo(
        name=schema["name"],
        module=schema.get("module", ""),
        file_path=schema.get("file_path", str(file_path)),
        fields=fields,
        docstring=schema.get("docstring"),
        meta=schema.get("config", {}),
    )

    return [doctype]


def scan_doctypes(
    root_dir: Path,
    exclude_patterns: list[str] | None = None,
) -> list[DocTypeInfo]:
    """Scan a directory tree for DocType definitions.

    Args:
        root_dir: Root directory to scan
        exclude_patterns: Glob patterns to exclude (e.g., ["**/test_*"])

    Returns:
        List of all DocTypeInfo objects found
    """
    exclude_patterns = exclude_patterns or [
        "**/test_*.py",
        "**/tests/**",
        "**/__pycache__/**",
        "**/.venv/**",
        "**/node_modules/**",
    ]

    doctypes: list[DocTypeInfo] = []

    # Find all Python files
    for py_file in root_dir.rglob("*.py"):
        relative_path = str(py_file.relative_to(root_dir))
        path_parts = relative_path.split("/")

        # Check if file matches any exclusion pattern
        excluded = False

        # Check path segments for excluded directories
        for part in path_parts:
            if part in ("tests", "__pycache__", ".venv", "node_modules"):
                excluded = True
                break
            if part.startswith("test_") and part.endswith(".py"):
                excluded = True
                break

        # Also check fnmatch patterns
        if not excluded:
            for pattern in exclude_patterns:
                if fnmatch(relative_path, pattern):
                    excluded = True
                    break

        if excluded:
            continue

        # Quick check: does file likely contain a DocType?
        try:
            content = py_file.read_text(encoding="utf-8")
            if "BaseDocType" not in content and "DocType" not in content:
                continue
        except (OSError, UnicodeDecodeError):
            continue

        # Parse and extract DocTypes (delegates to parser.py)
        file_doctypes = parse_doctype_file(py_file)
        doctypes.extend(file_doctypes)

    return doctypes


def doctype_to_dict(doctype: DocTypeInfo) -> dict[str, Any]:
    """Convert DocTypeInfo to dictionary for JSON serialization."""
    return {
        "name": doctype.name,
        "module": doctype.module,
        "file_path": doctype.file_path,
        "docstring": doctype.docstring,
        "fields": [
            {
                "name": f.name,
                "type": f.type,
                "default": f.default,
                "required": f.required,
                "description": f.description,
                "label": f.label,
                "validators": f.validators,
            }
            for f in doctype.fields
        ],
        "meta": doctype.meta,
    }


__all__ = [
    "DocTypeInfo",
    "FieldInfo",
    "doctype_to_dict",
    "parse_doctype_file",
    "scan_doctypes",
]
