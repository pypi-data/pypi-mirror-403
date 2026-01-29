"""Tests for DocType Transformer module."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest

from framework_m_studio.codegen.transformer import (
    add_field,
    remove_field,
    rename_field,
    update_doctype,
)


class TestUpdateDocType:
    """Tests for update_doctype function."""

    def test_add_new_field(self, tmp_path: Path) -> None:
        """update_doctype should add new fields."""
        code = dedent("""
            from framework_m.core.base import BaseDocType

            class Todo(BaseDocType):
                title: str
        """)

        file_path = tmp_path / "todo.py"
        file_path.write_text(code)

        result = update_doctype(
            file_path,
            {
                "name": "Todo",
                "fields": [
                    {"name": "title", "type": "str", "required": True},
                    {"name": "priority", "type": "int", "default": "1"},
                ],
            },
        )

        assert "title: str" in result
        assert "priority: int = 1" in result

    def test_update_field_type(self, tmp_path: Path) -> None:
        """update_doctype should update field types."""
        code = dedent("""
            from framework_m.core.base import BaseDocType

            class Item(BaseDocType):
                count: str
        """)

        file_path = tmp_path / "item.py"
        file_path.write_text(code)

        result = update_doctype(
            file_path,
            {
                "name": "Item",
                "fields": [
                    {"name": "count", "type": "int", "required": True},
                ],
            },
        )

        assert "count: int" in result
        assert "count: str" not in result

    def test_preserve_custom_methods(self, tmp_path: Path) -> None:
        """update_doctype should preserve custom methods."""
        code = dedent("""
            from framework_m.core.base import BaseDocType

            class Todo(BaseDocType):
                title: str
                
                def custom_method(self) -> str:
                    return self.title.upper()
        """)

        file_path = tmp_path / "todo.py"
        file_path.write_text(code)

        result = update_doctype(
            file_path,
            {
                "name": "Todo",
                "fields": [
                    {"name": "title", "type": "str", "required": True},
                    {"name": "done", "type": "bool", "default": "False"},
                ],
            },
        )

        assert "def custom_method(self)" in result
        assert "return self.title.upper()" in result

    def test_file_not_found(self) -> None:
        """update_doctype should raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            update_doctype("/nonexistent.py", {"name": "X", "fields": []})


class TestRemoveField:
    """Tests for remove_field function."""

    def test_remove_field(self, tmp_path: Path) -> None:
        """remove_field should remove a field."""
        code = dedent("""
            from framework_m.core.base import BaseDocType

            class Todo(BaseDocType):
                title: str
                obsolete: str = "old"
        """)

        file_path = tmp_path / "todo.py"
        file_path.write_text(code)

        result = remove_field(file_path, "Todo", "obsolete")

        assert "title: str" in result
        assert "obsolete" not in result


class TestRenameField:
    """Tests for rename_field function."""

    def test_rename_field(self, tmp_path: Path) -> None:
        """rename_field should rename a field."""
        code = dedent("""
            from framework_m.core.base import BaseDocType

            class Todo(BaseDocType):
                old_name: str
        """)

        file_path = tmp_path / "todo.py"
        file_path.write_text(code)

        result = rename_field(file_path, "Todo", "old_name", "new_name")

        assert "new_name: str" in result
        assert "old_name" not in result


class TestAddField:
    """Tests for add_field function."""

    def test_add_single_field(self, tmp_path: Path) -> None:
        """add_field should add a single field."""
        code = dedent("""
            from framework_m.core.base import BaseDocType

            class Todo(BaseDocType):
                title: str
        """)

        file_path = tmp_path / "todo.py"
        file_path.write_text(code)

        result = add_field(
            file_path,
            "Todo",
            "priority",
            "int",
            default="1",
            required=False,
        )

        # Non-required fields with defaults get | None type
        assert "priority: int" in result
        assert "= 1" in result
