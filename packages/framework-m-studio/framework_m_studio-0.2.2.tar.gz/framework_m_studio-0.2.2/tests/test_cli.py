"""Tests for Studio CLI Commands.

Tests the CLI commands following TDD principles as per CONTRIBUTING.md.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from framework_m_studio.cli import codegen_app, docs_app, studio_app


class TestCodegenApp:
    """Tests for codegen_app CLI."""

    def test_codegen_app_exists(self) -> None:
        """Test that codegen_app is defined."""
        assert codegen_app is not None
        assert "codegen" in codegen_app.name

    def test_codegen_client_command(
        self, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ) -> None:
        """Test codegen client command runs with real sdk_generator."""
        from framework_m_studio.cli import codegen_client

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
            codegen_client(
                lang="ts",
                out=str(tmp_path / "generated"),
                openapi_url="http://localhost:8000/schema/openapi.json",
            )

        captured = capsys.readouterr()
        assert "Generating TS client" in captured.out
        assert (tmp_path / "generated").exists()

    def test_codegen_doctype_command(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test codegen doctype command runs."""
        from framework_m_studio.cli import codegen_doctype

        codegen_doctype(name="TestDocType", app=None)
        captured = capsys.readouterr()
        assert "Generating DocType: TestDocType" in captured.out


class TestDocsApp:
    """Tests for docs_app CLI."""

    def test_docs_app_exists(self) -> None:
        """Test that docs_app is defined."""
        assert docs_app is not None
        assert "docs" in docs_app.name

    def test_docs_generate_command(
        self, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ) -> None:
        """Test docs generate command runs."""
        from framework_m_studio.cli import docs_generate

        output_dir = str(tmp_path / "docs")
        docs_generate(output=output_dir, openapi_url=None)
        captured = capsys.readouterr()
        # Accept either format (with doctypes or fallback)
        assert "documentation" in captured.out.lower() or "docs" in captured.out.lower()


class TestStudioApp:
    """Tests for studio_app CLI."""

    def test_studio_app_exists(self) -> None:
        """Test that studio_app is defined."""
        assert studio_app is not None
        assert "studio" in studio_app.name

    def test_studio_serve_prints_banner(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test studio serve prints startup banner before running uvicorn."""
        from framework_m_studio.cli import studio_serve

        # Mock uvicorn.run to prevent actual server startup
        with patch("uvicorn.run") as mock_uvicorn:
            studio_serve(port=9000, host="127.0.0.1", reload=False, cloud=False)

            captured = capsys.readouterr()
            assert "Starting Framework M Studio" in captured.out
            assert "127.0.0.1:9000" in captured.out

            # Verify uvicorn was called with correct args
            mock_uvicorn.assert_called_once_with(
                "framework_m_studio.app:app",
                host="127.0.0.1",
                port=9000,
                reload=False,
                log_level="info",
            )

    def test_studio_serve_custom_port(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test studio serve with custom port."""
        from framework_m_studio.cli import studio_serve

        with patch("uvicorn.run") as mock_uvicorn:
            studio_serve(port=8080, host="0.0.0.0", reload=False, cloud=False)

            mock_uvicorn.assert_called_once()
            call_kwargs = mock_uvicorn.call_args[1]
            assert call_kwargs["port"] == 8080
            assert call_kwargs["host"] == "0.0.0.0"

    def test_studio_serve_reload_mode(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test studio serve with reload enabled."""
        from framework_m_studio.cli import studio_serve

        with patch("uvicorn.run") as mock_uvicorn:
            studio_serve(port=9000, host="127.0.0.1", reload=True, cloud=False)

            mock_uvicorn.assert_called_once()
            call_kwargs = mock_uvicorn.call_args[1]
            assert call_kwargs["reload"] is True

    def test_studio_serve_cloud_mode(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test studio serve with cloud mode enabled."""
        from framework_m_studio.cli import studio_serve

        with patch("uvicorn.run"), patch.dict("os.environ", {}, clear=False):
            import os

            studio_serve(port=9000, host="127.0.0.1", reload=False, cloud=True)

            captured = capsys.readouterr()
            assert "Cloud mode enabled" in captured.out
            assert os.environ.get("STUDIO_CLOUD_MODE") == "1"


class TestModuleExports:
    """Tests for module exports."""

    def test_all_exports(self) -> None:
        """Test __all__ exports are correct."""
        from framework_m_studio import cli

        assert hasattr(cli, "__all__")
        assert "codegen_app" in cli.__all__
        assert "docs_app" in cli.__all__
        assert "studio_app" in cli.__all__
