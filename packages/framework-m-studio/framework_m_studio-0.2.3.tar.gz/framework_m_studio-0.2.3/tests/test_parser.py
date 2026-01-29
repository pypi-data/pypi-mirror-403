"""Tests for DocType Parser module."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest

from framework_m_studio.codegen.parser import (
    ConfigSchema,
    FieldSchema,
    parse_doctype,
)


class TestParseDoctype:
    """Tests for parse_doctype function."""

    def test_parse_simple_doctype(self, tmp_path: Path) -> None:
        """parse_doctype should extract basic DocType info."""
        code = dedent('''
            """Todo module."""
            
            from framework_m.core.base import BaseDocType
            
            
            class Todo(BaseDocType):
                """A simple todo item."""
                
                title: str
                completed: bool = False
        ''')

        file_path = tmp_path / "todo.py"
        file_path.write_text(code)

        schema = parse_doctype(file_path)

        assert schema["name"] == "Todo"
        assert schema["docstring"] == "A simple todo item."
        assert len(schema["fields"]) == 2
        assert schema["bases"] == ["BaseDocType"]

    def test_parse_fields_with_types(self, tmp_path: Path) -> None:
        """parse_doctype should extract field types and defaults."""
        code = dedent('''
            from framework_m.core.base import BaseDocType
            from typing import Optional
            from datetime import datetime
            
            
            class Invoice(BaseDocType):
                """Invoice document."""
                
                invoice_number: str
                amount: float
                due_date: datetime
                paid: bool = False
                notes: str | None = None
        ''')

        file_path = tmp_path / "invoice.py"
        file_path.write_text(code)

        schema = parse_doctype(file_path)

        assert schema["name"] == "Invoice"
        assert len(schema["fields"]) == 5

        # Check field properties
        fields_by_name = {f["name"]: f for f in schema["fields"]}

        assert fields_by_name["invoice_number"]["type"] == "str"
        assert fields_by_name["invoice_number"]["required"] is True

        assert fields_by_name["amount"]["type"] == "float"

        assert fields_by_name["paid"]["default"] == "False"
        assert fields_by_name["paid"]["required"] is False

        assert fields_by_name["notes"]["required"] is False

    def test_parse_config_class(self, tmp_path: Path) -> None:
        """parse_doctype should extract Config class metadata."""
        code = dedent('''
            from framework_m.core.base import BaseDocType
            
            
            class Order(BaseDocType):
                """Order document."""
                
                order_id: str
                
                class Config:
                    tablename = "orders"
                    verbose_name = "Sales Order"
                    is_submittable = True
        ''')

        file_path = tmp_path / "order.py"
        file_path.write_text(code)

        schema = parse_doctype(file_path)

        assert schema["name"] == "Order"
        assert schema["config"]["tablename"] == "orders"
        assert schema["config"]["verbose_name"] == "Sales Order"
        assert schema["config"]["is_submittable"] is True

    def test_parse_custom_methods(self, tmp_path: Path) -> None:
        """parse_doctype should list custom methods."""
        code = dedent('''
            from framework_m.core.base import BaseDocType
            
            
            class Item(BaseDocType):
                """Item with custom methods."""
                
                name: str
                price: float
                
                def calculate_tax(self) -> float:
                    return self.price * 0.1
                    
                def apply_discount(self, percent: float) -> None:
                    self.price *= (1 - percent / 100)
        ''')

        file_path = tmp_path / "item.py"
        file_path.write_text(code)

        schema = parse_doctype(file_path)

        assert "calculate_tax" in schema["custom_methods"]
        assert "apply_discount" in schema["custom_methods"]

    def test_parse_imports(self, tmp_path: Path) -> None:
        """parse_doctype should collect import statements."""
        code = dedent("""
            from __future__ import annotations
            
            from typing import Optional
            from datetime import datetime
            
            from framework_m.core.base import BaseDocType
            
            
            class Task(BaseDocType):
                title: str
        """)

        file_path = tmp_path / "task.py"
        file_path.write_text(code)

        schema = parse_doctype(file_path)

        assert len(schema["imports"]) >= 3
        assert any("datetime" in imp for imp in schema["imports"])

    def test_parse_file_not_found(self) -> None:
        """parse_doctype should raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            parse_doctype("/nonexistent/file.py")

    def test_parse_no_doctype(self, tmp_path: Path) -> None:
        """parse_doctype should raise ValueError if no DocType."""
        code = dedent("""
            def helper():
                pass
        """)

        file_path = tmp_path / "utils.py"
        file_path.write_text(code)

        with pytest.raises(ValueError, match="No DocType"):
            parse_doctype(file_path)


class TestFieldSchema:
    """Tests for FieldSchema dataclass."""

    def test_field_schema_defaults(self) -> None:
        """FieldSchema should have correct defaults."""
        field = FieldSchema(name="title", type="str")

        assert field.name == "title"
        assert field.type == "str"
        assert field.default is None
        assert field.required is True
        assert field.validators == {}


class TestConfigSchema:
    """Tests for ConfigSchema dataclass."""

    def test_config_schema_defaults(self) -> None:
        """ConfigSchema should have correct defaults."""
        config = ConfigSchema()

        assert config.tablename is None
        assert config.is_submittable is False
        assert config.track_changes is True
