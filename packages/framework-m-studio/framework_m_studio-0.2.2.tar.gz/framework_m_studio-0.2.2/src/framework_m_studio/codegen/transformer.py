"""DocType Transformer - LibCST-based file transformer.

This module provides file-level operations for updating DocType Python files:
- Parse existing files with LibCST
- Update/add/remove fields while preserving formatting
- Handle edge cases: field renames, type changes, deletions
- Preserve comments and custom methods

Usage:
    from framework_m_studio.codegen.transformer import update_doctype

    update_doctype(
        file_path="src/doctypes/todo.py",
        schema={"name": "Todo", "fields": [...]},
    )
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import libcst as cst

# =============================================================================
# LibCST Transformer for DocType Updates
# =============================================================================


class DocTypeTransformer(cst.CSTTransformer):
    """LibCST transformer to update DocType class fields.

    Handles:
    - Adding new fields
    - Updating existing field types/defaults
    - Removing deleted fields
    - Renaming fields
    - Preserving comments and custom methods
    """

    def __init__(
        self,
        target_class: str,
        new_fields: dict[str, dict[str, Any]],
        fields_to_remove: set[str] | None = None,
        field_renames: dict[str, str] | None = None,
    ) -> None:
        """Initialize transformer.

        Args:
            target_class: Name of the DocType class to update
            new_fields: Dict of field_name -> field_schema
            fields_to_remove: Set of field names to remove
            field_renames: Dict of old_name -> new_name for renames
        """
        self.target_class = target_class
        self.new_fields = new_fields
        self.fields_to_remove = fields_to_remove or set()
        self.field_renames = field_renames or {}

        self.in_target_class = False
        self.existing_fields: set[str] = set()
        self._class_body_updated = False

    def visit_ClassDef(self, node: cst.ClassDef) -> bool:
        """Track when inside target class."""
        if node.name.value == self.target_class:
            self.in_target_class = True
        return True

    def leave_ClassDef(
        self,
        original_node: cst.ClassDef,
        updated_node: cst.ClassDef,
    ) -> cst.ClassDef:
        """Add new fields when leaving target class."""
        if original_node.name.value != self.target_class:
            return updated_node

        self.in_target_class = False

        # Find fields that need to be added (not already existing)
        fields_to_add = [
            (name, schema)
            for name, schema in self.new_fields.items()
            if name not in self.existing_fields
        ]

        if not fields_to_add:
            return updated_node

        # Generate new field statements
        new_statements: list[cst.SimpleStatementLine] = []
        for field_name, field_schema in fields_to_add:
            stmt = self._create_field_statement(field_name, field_schema)
            new_statements.append(stmt)

        # Find insertion point (after last field, before methods)
        body_list = cast(list[cst.BaseStatement], list(updated_node.body.body))
        insert_index = self._find_field_insert_index(body_list)

        # Insert new fields
        for i, stmt in enumerate(new_statements):
            body_list.insert(insert_index + i, stmt)

        return updated_node.with_changes(
            body=updated_node.body.with_changes(body=body_list)
        )

    def leave_SimpleStatementLine(
        self,
        original_node: cst.SimpleStatementLine,
        updated_node: cst.SimpleStatementLine,
    ) -> cst.SimpleStatementLine | cst.RemovalSentinel:
        """Handle field updates and removals."""
        if not self.in_target_class:
            return updated_node

        # Check if this is an annotated assignment (field)
        if not updated_node.body:
            return updated_node

        stmt = updated_node.body[0]
        if not isinstance(stmt, cst.AnnAssign):
            return updated_node

        if not isinstance(stmt.target, cst.Name):
            return updated_node

        field_name = stmt.target.value

        # Skip private fields
        if field_name.startswith("_"):
            return updated_node

        self.existing_fields.add(field_name)

        # Handle removal
        if field_name in self.fields_to_remove:
            return cst.RemovalSentinel.REMOVE

        # Handle rename
        if field_name in self.field_renames:
            new_name = self.field_renames[field_name]
            new_stmt = stmt.with_changes(target=cst.Name(new_name))
            self.existing_fields.add(new_name)

            # Also update if there's new schema for renamed field
            if new_name in self.new_fields:
                new_stmt = self._update_field(new_stmt, self.new_fields[new_name])

            return updated_node.with_changes(body=[new_stmt])

        # Handle update
        if field_name in self.new_fields:
            new_stmt = self._update_field(stmt, self.new_fields[field_name])
            return updated_node.with_changes(body=[new_stmt])

        return updated_node

    def _update_field(
        self,
        stmt: cst.AnnAssign,
        schema: dict[str, Any],
    ) -> cst.AnnAssign:
        """Update field type and default value."""
        # Update type
        new_type = schema.get("type", "str")
        if not schema.get("required", True) and "None" not in new_type:
            new_type = f"{new_type} | None"

        new_annotation = cst.Annotation(annotation=cst.parse_expression(new_type))

        # Update default
        new_value = None
        if schema.get("default"):
            new_value = cst.parse_expression(schema["default"])
        elif not schema.get("required", True):
            new_value = cst.Name("None")

        return stmt.with_changes(
            annotation=new_annotation,
            value=new_value,
        )

    def _create_field_statement(
        self,
        field_name: str,
        schema: dict[str, Any],
    ) -> cst.SimpleStatementLine:
        """Create a new field statement."""
        type_str = schema.get("type", "str")
        if not schema.get("required", True) and "None" not in type_str:
            type_str = f"{type_str} | None"

        annotation = cst.Annotation(annotation=cst.parse_expression(type_str))

        value = None
        if schema.get("default"):
            value = cst.parse_expression(schema["default"])
        elif not schema.get("required", True):
            value = cst.Name("None")

        return cst.SimpleStatementLine(
            body=[
                cst.AnnAssign(
                    target=cst.Name(field_name),
                    annotation=annotation,
                    value=value,
                )
            ]
        )

    def _find_field_insert_index(
        self,
        body: list[cst.BaseStatement],
    ) -> int:
        """Find the best index to insert new fields.

        Insert after last field definition, before methods and Config class.
        """
        last_field_index = 0

        for i, stmt in enumerate(body):
            # Skip docstrings
            if isinstance(stmt, cst.SimpleStatementLine):
                if stmt.body and isinstance(stmt.body[0], cst.Expr):
                    expr = stmt.body[0].value
                    if isinstance(expr, cst.SimpleString | cst.ConcatenatedString):
                        continue

                # This is a field or assignment
                if stmt.body and isinstance(stmt.body[0], cst.AnnAssign):
                    last_field_index = i + 1

            # Stop before methods or nested classes
            elif isinstance(stmt, (cst.FunctionDef, cst.ClassDef)):
                break

        return last_field_index


# =============================================================================
# Public API
# =============================================================================


def update_doctype(
    file_path: str | Path,
    schema: dict[str, Any],
    fields_to_remove: list[str] | None = None,
    field_renames: dict[str, str] | None = None,
) -> str:
    """Update a DocType file with new field definitions.

    Args:
        file_path: Path to the DocType Python file
        schema: Updated DocType schema with fields
        fields_to_remove: List of field names to remove
        field_renames: Dict of old_name -> new_name for renames

    Returns:
        Updated source code (also written to file)

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file can't be parsed

    Example:
        >>> update_doctype(
        ...     "src/doctypes/todo.py",
        ...     {
        ...         "name": "Todo",
        ...         "fields": [
        ...             {"name": "title", "type": "str", "required": True},
        ...             {"name": "priority", "type": "int", "default": "1"},
        ...         ],
        ...     },
        ...     fields_to_remove=["old_field"],
        ...     field_renames={"status": "state"},
        ... )
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    source = path.read_text(encoding="utf-8")

    try:
        tree = cst.parse_module(source)
    except cst.ParserSyntaxError as e:
        raise ValueError(f"Failed to parse Python file: {e}") from e

    # Build field dict from schema
    new_fields: dict[str, dict[str, Any]] = {}
    for field in schema.get("fields", []):
        new_fields[field["name"]] = field

    # Create and apply transformer
    transformer = DocTypeTransformer(
        target_class=schema["name"],
        new_fields=new_fields,
        fields_to_remove=set(fields_to_remove or []),
        field_renames=field_renames or {},
    )

    updated_tree = tree.visit(transformer)
    updated_source = updated_tree.code

    # Write back to file
    path.write_text(updated_source, encoding="utf-8")

    return updated_source


def add_field(
    file_path: str | Path,
    doctype_name: str,
    field_name: str,
    field_type: str,
    default: str | None = None,
    required: bool = True,
) -> str:
    """Add a single field to a DocType file.

    Convenience function for adding one field.

    Args:
        file_path: Path to the DocType file
        doctype_name: Name of the DocType class
        field_name: Name of the new field
        field_type: Python type annotation
        default: Default value expression
        required: Whether field is required

    Returns:
        Updated source code
    """
    return update_doctype(
        file_path,
        {
            "name": doctype_name,
            "fields": [
                {
                    "name": field_name,
                    "type": field_type,
                    "default": default,
                    "required": required,
                }
            ],
        },
    )


def remove_field(
    file_path: str | Path,
    doctype_name: str,
    field_name: str,
) -> str:
    """Remove a field from a DocType file.

    Args:
        file_path: Path to the DocType file
        doctype_name: Name of the DocType class
        field_name: Name of the field to remove

    Returns:
        Updated source code
    """
    return update_doctype(
        file_path,
        {"name": doctype_name, "fields": []},
        fields_to_remove=[field_name],
    )


def rename_field(
    file_path: str | Path,
    doctype_name: str,
    old_name: str,
    new_name: str,
) -> str:
    """Rename a field in a DocType file.

    Args:
        file_path: Path to the DocType file
        doctype_name: Name of the DocType class
        old_name: Current field name
        new_name: New field name

    Returns:
        Updated source code
    """
    return update_doctype(
        file_path,
        {"name": doctype_name, "fields": []},
        field_renames={old_name: new_name},
    )


__all__ = [
    "add_field",
    "remove_field",
    "rename_field",
    "update_doctype",
]
