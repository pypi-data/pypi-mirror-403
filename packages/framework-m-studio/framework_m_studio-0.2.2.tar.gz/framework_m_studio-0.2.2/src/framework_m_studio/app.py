"""Framework M Studio - Litestar Application.

This module provides the Studio web application for visual DocType building.
It serves both the API endpoints and the React SPA.

Usage:
    m studio              # Starts on port 9000
    m studio --port 9001  # Custom port
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from litestar import Litestar, Response, Router, get
from litestar.config.cors import CORSConfig
from litestar.response import File, Redirect
from litestar.static_files import create_static_files_router

from framework_m_studio.routes import DocTypeController

# Path to static files (built React app)
STATIC_DIR = Path(__file__).parent / "static"


# =============================================================================
# Studio API Routes (Health & Field Types)
# =============================================================================


@get(["/studio/api", "/studio/api/"], tags=["Studio"])
async def api_root() -> dict[str, Any]:
    """API root endpoint with available endpoints."""
    return {
        "service": "framework-m-studio",
        "version": "0.1.0",
        "endpoints": {
            "health": "/studio/api/health",
            "field_types": "/studio/api/field-types",
            "doctypes": "/studio/api/doctypes",
        },
    }


def _get_spa_response(path: str) -> Response[Any]:
    """Helper to serve SPA files."""
    if not STATIC_DIR.exists():
        # Development mode: no built assets yet
        return Response(
            content={
                "message": "Studio UI not built yet",
                "hint": "Run: cd apps/studio/studio_ui && pnpm build",
                "api_health": "/studio/api/health",
                "api_doctypes": "/studio/api/doctypes",
                "api_field_types": "/studio/api/field-types",
            },
            media_type="application/json",
        )

    # Check for actual file
    file_path = STATIC_DIR / path
    if file_path.is_file():
        # Serve the actual file with proper content type detection
        content = file_path.read_bytes()
        # Let Litestar infer content type from file extension
        from mimetypes import guess_type

        content_type, _ = guess_type(str(file_path))
        return Response(
            content=content,
            media_type=content_type or "application/octet-stream",
        )

    # Serve index.html for SPA routing (fallback for client-side routes)
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        content = index_path.read_bytes()
        return Response(
            content=content,
            media_type="text/html; charset=utf-8",
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",
            },
        )

    return Response(
        content={"error": "Studio UI not found"},
        media_type="application/json",
        status_code=404,
    )


@get("/studio/ui/{path:path}", include_in_schema=False)
async def serve_spa(path: str) -> Response[Any]:
    """Serve Studio SPA with client-side routing support under /studio/ui/*."""
    return _get_spa_response(path)


@get(["/studio/ui", "/studio/ui/"], include_in_schema=False)
async def serve_studio_root() -> Response[Any]:
    """Serve Studio root (index.html) at /studio/ui."""
    return _get_spa_response("index.html")


@get(["/studio", "/studio/"], include_in_schema=False)
async def redirect_to_ui() -> Redirect:
    """Redirect /studio to /studio/ui/ for convenience."""
    return Redirect(path="/studio/ui/")


@get("/studio/api/health", tags=["Studio"])
async def health_check() -> dict[str, str]:
    """Health check endpoint for Studio API."""
    return {"status": "ok", "service": "framework-m-studio"}


@get("/studio/api/field-types", tags=["Studio"])
async def list_field_types() -> dict[str, Any]:
    """List available field types.

    Returns built-in types plus any registered by installed apps.
    Uses FieldRegistry for dynamic discovery.
    """
    try:
        from framework_m.adapters.db.field_registry import FieldRegistry

        types_list = []
        for type_info in FieldRegistry.get_instance().get_all_types():
            types_list.append(
                {
                    "name": type_info.name,
                    "pydantic_type": type_info.pydantic_type,
                    "label": type_info.label,
                    "ui_widget": type_info.ui_widget,
                    "category": type_info.category,
                    "validators": type_info.validators,
                }
            )
        return {"field_types": types_list}
    except ImportError:
        # Fallback to static list if framework_m not available
        return {
            "field_types": [
                {
                    "name": "str",
                    "pydantic_type": "str",
                    "label": "Text",
                    "ui_widget": "text",
                    "category": "text",
                },
                {
                    "name": "int",
                    "pydantic_type": "int",
                    "label": "Integer",
                    "ui_widget": "number",
                    "category": "number",
                },
                {
                    "name": "float",
                    "pydantic_type": "float",
                    "label": "Decimal",
                    "ui_widget": "number",
                    "category": "number",
                },
                {
                    "name": "bool",
                    "pydantic_type": "bool",
                    "label": "Checkbox",
                    "ui_widget": "checkbox",
                    "category": "boolean",
                },
                {
                    "name": "date",
                    "pydantic_type": "date",
                    "label": "Date",
                    "ui_widget": "date",
                    "category": "datetime",
                },
                {
                    "name": "datetime",
                    "pydantic_type": "datetime",
                    "label": "DateTime",
                    "ui_widget": "datetime",
                    "category": "datetime",
                },
            ]
        }


# =============================================================================
# SPA Serving (Catch-all for React Router)
# =============================================================================


@get("/favicon.ico", include_in_schema=False)
async def serve_favicon() -> File | dict[str, str]:
    """Serve favicon from static directory."""
    favicon_path = STATIC_DIR / "favicon.ico"
    if favicon_path.exists():
        return File(path=favicon_path)
    return {"error": "Favicon not found"}


@get("/", include_in_schema=False)
async def root_redirect() -> Redirect:
    """Redirect root to /studio/."""
    return Redirect(path="/studio/")


# =============================================================================
# Router and App Assembly
# =============================================================================

studio_api_router = Router(
    path="/",
    route_handlers=[
        api_root,
        health_check,
        list_field_types,
    ],
)


def create_app() -> Litestar:
    """Create the Studio Litestar application."""
    route_handlers: list[Any] = [
        studio_api_router,
        DocTypeController,  # File System API for DocTypes
    ]
    # Always include favicon and redirects
    route_handlers.extend(
        [
            serve_favicon,
            root_redirect,
        ]
    )

    # Create static files router for Studio SPA
    # HashRouter is used on the frontend, so we only need to serve index.html at root
    # and static assets.

    # Static assets (js/css/images)
    if STATIC_DIR.exists():
        route_handlers.append(
            create_static_files_router(
                path="/studio/ui/assets",
                directories=[STATIC_DIR / "assets"],
                name="studio_assets",
                html_mode=False,
            )
        )

    # We mount the serve_studio_root handler which has path="/studio" and "/studio/"
    route_handlers.append(serve_studio_root)
    route_handlers.append(serve_spa)
    route_handlers.append(redirect_to_ui)
    # CORS config for development (frontend on different port)
    cors_config = CORSConfig(
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )

    return Litestar(
        route_handlers=route_handlers,
        cors_config=cors_config,
        debug=True,
        openapi_config=None,  # Studio doesn't need its own OpenAPI
    )


# Application instance for uvicorn
app = create_app()


__all__ = [
    "app",
    "create_app",
]
