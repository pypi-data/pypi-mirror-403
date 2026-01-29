"""Tests for Client SDK Generator.

Tests for the `m codegen client` CLI command following TDD.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch


class TestCodegenFetchOpenAPI:
    """Tests for fetching OpenAPI schema."""

    def test_fetch_openapi_schema(self, tmp_path: Path) -> None:
        """Test fetching OpenAPI schema from URL."""
        from framework_m_studio.sdk_generator import fetch_openapi_schema

        mock_schema = {
            "openapi": "3.1.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/users": {"get": {"operationId": "list_users"}},
            },
        }

        with patch("framework_m_studio.sdk_generator.urlopen") as mock_urlopen:
            mock_fp = MagicMock()
            mock_fp.read.return_value = json.dumps(mock_schema).encode()
            mock_fp.__enter__ = MagicMock(return_value=mock_fp)
            mock_fp.__exit__ = MagicMock(return_value=False)
            mock_urlopen.return_value = mock_fp

            schema = fetch_openapi_schema("http://localhost:8000/schema/openapi.json")

        assert schema["openapi"] == "3.1.0"
        assert "paths" in schema


class TestTypeScriptGenerator:
    """Tests for TypeScript client generation."""

    def test_generate_typescript_types(self) -> None:
        """Test generating TypeScript types from OpenAPI schemas."""
        from framework_m_studio.sdk_generator import generate_typescript_types

        schema = {
            "components": {
                "schemas": {
                    "User": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"},
                            "name": {"type": "string"},
                            "email": {"type": "string"},
                        },
                        "required": ["id", "name"],
                    }
                }
            }
        }

        ts_code = generate_typescript_types(schema)

        assert "interface User" in ts_code or "type User" in ts_code
        assert "id:" in ts_code
        assert "name:" in ts_code
        assert "email" in ts_code

    def test_generate_typescript_client(self) -> None:
        """Test generating TypeScript fetch client."""
        from framework_m_studio.sdk_generator import generate_typescript_client

        schema = {
            "openapi": "3.1.0",
            "info": {"title": "Test API"},
            "paths": {
                "/users": {
                    "get": {
                        "operationId": "listUsers",
                        "responses": {"200": {"description": "OK"}},
                    }
                }
            },
        }

        client_code = generate_typescript_client(schema)

        assert "listUsers" in client_code
        assert "fetch" in client_code


class TestPythonGenerator:
    """Tests for Python client generation."""

    def test_generate_python_models(self) -> None:
        """Test generating Python Pydantic models from OpenAPI schemas."""
        from framework_m_studio.sdk_generator import generate_python_models

        schema = {
            "components": {
                "schemas": {
                    "User": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"},
                            "name": {"type": "string"},
                        },
                        "required": ["id", "name"],
                    }
                }
            }
        }

        py_code = generate_python_models(schema)

        assert "class User" in py_code
        assert "id:" in py_code
        assert "name:" in py_code


class TestRunCodegen:
    """Tests for run_codegen entry point."""

    def test_run_codegen_typescript(self, tmp_path: Path) -> None:
        """Test running codegen for TypeScript."""
        from framework_m_studio.sdk_generator import run_codegen

        mock_schema = {
            "openapi": "3.1.0",
            "info": {"title": "Test API"},
            "paths": {},
            "components": {"schemas": {}},
        }

        with patch(
            "framework_m_studio.sdk_generator.fetch_openapi_schema",
            return_value=mock_schema,
        ):
            run_codegen(
                lang="ts",
                out=str(tmp_path / "generated"),
                openapi_url="http://localhost:8000/schema/openapi.json",
            )

        # Check that files were created
        assert (tmp_path / "generated").exists()

    def test_run_codegen_python(self, tmp_path: Path) -> None:
        """Test running codegen for Python."""
        from framework_m_studio.sdk_generator import run_codegen

        mock_schema = {
            "openapi": "3.1.0",
            "info": {"title": "Test API"},
            "paths": {},
            "components": {"schemas": {}},
        }

        with patch(
            "framework_m_studio.sdk_generator.fetch_openapi_schema",
            return_value=mock_schema,
        ):
            run_codegen(
                lang="py",
                out=str(tmp_path / "generated"),
                openapi_url="http://localhost:8000/schema/openapi.json",
            )

        # Check that files were created
        assert (tmp_path / "generated").exists()
