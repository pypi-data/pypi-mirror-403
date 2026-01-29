"""Tests for Documentation Generator.

Tests for the `m docs:generate` CLI command following TDD.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestDocsGenerator:
    """Tests for docs generator module."""

    def test_generate_doctype_markdown(self, tmp_path: Path) -> None:
        """Test generating markdown from DocType info."""
        from framework_m_studio.docs_generator import generate_doctype_markdown

        doctype_info = {
            "name": "Invoice",
            "docstring": "Represents a sales invoice.",
            "fields": [
                {"name": "number", "type": "str", "description": "Invoice number"},
                {"name": "amount", "type": "float", "description": "Total amount"},
                {"name": "is_paid", "type": "bool", "description": "Payment status"},
            ],
        }

        markdown = generate_doctype_markdown(doctype_info)

        assert "# Invoice" in markdown
        assert "Represents a sales invoice." in markdown
        assert "| number |" in markdown
        assert "| amount |" in markdown
        assert "| is_paid |" in markdown

    def test_generate_api_reference(self, tmp_path: Path) -> None:
        """Test generating API reference from multiple DocTypes."""
        from framework_m_studio.docs_generator import generate_api_reference

        doctypes = [
            {
                "name": "Invoice",
                "docstring": "Invoice DocType",
                "fields": [{"name": "number", "type": "str"}],
            },
            {
                "name": "Customer",
                "docstring": "Customer DocType",
                "fields": [{"name": "name", "type": "str"}],
            },
        ]

        output_dir = tmp_path / "docs"
        generate_api_reference(doctypes, output_dir)

        assert (output_dir / "invoice.md").exists()
        assert (output_dir / "customer.md").exists()
        assert (output_dir / "index.md").exists()

    def test_export_openapi_json(self, tmp_path: Path) -> None:
        """Test exporting OpenAPI JSON from app."""
        from framework_m_studio.docs_generator import export_openapi_json

        output_file = tmp_path / "openapi.json"

        # Mock the HTTP request - patch where urlopen is used, not where it's defined
        mock_schema = {
            "openapi": "3.1.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {},
        }

        with patch("framework_m_studio.docs_generator.urlopen") as mock_urlopen:
            import json

            mock_fp = MagicMock()
            mock_fp.read.return_value = json.dumps(mock_schema).encode()
            mock_fp.__enter__ = MagicMock(return_value=mock_fp)
            mock_fp.__exit__ = MagicMock(return_value=False)
            mock_urlopen.return_value = mock_fp

            export_openapi_json(
                "http://localhost:8000/schema/openapi.json", output_file
            )

        assert output_file.exists()
        content = output_file.read_text()
        assert "openapi" in content
        assert "3.1.0" in content


class TestDocsGeneratorCLI:
    """Tests for docs:generate CLI integration."""

    def test_docs_generate_creates_output_dir(self, tmp_path: Path) -> None:
        """Test that docs:generate creates output directory."""
        from framework_m_studio.docs_generator import run_docs_generate

        output_dir = tmp_path / "docs" / "api"

        # Mock discovery to return empty list
        with patch("framework_m_studio.discovery.scan_doctypes", return_value=[]):
            run_docs_generate(output=str(output_dir), project_root=str(tmp_path))

        assert output_dir.exists()

    def test_docs_generate_with_doctypes(self, tmp_path: Path) -> None:
        """Test docs:generate with discovered DocTypes."""
        from framework_m_studio.docs_generator import run_docs_generate

        output_dir = tmp_path / "docs"

        # Mock discovery
        mock_doctype = MagicMock()
        mock_doctype.name = "TestDoc"
        mock_doctype.docstring = "Test docstring"
        mock_doctype.fields = []
        mock_doctype.file_path = str(tmp_path / "test.py")

        with (
            patch(
                "framework_m_studio.discovery.scan_doctypes",
                return_value=[mock_doctype],
            ),
            patch("framework_m_studio.discovery.doctype_to_dict") as mock_to_dict,
        ):
            mock_to_dict.return_value = {
                "name": "TestDoc",
                "docstring": "Test docstring",
                "fields": [],
            }
            run_docs_generate(output=str(output_dir), project_root=str(tmp_path))

        assert (output_dir / "testdoc.md").exists() or (
            output_dir / "index.md"
        ).exists()


class TestMarkdownFormatting:
    """Tests for markdown formatting utilities."""

    def test_field_table_formatting(self) -> None:
        """Test field table markdown generation."""
        from framework_m_studio.docs_generator import format_field_table

        fields = [
            {
                "name": "id",
                "type": "int",
                "required": True,
                "description": "Primary key",
            },
            {"name": "name", "type": "str", "required": True, "description": "Name"},
            {
                "name": "email",
                "type": "str",
                "required": False,
                "description": "Email address",
            },
        ]

        table = format_field_table(fields)

        assert "| Field | Type | Required | Description |" in table
        assert "| id | int |" in table
        assert "| name | str |" in table
        assert "| email | str |" in table

    def test_index_generation(self) -> None:
        """Test index.md generation."""
        from framework_m_studio.docs_generator import generate_index

        doctypes = ["Invoice", "Customer", "Product"]

        index_md = generate_index(doctypes)

        assert "# API Reference" in index_md
        assert "[Invoice](invoice.md)" in index_md
        assert "[Customer](customer.md)" in index_md
        assert "[Product](product.md)" in index_md


class TestMkDocsBuild:
    """Tests for mkdocs build integration."""

    def test_run_mkdocs_build_no_mkdocs(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test mkdocs build when mkdocs is not installed."""
        from framework_m_studio.docs_generator import run_mkdocs_build

        with patch("shutil.which", return_value=None):
            result = run_mkdocs_build(tmp_path)

        assert result is False
        captured = capsys.readouterr()
        assert "mkdocs not found" in captured.out

    def test_run_mkdocs_build_no_config(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test mkdocs build when mkdocs.yml doesn't exist."""
        from framework_m_studio.docs_generator import run_mkdocs_build

        with patch("shutil.which", return_value="/usr/bin/mkdocs"):
            result = run_mkdocs_build(tmp_path)

        assert result is False
        captured = capsys.readouterr()
        assert "No mkdocs.yml found" in captured.out

    def test_run_mkdocs_build_success(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test successful mkdocs build."""
        from framework_m_studio.docs_generator import run_mkdocs_build

        # Create mkdocs.yml
        (tmp_path / "mkdocs.yml").write_text("site_name: Test")

        mock_result = MagicMock()
        mock_result.returncode = 0

        with (
            patch("shutil.which", return_value="/usr/bin/mkdocs"),
            patch("subprocess.run", return_value=mock_result) as mock_run,
        ):
            result = run_mkdocs_build(tmp_path)

        assert result is True
        mock_run.assert_called_once()
        captured = capsys.readouterr()
        assert "Site built successfully" in captured.out
