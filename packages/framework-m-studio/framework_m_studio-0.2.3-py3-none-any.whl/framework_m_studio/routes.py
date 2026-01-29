"""Studio API Routes - File System API.

This module provides the REST API for DocType file operations:
- GET /studio/api/doctypes - List all DocTypes in project
- GET /studio/api/doctype/{name} - Get DocType schema
- POST /studio/api/doctype/{name} - Create/update DocType
- DELETE /studio/api/doctype/{name} - Delete DocType
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, ClassVar

from litestar import Controller, delete, get, post
from litestar.exceptions import NotFoundException
from pydantic import BaseModel

from framework_m_studio.discovery import (
    doctype_to_dict,
    scan_doctypes,
)

# =============================================================================
# Request/Response Models
# =============================================================================


class ValidatorSchema(BaseModel):
    """Validator constraints for a field."""

    min_length: int | None = None
    max_length: int | None = None
    pattern: str | None = None
    min_value: float | None = None
    max_value: float | None = None


class FieldSchema(BaseModel):
    """Field definition for DocType creation/update."""

    name: str
    type: str
    label: str | None = None
    default: str | None = None
    required: bool = True
    description: str | None = None
    hidden: bool = False
    read_only: bool = False
    validators: ValidatorSchema | None = None


class DocTypeSchema(BaseModel):
    """DocType schema for creation/update."""

    name: str
    module: str | None = None
    docstring: str | None = None
    fields: list[FieldSchema] = []


class DocTypeListResponse(BaseModel):
    """Response for listing DocTypes."""

    doctypes: list[dict[str, Any]]
    count: int
    project_root: str


class DocTypeResponse(BaseModel):
    """Response for single DocType."""

    name: str
    module: str
    file_path: str
    docstring: str | None
    fields: list[dict[str, Any]]
    meta: dict[str, Any]


class CreateDocTypeRequest(BaseModel):
    """Request body for creating a DocType."""

    name: str
    app: str | None = None
    docstring: str | None = None
    fields: list[FieldSchema] = []


class MessageResponse(BaseModel):
    """Generic message response."""

    message: str
    file_path: str | None = None


# =============================================================================
# Project Root Detection
# =============================================================================


def get_project_root() -> Path:
    """Get the project root directory.

    Priority:
    1. If CWD has src/doctypes directory, use CWD (local app mode)
    2. If CWD has doctypes directory, use CWD
    3. Look for pyproject.toml or .git in CWD only (don't traverse up)
    4. Fall back to CWD

    This ensures Studio scans only the current directory, not parent repos.
    """
    cwd = Path.cwd()

    # Priority 1: CWD has src/doctypes (standard app structure)
    if (cwd / "src" / "doctypes").exists():
        return cwd

    # Priority 2: CWD has doctypes directly
    if (cwd / "doctypes").exists():
        return cwd

    # Priority 3: CWD has project markers (don't traverse up!)
    if (cwd / "pyproject.toml").exists() or (cwd / ".git").exists():
        return cwd

    # Fall back to CWD
    return cwd


# =============================================================================
# File System API Controller
# =============================================================================


class DocTypeController(Controller):
    """Controller for DocType file system operations."""

    path = "/studio/api"
    tags: ClassVar[list[str]] = ["Studio - DocTypes"]  # type: ignore[misc]

    @get("/doctypes")
    async def list_doctypes(self) -> DocTypeListResponse:
        """List all DocTypes in the project.

        Scans the project for Python files containing DocType class definitions.
        """
        project_root = get_project_root()

        # Scan for DocTypes
        doctypes = scan_doctypes(project_root)

        return DocTypeListResponse(
            doctypes=[doctype_to_dict(dt) for dt in doctypes],
            count=len(doctypes),
            project_root=str(project_root),
        )

    @get("/doctype/{name:str}")
    async def get_doctype(self, name: str) -> DocTypeResponse:
        """Get a specific DocType by name.

        Args:
            name: DocType class name (e.g., "Todo", "User")
        """
        project_root = get_project_root()

        # Scan for DocTypes and find the matching one
        doctypes = scan_doctypes(project_root)

        for doctype in doctypes:
            if doctype.name == name:
                # Helper to clean validators
                def clean_validators(
                    validators: dict[str, Any],
                ) -> dict[str, Any] | None:
                    if not validators:
                        return None
                    # Remove None/empty values
                    cleaned = {k: v for k, v in validators.items() if v is not None}
                    return cleaned if cleaned else None

                return DocTypeResponse(
                    name=doctype.name,
                    module=doctype.module,
                    file_path=doctype.file_path,
                    docstring=doctype.docstring,
                    fields=[
                        {
                            "name": f.name,
                            "type": f.type,
                            "default": f.default,
                            "required": f.required,
                            "label": f.label,
                            "description": f.description,
                            "validators": clean_validators(f.validators),
                        }
                        for f in doctype.fields
                    ],
                    meta=doctype.meta,
                )

        raise NotFoundException(f"DocType '{name}' not found")

    @post("/doctype/{name:str}")
    async def create_or_update_doctype(
        self,
        name: str,
        data: CreateDocTypeRequest,
    ) -> MessageResponse:
        """Create or update a DocType.

        Creates a folder structure with:
        - doctype.py: DocType class definition
        - controller.py: Controller with lifecycle hooks
        - __init__.py: Package exports
        - test_<name>.py: Test file

        Args:
            name: Original DocType class name (from URL path)
            data: DocType schema including fields (data.name is the new name)
        """
        project_root = get_project_root()

        # Sanitize the DocType name for valid Python identifier
        # e.g., "Sales Invoice" -> class "SalesInvoice", folder "sales_invoice"
        sanitized_class_name = _sanitize_doctype_name(data.name)
        sanitized_folder_name = _to_snake_case(sanitized_class_name)

        # Update the data name to the sanitized version
        data.name = sanitized_class_name

        # Check if this is a rename operation
        is_rename = name != sanitized_class_name
        old_folder_path = None

        if is_rename:
            # Find the old folder and mark for deletion
            doctypes = scan_doctypes(project_root)
            for doctype in doctypes:
                if doctype.name == name:
                    old_file = Path(doctype.file_path)
                    # Check if it's in a folder structure or flat file
                    if old_file.parent.name == _to_snake_case(name):
                        old_folder_path = old_file.parent
                    else:
                        # Old flat file structure - delete both files
                        old_folder_path = None
                        if old_file.exists():
                            old_file.unlink()
                        old_controller = (
                            old_file.parent / f"{old_file.stem}_controller.py"
                        )
                        if old_controller.exists():
                            old_controller.unlink()
                    break

        # Determine target directory
        if data.app:
            # Use specified app directory
            target_dir = project_root / data.app / "src"
            if not target_dir.exists():
                target_dir = project_root / data.app
        else:
            # Default to src/
            target_dir = project_root / "src"
            if not target_dir.exists():
                target_dir = project_root

        # Create folder structure: src/doctypes/<name>/
        doctype_folder = target_dir / "doctypes" / sanitized_folder_name
        doctype_folder.mkdir(parents=True, exist_ok=True)

        # Generate and write doctype.py
        doctype_code = _generate_doctype_code(data)
        (doctype_folder / "doctype.py").write_text(doctype_code, encoding="utf-8")

        # Generate and write controller.py
        controller_code = _generate_controller_code(sanitized_class_name)
        (doctype_folder / "controller.py").write_text(controller_code, encoding="utf-8")

        # Generate and write __init__.py
        init_code = _generate_init_code(sanitized_class_name)
        (doctype_folder / "__init__.py").write_text(init_code, encoding="utf-8")

        # Generate and write test file
        test_code = _generate_test_code(sanitized_class_name, sanitized_folder_name)
        (doctype_folder / f"test_{sanitized_folder_name}.py").write_text(
            test_code, encoding="utf-8"
        )

        # Delete old folder if this was a rename
        if is_rename and old_folder_path and old_folder_path.exists():
            import shutil

            shutil.rmtree(old_folder_path)

        action = "renamed" if is_rename else "created"
        return MessageResponse(
            message=f"DocType '{sanitized_class_name}' {action} successfully",
            file_path=str(doctype_folder),
        )

    @delete("/doctype/{name:str}", status_code=200)
    async def delete_doctype(self, name: str) -> MessageResponse:
        """Delete a DocType directory and all its files.

        Args:
            name: DocType class name to delete
        """
        import shutil

        project_root = get_project_root()

        # Find the DocType file
        doctypes = scan_doctypes(project_root)

        for doctype in doctypes:
            if doctype.name == name:
                file_path = Path(doctype.file_path)
                doctype_dir = file_path.parent

                # Delete the entire DocType directory
                if doctype_dir.exists() and doctype_dir.is_dir():
                    shutil.rmtree(doctype_dir)
                    return MessageResponse(
                        message=f"DocType '{name}' deleted successfully",
                        file_path=str(doctype_dir),
                    )
                elif file_path.exists():
                    # Fallback: delete just the file if no directory
                    file_path.unlink()
                    return MessageResponse(
                        message=f"DocType '{name}' deleted successfully",
                        file_path=str(file_path),
                    )

        raise NotFoundException(f"DocType '{name}' not found")


# =============================================================================
# Code Generation Helpers
# =============================================================================


def _sanitize_doctype_name(name: str) -> str:
    """Sanitize DocType name to be valid Python identifier.

    - Replace spaces with underscores
    - Remove all special characters except underscores
    - Convert to PascalCase

    Args:
        name: Raw DocType name (e.g., "Sales Invoice", "sales-order")

    Returns:
        Sanitized PascalCase name (e.g., "SalesInvoice", "SalesOrder")
    """
    import re

    # Replace hyphens and spaces with underscores first
    s = re.sub(r"[-\s]+", "_", name)

    # Remove any non-alphanumeric characters except underscores
    s = re.sub(r"[^a-zA-Z0-9_]", "", s)

    # Split by underscores and capitalize first letter of each word
    # Use word[0].upper() + word[1:] instead of capitalize() to preserve case
    parts = s.split("_")
    pascal = "".join((word[0].upper() + word[1:]) if word else "" for word in parts)

    return pascal or "DocType"


def _to_snake_case(name: str) -> str:
    """Convert PascalCase to snake_case."""
    import re

    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def _generate_doctype_code(schema: CreateDocTypeRequest) -> str:
    """Generate Python code for a DocType.

    Now uses the Jinja2 template system for consistent code generation.
    """
    from framework_m_studio.codegen.generator import generate_doctype_source

    # Convert CreateDocTypeRequest to dict format expected by generator
    schema_dict = {
        "name": schema.name,
        "docstring": schema.docstring,
        "fields": [
            {
                "name": f.name,
                "type": f.type,
                "required": f.required,
                "label": f.label,
                "default": f.default,
                "description": f.description,
                "validators": (
                    {
                        "min_length": f.validators.min_length,
                        "max_length": f.validators.max_length,
                        "pattern": f.validators.pattern,
                        "min_value": f.validators.min_value,
                        "max_value": f.validators.max_value,
                    }
                    if f.validators
                    else {}
                ),
            }
            for f in schema.fields
        ],
    }

    return str(generate_doctype_source(schema_dict))


def _generate_controller_code(name: str) -> str:
    """Generate Python code for a Controller.

    Args:
        name: The DocType class name (e.g., "Invoice")

    Returns:
        Generated controller Python code
    """
    lines = [
        f'"""Controller for {name} DocType."""',
        "",
        "from __future__ import annotations",
        "",
        "from framework_m.core.domain.base_controller import BaseController",
        f"from .doctype import {name}",
        "",
        "",
        f"class {name}Controller(BaseController[{name}]):",
        f'    """Controller for {name} DocType.',
        "",
        "    Implement custom business logic here.",
        "",
        "    Lifecycle Hooks:",
        "        - validate: Called before save to validate data",
        "        - before_save: Called before persisting to database",
        "        - after_save: Called after successful save",
        "        - before_delete: Called before deleting a document",
        '    """',
        "",
        f"    doctype = {name}",
        "",
        f"    async def validate(self, doc: {name}) -> None:",
        '        """Validate document before saving.',
        "",
        "        Raise ValueError for validation errors.",
        "",
        "        Example:",
        "            if not doc.name:",
        '                raise ValueError("Name is required")',
        '        """',
        "        pass",
        "",
        f"    async def before_save(self, doc: {name}) -> None:",
        '        """Called before saving a document.',
        "",
        "        Use for setting computed fields or timestamps.",
        '        """',
        "        pass",
        "",
        f"    async def after_save(self, doc: {name}) -> None:",
        '        """Called after saving a document.',
        "",
        "        Use for side effects like sending notifications.",
        '        """',
        "        pass",
        "",
        f"    async def before_delete(self, doc: {name}) -> None:",
        '        """Called before deleting a document.',
        "",
        "        Use for cleanup or validation before delete.",
        '        """',
        "        pass",
        "",
    ]

    return "\n".join(lines)


def _generate_init_code(name: str) -> str:
    """Generate __init__.py code for a DocType package.

    Args:
        name: The DocType class name (e.g., "Invoice")

    Returns:
        Generated __init__.py Python code
    """
    return f'''"""{{ class_name }} DocType package.

Auto-generated by Framework M Studio.
"""

from .controller import {name}Controller
from .doctype import {name}

__all__ = ["{name}", "{name}Controller"]
'''.replace("{{ class_name }}", name)


def _generate_test_code(name: str, snake_name: str) -> str:
    """Generate test file code for a DocType.

    Args:
        name: The DocType class name (e.g., "Invoice")
        snake_name: Snake case name (e.g., "invoice")

    Returns:
        Generated test Python code
    """
    return f'''"""Tests for {name} DocType.

Auto-generated by Framework M Studio.
"""

from __future__ import annotations

import pytest

from .doctype import {name}


class Test{name}:
    """Tests for {name}."""

    def test_create_{snake_name}(self) -> None:
        """{name} should be creatable."""
        doc = {name}(name="test-001")
        assert doc.name == "test-001"

    def test_{snake_name}_doctype_name(self) -> None:
        """{name} should have correct class name."""
        assert {name}.__name__ == "{name}"
'''


__all__ = [
    "CreateDocTypeRequest",
    "DocTypeController",
    "DocTypeListResponse",
    "DocTypeResponse",
]
