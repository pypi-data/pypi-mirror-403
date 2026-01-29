"""DocType Parser - LibCST-based Python file parser.

This module provides the `parse_doctype` function that extracts structured
information from DocType Python files, including:
- Class definition and bases
- Field definitions with types and defaults
- Config class metadata (tablename, verbose_name, etc.)
- Docstrings and comments

Strategy: "LibCST for parsing, Jinja for generation"
- LibCST preserves comments and formatting when modifying existing files
- Jinja templates provide clean scaffolding for new files

Usage:
    from framework_m_studio.codegen.parser import parse_doctype

    schema = parse_doctype("/path/to/todo.py")
    # Returns structured dict with class info, fields, config
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import libcst as cst

# =============================================================================
# Data Models
# =============================================================================


@dataclass
class FieldSchema:
    """Parsed field information from a DocType class."""

    name: str
    type: str
    default: str | None = None
    required: bool = True
    description: str | None = None
    label: str | None = None
    validators: dict[str, Any] = field(default_factory=dict)


@dataclass
class ConfigSchema:
    """Parsed Config class metadata."""

    tablename: str | None = None
    verbose_name: str | None = None
    verbose_name_plural: str | None = None
    is_submittable: bool = False
    is_tree: bool = False
    track_changes: bool = True
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class DocTypeSchema:
    """Complete parsed DocType schema."""

    name: str
    module: str
    file_path: str
    bases: list[str] = field(default_factory=list)
    fields: list[FieldSchema] = field(default_factory=list)
    config: ConfigSchema = field(default_factory=ConfigSchema)
    docstring: str | None = None
    imports: list[str] = field(default_factory=list)
    custom_methods: list[str] = field(default_factory=list)


# =============================================================================
# LibCST Visitor for Complete DocType Parsing
# =============================================================================


class DocTypeParserVisitor(cst.CSTVisitor):
    """LibCST visitor to extract complete DocType information."""

    def __init__(self) -> None:
        self.doctypes: list[DocTypeSchema] = []
        self.imports: list[str] = []
        self._current_class: str | None = None
        self._current_bases: list[str] = []
        self._current_fields: list[FieldSchema] = []
        self._current_docstring: str | None = None
        self._current_config: ConfigSchema = ConfigSchema()
        self._current_methods: list[str] = []
        self._in_config_class: bool = False

    def visit_Import(self, node: cst.Import) -> bool:
        """Collect import statements."""
        self.imports.append(_node_to_source(node))
        return False

    def visit_ImportFrom(self, node: cst.ImportFrom) -> bool:
        """Collect from imports."""
        self.imports.append(_node_to_source(node))
        return False

    def visit_ClassDef(self, node: cst.ClassDef) -> bool:
        """Visit class definition."""
        class_name = node.name.value

        # Check if this is the Config or Meta inner class
        if self._current_class and class_name in ("Config", "Meta"):
            self._in_config_class = True
            return True

        # Get base classes
        bases: list[str] = []
        for arg in node.bases:
            if isinstance(arg.value, cst.Name):
                bases.append(arg.value.value)
            elif isinstance(arg.value, cst.Attribute):
                bases.append(_get_attribute_name(arg.value))

        # Check if this is a DocType
        is_doctype = any(
            base in ("BaseDocType", "DocType") or "DocType" in base for base in bases
        )

        if is_doctype:
            self._current_class = class_name
            self._current_bases = bases
            self._current_fields = []
            self._current_methods = []
            self._current_config = ConfigSchema()

            # Extract docstring
            self._current_docstring = _extract_docstring(node)

        return True

    def leave_ClassDef(self, node: cst.ClassDef) -> None:
        """Leave class definition."""
        class_name = node.name.value

        if class_name in ("Config", "Meta"):
            self._in_config_class = False
            return

        if self._current_class == class_name:
            doctype = DocTypeSchema(
                name=self._current_class,
                module="",
                file_path="",
                bases=self._current_bases,
                fields=self._current_fields,
                config=self._current_config,
                docstring=self._current_docstring,
                imports=self.imports.copy(),
                custom_methods=self._current_methods,
            )
            self.doctypes.append(doctype)

            self._current_class = None
            self._current_bases = []
            self._current_fields = []
            self._current_docstring = None
            self._current_config = ConfigSchema()
            self._current_methods = []

    def visit_FunctionDef(self, node: cst.FunctionDef) -> bool:
        """Visit function/method definition."""
        if self._current_class and not self._in_config_class:
            method_name = node.name.value
            if not method_name.startswith("_"):
                self._current_methods.append(method_name)
        return False

    def visit_AnnAssign(self, node: cst.AnnAssign) -> bool:
        """Visit annotated assignment (field definition)."""
        if self._current_class is None:
            return False

        if not isinstance(node.target, cst.Name):
            return False

        field_name = node.target.value

        # Config class attributes
        if self._in_config_class:
            self._parse_config_attribute(field_name, node)
            return False

        # Skip private/dunder fields
        if field_name.startswith("_"):
            return False

        # Parse field
        field_type_raw = node.annotation.annotation
        field_type = _annotation_to_string(field_type_raw)
        default_value: str | None = None
        required = node.value is None
        validators: dict[str, Any] = {}
        description: str | None = None
        label: str | None = None

        # Check for Annotated[type, Field(...)] pattern
        if isinstance(field_type_raw, cst.Subscript):
            subscript_value = _node_to_source(field_type_raw.value)
            if subscript_value == "Annotated":
                # libcst slice is a tuple of SubscriptElement objects
                slice_elements = field_type_raw.slice
                if isinstance(slice_elements, tuple) and len(slice_elements) >= 1:
                    # First element is the actual type (wrapped in Index)
                    first_elem = slice_elements[0]
                    if isinstance(first_elem.slice, cst.Index):
                        field_type = _node_to_source(first_elem.slice.value)
                    else:
                        field_type = _node_to_source(first_elem.slice)

                    # Look for Field() in remaining elements
                    for elem in slice_elements[1:]:
                        if isinstance(elem.slice, cst.Index):
                            value = elem.slice.value
                        else:
                            value = elem.slice

                        if isinstance(value, cst.Call):
                            func_name = _node_to_source(value.func)
                            if func_name == "Field":
                                default_value, validators, description, label = (
                                    _parse_field_call(value)
                                )
                                if default_value == "...":
                                    required = True
                                    default_value = None
                                elif default_value is not None:
                                    required = False
                                break

        # Check for Optional type
        if "Optional" in field_type or "None" in field_type:
            required = False

        # Handle Field() call in value (old style: field: type = Field(...))
        if node.value and isinstance(node.value, cst.Call):
            func_name = _node_to_source(node.value.func)
            if func_name == "Field":
                # Extract default from first positional argument
                default_value, validators, description, label = _parse_field_call(
                    node.value
                )
                # If default is "..." it means required with no default
                if default_value == "...":
                    required = True
                    default_value = None
                elif default_value is not None:
                    required = False
            else:
                # Some other call, keep as is
                default_value = _node_to_source(node.value)
        elif node.value:
            default_value = _node_to_source(node.value)

        field_schema = FieldSchema(
            name=field_name,
            type=field_type,
            default=default_value,
            required=required,
            description=description,
            label=label,
            validators=validators,
        )
        self._current_fields.append(field_schema)

        return False

    def visit_Assign(self, node: cst.Assign) -> bool:
        """Visit simple assignment (for Config class)."""
        if not self._in_config_class:
            return False

        for target in node.targets:
            if isinstance(target.target, cst.Name):
                field_name = target.target.value
                value = _node_to_source(node.value)
                self._set_config_value(field_name, value)

        return False

    def _parse_config_attribute(self, name: str, node: cst.AnnAssign) -> None:
        """Parse Config class attribute."""
        value = _node_to_source(node.value) if node.value else None
        self._set_config_value(name, value)

    def _set_config_value(self, name: str, value: str | None) -> None:
        """Set a config value."""
        if value is None:
            return

        # Remove quotes from strings
        clean_value = value.strip("\"'")

        if name == "tablename":
            self._current_config.tablename = clean_value
        elif name == "verbose_name":
            self._current_config.verbose_name = clean_value
        elif name == "verbose_name_plural":
            self._current_config.verbose_name_plural = clean_value
        elif name == "is_submittable":
            self._current_config.is_submittable = value.lower() == "true"
        elif name == "is_tree":
            self._current_config.is_tree = value.lower() == "true"
        elif name == "track_changes":
            self._current_config.track_changes = value.lower() != "false"
        else:
            self._current_config.extra[name] = value


# =============================================================================
# Helper Functions
# =============================================================================


def _get_attribute_name(node: cst.Attribute) -> str:
    """Get full attribute name from Attribute node."""
    parts: list[str] = []
    current: cst.BaseExpression = node

    while isinstance(current, cst.Attribute):
        parts.append(current.attr.value)
        current = current.value

    if isinstance(current, cst.Name):
        parts.append(current.value)

    return ".".join(reversed(parts))


def _annotation_to_string(node: cst.BaseExpression) -> str:
    """Convert annotation node to string."""
    return _node_to_source(node)


def _node_to_source(node: cst.CSTNode) -> str:
    """Convert CST node to source code string."""
    return cst.Module(body=[]).code_for_node(node)


def _extract_docstring(node: cst.ClassDef) -> str | None:
    """Extract docstring from class definition."""
    if not node.body or not node.body.body:
        return None

    first_stmt = node.body.body[0]
    if not isinstance(first_stmt, cst.SimpleStatementLine):
        return None

    if not first_stmt.body or not isinstance(first_stmt.body[0], cst.Expr):
        return None

    expr = first_stmt.body[0].value
    if isinstance(expr, cst.SimpleString):
        value = expr.value
        if value.startswith('"""') or value.startswith("'''"):
            return value[3:-3].strip()
        elif value.startswith('"') or value.startswith("'"):
            return value[1:-1].strip()
    elif isinstance(expr, cst.ConcatenatedString):
        # Handle multi-line docstrings
        parts = []
        for part in (expr.left, expr.right):
            if isinstance(part, cst.SimpleString):
                parts.append(part.value.strip("\"'"))
        return "".join(parts)

    return None


def _parse_field_call(
    node: cst.Call,
) -> tuple[str | None, dict[str, Any], str | None, str | None]:
    """Parse Field(...) call and extract default, validators, description, and label.

    Returns:
        Tuple of (default_value, validators_dict, description, label)
    """
    default_value: str | None = None
    validators: dict[str, Any] = {}
    description: str | None = None
    label: str | None = None

    for i, arg in enumerate(node.args):
        # First positional argument is the default value
        if arg.keyword is None and i == 0:
            default_value = _node_to_source(arg.value)
            continue

        if isinstance(arg.keyword, cst.Name):
            key = arg.keyword.value
            value_str = _node_to_source(arg.value)

            # Map Pydantic Field kwargs to our validator schema
            if key == "ge":
                # Remove trailing decimal if present (100000.0 -> 100000)
                val = float(value_str)
                validators["min_value"] = int(val) if val == int(val) else val
            elif key == "le":
                val = float(value_str)
                validators["max_value"] = int(val) if val == int(val) else val
            elif key == "gt":
                val = float(value_str)
                validators["min_value"] = int(val) + 1 if val == int(val) else val
            elif key == "lt":
                val = float(value_str)
                validators["max_value"] = int(val) - 1 if val == int(val) else val
            elif key == "min_length":
                validators["min_length"] = int(value_str)
            elif key == "max_length":
                validators["max_length"] = int(value_str)
            elif key in ("pattern", "regex"):
                # Remove r prefix and quotes
                pattern = value_str
                if pattern.startswith("r"):
                    pattern = pattern[1:]
                pattern = pattern.strip("\"'")
                validators["pattern"] = pattern
            elif key == "description":
                description = value_str.strip("\"'")
            elif key == "label":
                label = value_str.strip("\"'")
            elif key == "default":
                default_value = value_str

    return default_value, validators, description, label


def _path_to_module(file_path: Path) -> str:
    """Convert file path to Python module path."""
    parts = file_path.parts
    try:
        src_idx = parts.index("src")
        module_parts = parts[src_idx + 1 : -1]
        module_name = file_path.stem
        return ".".join([*module_parts, module_name])
    except ValueError:
        return file_path.stem


# =============================================================================
# Public API
# =============================================================================


def parse_doctype(file_path: str | Path) -> dict[str, Any]:
    """Parse a DocType Python file and return structured schema.

    Args:
        file_path: Path to the Python file containing DocType

    Returns:
        Dictionary with keys:
        - name: DocType class name
        - module: Python module path
        - file_path: Absolute file path
        - bases: List of base class names
        - fields: List of field definitions
        - config: Config class metadata
        - docstring: Class docstring
        - imports: List of import statements
        - custom_methods: List of custom method names

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If no DocType found in file

    Example:
        >>> schema = parse_doctype("src/myapp/doctypes/todo.py")
        >>> schema["name"]
        'Todo'
        >>> schema["fields"][0]["name"]
        'title'
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    source = path.read_text(encoding="utf-8")

    try:
        tree = cst.parse_module(source)
    except cst.ParserSyntaxError as e:
        raise ValueError(f"Failed to parse Python file: {e}") from e

    visitor = DocTypeParserVisitor()
    tree.visit(visitor)

    if not visitor.doctypes:
        raise ValueError(f"No DocType class found in {file_path}")

    # Return the first DocType found
    doctype = visitor.doctypes[0]
    doctype.file_path = str(path.absolute())
    doctype.module = _path_to_module(path)

    return doctype_to_dict(doctype)


def doctype_to_dict(doctype: DocTypeSchema) -> dict[str, Any]:
    """Convert DocTypeSchema to dictionary."""
    return {
        "name": doctype.name,
        "module": doctype.module,
        "file_path": doctype.file_path,
        "bases": doctype.bases,
        "fields": [
            {
                "name": f.name,
                "type": f.type,
                "default": f.default,
                "required": f.required,
                "label": f.label,
                "description": f.description,
                "validators": f.validators,
            }
            for f in doctype.fields
        ],
        "config": {
            "tablename": doctype.config.tablename,
            "verbose_name": doctype.config.verbose_name,
            "verbose_name_plural": doctype.config.verbose_name_plural,
            "is_submittable": doctype.config.is_submittable,
            "is_tree": doctype.config.is_tree,
            "track_changes": doctype.config.track_changes,
            **doctype.config.extra,
        },
        "docstring": doctype.docstring,
        "imports": doctype.imports,
        "custom_methods": doctype.custom_methods,
    }


__all__ = [
    "ConfigSchema",
    "DocTypeSchema",
    "FieldSchema",
    "doctype_to_dict",
    "parse_doctype",
]
