"""Tests for DocType Code Generator module."""

from __future__ import annotations

from textwrap import dedent

from framework_m_studio.codegen.generator import (
    generate_doctype_source,
    generate_test_source,
    update_doctype_source,
)


class TestGenerateDocTypeSource:
    """Tests for generate_doctype_source function."""

    def test_generate_simple_doctype(self) -> None:
        """generate_doctype_source should create valid Python code."""
        code = generate_doctype_source(
            {
                "name": "Todo",
                "fields": [
                    {"name": "title", "type": "str", "required": True},
                ],
            }
        )

        assert "class Todo(BaseDocType):" in code
        assert "title: str" in code
        assert "from framework_m.core.base import BaseDocType" in code

    def test_generate_with_docstring(self) -> None:
        """generate_doctype_source should include docstring."""
        code = generate_doctype_source(
            {
                "name": "Invoice",
                "docstring": "An invoice document.",
                "fields": [{"name": "number", "type": "str", "required": True}],
            }
        )

        assert '"""An invoice document."""' in code

    def test_generate_with_defaults(self) -> None:
        """generate_doctype_source should handle default values."""
        code = generate_doctype_source(
            {
                "name": "Task",
                "fields": [
                    {"name": "title", "type": "str", "required": True},
                    {"name": "done", "type": "bool", "default": "False"},
                ],
            }
        )

        assert "title: str" in code
        assert "done: bool = False" in code

    def test_generate_optional_fields(self) -> None:
        """generate_doctype_source should handle optional fields."""
        code = generate_doctype_source(
            {
                "name": "User",
                "fields": [
                    {"name": "name", "type": "str", "required": True},
                    {"name": "bio", "type": "str", "required": False},
                ],
            }
        )

        assert "name: str" in code
        assert "bio: str | None = None" in code

    def test_generate_with_config(self) -> None:
        """generate_doctype_source should include Config class."""
        code = generate_doctype_source(
            {
                "name": "Order",
                "fields": [{"name": "number", "type": "str", "required": True}],
                "config": {
                    "tablename": "orders",
                    "verbose_name": "Sales Order",
                    "is_submittable": True,
                },
            }
        )

        assert "class Config:" in code
        assert 'tablename = "orders"' in code
        assert 'verbose_name = "Sales Order"' in code
        assert "is_submittable = True" in code


class TestGenerateTestSource:
    """Tests for generate_test_source function."""

    def test_generate_test_file(self) -> None:
        """generate_test_source should create valid test code."""
        code = generate_test_source(
            {
                "name": "Todo",
                "module": "myapp.doctypes.todo",
                "fields": [
                    {"name": "title", "type": "str", "required": True},
                ],
            }
        )

        assert "class TestTodo:" in code
        assert "def test_create_todo" in code
        assert "from myapp.doctypes.todo import Todo" in code


class TestUpdateDocTypeSource:
    """Tests for update_doctype_source function."""

    def test_add_new_field(self) -> None:
        """update_doctype_source should add new fields."""
        original = dedent("""
            from framework_m.core.base import BaseDocType

            class Todo(BaseDocType):
                title: str
        """)

        updated = update_doctype_source(
            original,
            {
                "name": "Todo",
                "fields": [
                    {"name": "title", "type": "str", "required": True},
                    {"name": "priority", "type": "int", "default": "1"},
                ],
            },
        )

        assert "title: str" in updated
        assert "priority: int = 1" in updated

    def test_update_field_type(self) -> None:
        """update_doctype_source should update field types."""
        original = dedent("""
            from framework_m.core.base import BaseDocType

            class Todo(BaseDocType):
                count: str
        """)

        updated = update_doctype_source(
            original,
            {
                "name": "Todo",
                "fields": [
                    {"name": "count", "type": "int", "required": True},
                ],
            },
        )

        assert "count: int" in updated

    def test_preserve_custom_methods(self) -> None:
        """update_doctype_source should preserve custom methods."""
        original = dedent("""
            from framework_m.core.base import BaseDocType

            class Todo(BaseDocType):
                title: str
                
                def custom_method(self) -> str:
                    return self.title.upper()
        """)

        updated = update_doctype_source(
            original,
            {
                "name": "Todo",
                "fields": [
                    {"name": "title", "type": "str", "required": True},
                    {"name": "done", "type": "bool", "default": "False"},
                ],
            },
        )

        assert "def custom_method(self)" in updated
        assert "return self.title.upper()" in updated
