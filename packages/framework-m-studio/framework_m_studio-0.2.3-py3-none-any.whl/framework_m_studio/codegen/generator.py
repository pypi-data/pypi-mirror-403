"""DocType Code Generator.

Strategy: "Jinja for Creation, LibCST for Mutation"

- **Creation (Scaffolding)**: Use Jinja2 templates to generate clean Python code from scratch.
  Shared with CLI `m new:doctype`.

- **Mutation (Transformer)**: Use LibCST to parse and modify existing files, preserving
  comments and custom methods.

Usage:
    from framework_m_studio.codegen.generator import generate_doctype_source

    code = generate_doctype_source({
        "name": "Todo",
        "fields": [
            {"name": "title", "type": "str", "required": True},
            {"name": "completed", "type": "bool", "default": "False"},
        ],
    })
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

# Template directory
TEMPLATE_DIR = Path(__file__).parent / "templates"


def _get_jinja_env() -> Environment:
    """Get configured Jinja2 environment."""
    return Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=select_autoescape(enabled_extensions=()),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )


def _to_snake_case(name: str) -> str:
    """Convert PascalCase to snake_case."""
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def _get_test_value(field_type: str) -> str:
    """Get a test value for a field type."""
    type_values = {
        "str": '"test"',
        "int": "1",
        "float": "1.0",
        "bool": "True",
        "date": "date.today()",
        "datetime": "datetime.now()",
        "UUID": "uuid4()",
        "uuid": "uuid4()",
    }

    # Check for base type (handle Optional, Union, etc.)
    base_type = field_type.split("[")[0].split("|")[0].strip()
    return type_values.get(base_type, '"test"')


def generate_doctype_source(schema: dict[str, Any]) -> str:
    """Generate Python source code for a DocType.

    Args:
        schema: Dictionary with DocType schema:
            - name: str - Class name (PascalCase)
            - fields: list[dict] - Field definitions
            - docstring: str | None - Class docstring
            - config: dict | None - Config class metadata
            - imports: list[str] | None - Additional imports

    Returns:
        Generated Python source code as string.

    Example:
        >>> code = generate_doctype_source({
        ...     "name": "Todo",
        ...     "fields": [{"name": "title", "type": "str", "required": True}],
        ... })
        >>> print(code)
    """
    env = _get_jinja_env()
    template = env.get_template("doctype.py.jinja2")

    # Prepare context
    context = {
        "name": schema["name"],
        "docstring": schema.get("docstring"),
        "fields": schema.get("fields", []),
        "config": schema.get("config"),
        "imports": schema.get("imports", []),
    }

    return template.render(**context)


def generate_test_source(schema: dict[str, Any]) -> str:
    """Generate test file source code for a DocType.

    Args:
        schema: Dictionary with DocType schema (same as generate_doctype_source)
            Plus:
            - module: str - Python module path for imports

    Returns:
        Generated test file source code.
    """
    env = _get_jinja_env()
    template = env.get_template("test_doctype.py.jinja2")

    # Prepare fields with test values
    fields = schema.get("fields", [])
    for field in fields:
        if "test_value" not in field:
            field["test_value"] = _get_test_value(field.get("type", "str"))

    # Check if has required fields
    has_required = any(f.get("required", False) for f in fields)

    context = {
        "name": schema["name"],
        "snake_name": _to_snake_case(schema["name"]),
        "module": schema.get("module", "myapp.doctypes"),
        "fields": fields,
        "has_required_fields": has_required,
    }

    return template.render(**context)


def update_doctype_source(
    source: str,
    schema: dict[str, Any],
) -> str:
    """Update existing DocType source by adding/modifying fields.

    Uses LibCST to preserve comments and custom methods.

    Args:
        source: Existing Python source code
        schema: Updated DocType schema with fields to add/modify

    Returns:
        Updated Python source code.

    Note:
        This function preserves:
        - Comments and docstrings
        - Custom methods
        - Import statements
        - Existing fields not in schema (unless explicitly removed)
    """
    import libcst as cst

    class DocTypeUpdater(cst.CSTTransformer):
        """LibCST transformer to update DocType fields."""

        def __init__(self, schema: dict[str, Any]) -> None:
            self.schema = schema
            self.target_class = schema["name"]
            self.fields_to_add = {f["name"]: f for f in schema.get("fields", [])}
            self.in_target_class = False
            self.existing_fields: set[str] = set()

        def visit_ClassDef(self, node: cst.ClassDef) -> bool:
            """Track when we're inside target class."""
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

            # Find fields that need to be added
            fields_to_add = [
                f
                for name, f in self.fields_to_add.items()
                if name not in self.existing_fields
            ]

            if not fields_to_add:
                return updated_node

            # Generate new field statements
            new_statements = []
            for field in fields_to_add:
                stmt = self._create_field_statement(field)
                new_statements.append(stmt)

            # Insert new statements at the end of class body
            new_body = list(updated_node.body.body) + new_statements

            return updated_node.with_changes(
                body=updated_node.body.with_changes(body=new_body)
            )

        def leave_AnnAssign(
            self,
            original_node: cst.AnnAssign,
            updated_node: cst.AnnAssign,
        ) -> cst.AnnAssign:
            """Update existing field definitions."""
            if not self.in_target_class:
                return updated_node

            if not isinstance(original_node.target, cst.Name):
                return updated_node

            field_name = original_node.target.value
            self.existing_fields.add(field_name)

            # Check if field needs update
            if field_name not in self.fields_to_add:
                return updated_node

            new_field = self.fields_to_add[field_name]

            # Update type annotation
            new_annotation = cst.Annotation(
                annotation=cst.parse_expression(new_field["type"])
            )

            # Update default value
            new_value = None
            if new_field.get("default"):
                new_value = cst.parse_expression(new_field["default"])
            elif not new_field.get("required", True):
                new_value = cst.Name("None")

            return updated_node.with_changes(
                annotation=new_annotation,
                value=new_value,
            )

        def _create_field_statement(
            self,
            field: dict[str, Any],
        ) -> cst.SimpleStatementLine:
            """Create a new field statement."""
            type_str = field["type"]
            if not field.get("required", True) and "None" not in type_str:
                type_str = f"{type_str} | None"

            annotation = cst.Annotation(annotation=cst.parse_expression(type_str))

            value = None
            if field.get("default"):
                value = cst.parse_expression(field["default"])
            elif not field.get("required", True):
                value = cst.Name("None")

            return cst.SimpleStatementLine(
                body=[
                    cst.AnnAssign(
                        target=cst.Name(field["name"]),
                        annotation=annotation,
                        value=value,
                    )
                ]
            )

    # Parse and transform
    tree = cst.parse_module(source)
    transformer = DocTypeUpdater(schema)
    updated_tree = tree.visit(transformer)

    return updated_tree.code


__all__ = [
    "generate_doctype_source",
    "generate_test_source",
    "update_doctype_source",
]
