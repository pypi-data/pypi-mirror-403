"""Test configuration for Studio."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from litestar.testing import TestClient

from framework_m_studio.app import app


@pytest.fixture(scope="function")
def client() -> Iterator[TestClient]:
    """Create a Litestar test client."""
    with TestClient(app=app) as client:
        yield client
