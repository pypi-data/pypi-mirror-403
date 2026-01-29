"""Tests for DocType Discovery Service."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

from framework_m_studio.discovery import (
    DocTypeInfo,
    FieldInfo,
    doctype_to_dict,
    parse_doctype_file,
    scan_doctypes,
)


class TestFieldInfo:
    """Tests for FieldInfo dataclass."""

    def test_field_info_creation(self) -> None:
        """FieldInfo should be creatable with required fields."""
        field = FieldInfo(name="title", type="str")
        assert field.name == "title"
        assert field.type == "str"
        assert field.required is True
        assert field.default is None

    def test_field_info_with_defaults(self) -> None:
        """FieldInfo should accept optional fields."""
        field = FieldInfo(
            name="status",
            type="str",
            default='"pending"',
            required=False,
            description="Current status",
        )
        assert field.default == '"pending"'
        assert field.required is False
        assert field.description == "Current status"


class TestDocTypeInfo:
    """Tests for DocTypeInfo dataclass."""

    def test_doctype_info_creation(self) -> None:
        """DocTypeInfo should be creatable with required fields."""
        doctype = DocTypeInfo(
            name="Todo",
            module="myapp.doctypes.todo",
            file_path="/path/to/todo.py",
        )
        assert doctype.name == "Todo"
        assert doctype.module == "myapp.doctypes.todo"
        assert doctype.fields == []
        assert doctype.meta == {}


class TestParseDocTypeFile:
    """Tests for parse_doctype_file function."""

    def test_parse_simple_doctype(self, tmp_path: Path) -> None:
        """parse_doctype_file should extract DocType from simple file."""
        code = dedent('''
            """Todo DocType module."""
            
            from framework_m.core.base import BaseDocType
            
            
            class Todo(BaseDocType):
                """A simple todo item."""
                
                title: str
                completed: bool = False
        ''')

        file_path = tmp_path / "todo.py"
        file_path.write_text(code)

        doctypes = parse_doctype_file(file_path)

        assert len(doctypes) == 1
        assert doctypes[0].name == "Todo"
        assert len(doctypes[0].fields) == 2

        # Check title field
        title_field = next(f for f in doctypes[0].fields if f.name == "title")
        assert title_field.type == "str"
        assert title_field.required is True

        # Check completed field
        completed_field = next(f for f in doctypes[0].fields if f.name == "completed")
        assert completed_field.type == "bool"
        assert completed_field.required is False  # Has default

    def test_parse_file_without_doctype(self, tmp_path: Path) -> None:
        """parse_doctype_file should return empty list for non-DocType files."""
        code = dedent('''
            """Some utility module."""
            
            def helper():
                pass
        ''')

        file_path = tmp_path / "utils.py"
        file_path.write_text(code)

        doctypes = parse_doctype_file(file_path)

        assert doctypes == []

    def test_parse_invalid_python(self, tmp_path: Path) -> None:
        """parse_doctype_file should return empty list for invalid Python."""
        file_path = tmp_path / "invalid.py"
        file_path.write_text("this is not { valid python")

        doctypes = parse_doctype_file(file_path)

        assert doctypes == []

    def test_parse_optional_fields(self, tmp_path: Path) -> None:
        """parse_doctype_file should detect Optional fields as not required."""
        code = dedent("""
            from framework_m.core.base import BaseDocType
            from typing import Optional
            
            
            class User(BaseDocType):
                name: str
                email: str | None = None
                phone: Optional[str] = None
        """)

        file_path = tmp_path / "user.py"
        file_path.write_text(code)

        doctypes = parse_doctype_file(file_path)

        assert len(doctypes) == 1

        name_field = next(f for f in doctypes[0].fields if f.name == "name")
        assert name_field.required is True

        email_field = next(f for f in doctypes[0].fields if f.name == "email")
        assert email_field.required is False


class TestScanDocTypes:
    """Tests for scan_doctypes function."""

    def test_scan_finds_doctypes(self, tmp_path: Path) -> None:
        """scan_doctypes should find DocTypes in directory tree."""
        # Create a DocType file
        src_dir = tmp_path / "src" / "doctypes"
        src_dir.mkdir(parents=True)

        (src_dir / "todo.py").write_text(
            dedent("""
            from framework_m.core.base import BaseDocType
            
            class Todo(BaseDocType):
                title: str
        """)
        )

        doctypes = scan_doctypes(tmp_path)

        assert len(doctypes) == 1
        assert doctypes[0].name == "Todo"

    def test_scan_excludes_tests(self, tmp_path: Path) -> None:
        """scan_doctypes should exclude test files by default."""
        # Create a test file with DocType
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()

        (tests_dir / "test_todo.py").write_text(
            dedent("""
            from framework_m.core.base import BaseDocType
            
            class TestDocType(BaseDocType):
                name: str
        """)
        )

        doctypes = scan_doctypes(tmp_path)

        assert len(doctypes) == 0


class TestDocTypeToDict:
    """Tests for doctype_to_dict function."""

    def test_converts_to_dict(self) -> None:
        """doctype_to_dict should convert DocTypeInfo to dictionary."""
        doctype = DocTypeInfo(
            name="Todo",
            module="app.doctypes.todo",
            file_path="/path/to/todo.py",
            docstring="A todo item.",
            fields=[
                FieldInfo(name="title", type="str"),
                FieldInfo(name="done", type="bool", default="False"),
            ],
        )

        result = doctype_to_dict(doctype)

        assert result["name"] == "Todo"
        assert result["module"] == "app.doctypes.todo"
        assert result["docstring"] == "A todo item."
        assert len(result["fields"]) == 2
        assert result["fields"][0]["name"] == "title"
