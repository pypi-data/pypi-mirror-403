"""Tests for Studio API Routes."""

from __future__ import annotations

from litestar.status_codes import HTTP_200_OK
from litestar.testing import TestClient


def test_health_check(client: TestClient) -> None:
    """Test health check endpoint."""
    response = client.get("/studio/api/health")
    assert response.status_code == HTTP_200_OK
    assert response.json() == {"status": "ok", "service": "framework-m-studio"}


def test_studio_root_redirect(client: TestClient) -> None:
    """Test /studio redirects to /studio/ui/."""
    # TestClient follows redirects by default? default is True in requests, usually False in starlette/litestar
    # Litestar TestClient is based on httpx.
    response = client.get("/studio", follow_redirects=False)
    # Redirect defaults to 307 in Litestar but might be 302 depending on version/config
    # Test output showed 302
    assert response.status_code in (302, 307)
    assert response.headers["location"] == "/studio/ui/"


def test_studio_ui_root(client: TestClient) -> None:
    """Test /studio/ui/ serves index.html."""
    response = client.get("/studio/ui/")
    assert response.status_code == HTTP_200_OK
    assert "text/html" in response.headers["content-type"]
    # In test env, static dir might not exist or contain build artifacts
    # The app returns a dummy response if STATIC_DIR matches nothing?
    # checking app.py _get_spa_response logic:
    # "if not STATIC_DIR.exists(): return Response(..., media_type=MediaType.HTML)"
    assert response.text  # Should return something


def test_list_field_types(client: TestClient) -> None:
    """Test /studio/api/field-types endpoint."""
    # Mock FieldRegistry first to avoid external dependencies?
    # But adapter is loaded. It should work if framework_m is installed.
    # We might need to mock if database dependencies are strict.
    # Current FieldRegistry is memory-based/hardcoded for standard types in _register_standard_types.

    response = client.get("/studio/api/field-types")
    assert response.status_code == HTTP_200_OK
    data = response.json()
    assert "field_types" in data
    assert len(data["field_types"]) > 0
    # Check for a known type
    types = [t["name"] for t in data["field_types"]]
    assert "str" in types
