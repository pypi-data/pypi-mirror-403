"""Framework M Studio CLI Commands.

This module provides CLI commands that are registered via entry points
when framework-m-studio is installed. These extend the base `m` CLI
with developer tools.

Entry Point Registration (pyproject.toml):
    [project.entry-points."framework_m.cli_commands"]
    codegen = "framework_m_studio.cli:codegen_app"
"""

from __future__ import annotations

from typing import Annotated

import cyclopts

# =============================================================================
# Codegen Sub-App
# =============================================================================

codegen_app = cyclopts.App(
    name="codegen",
    help="Code generation tools for Framework M",
)


@codegen_app.command(name="client")
def codegen_client(
    lang: Annotated[
        str,
        cyclopts.Parameter(
            name="--lang",
            help="Target language: ts (TypeScript) or py (Python)",
        ),
    ] = "ts",
    out: Annotated[
        str,
        cyclopts.Parameter(
            name="--out",
            help="Output directory for generated code",
        ),
    ] = "./generated",
    openapi_url: Annotated[
        str,
        cyclopts.Parameter(
            name="--openapi-url",
            help="URL to fetch OpenAPI schema from",
        ),
    ] = "http://localhost:8000/schema/openapi.json",
) -> None:
    """Generate API client from OpenAPI schema.

    Examples:
        m codegen client --lang ts --out ./frontend/src/api
        m codegen client --lang py --out ./scripts/api_client
    """
    from pathlib import Path

    from framework_m_studio.sdk_generator import (
        fetch_openapi_schema,
        generate_typescript_client,
        generate_typescript_types,
    )

    print(f"Generating {lang.upper()} client...")
    print(f"  OpenAPI URL: {openapi_url}")
    print(f"  Output: {out}")

    # Create output directory
    output_path = Path(out)
    output_path.mkdir(parents=True, exist_ok=True)

    # Fetch schema and generate
    schema = fetch_openapi_schema(openapi_url)
    if lang.lower() == "ts":
        types_code = generate_typescript_types(schema)
        client_code = generate_typescript_client(schema)
        (output_path / "types.ts").write_text(types_code)
        (output_path / "client.ts").write_text(client_code)


@codegen_app.command(name="doctype")
def codegen_doctype(
    name: Annotated[
        str,
        cyclopts.Parameter(help="DocType class name (PascalCase)"),
    ],
    app: Annotated[
        str | None,
        cyclopts.Parameter(
            name="--app",
            help="Target app directory",
        ),
    ] = None,
) -> None:
    """Generate DocType Python code from schema.

    This is the programmatic version of the Studio UI's
    DocType builder. Useful for CI/CD pipelines.

    Examples:
        m codegen doctype Invoice --app apps/billing
    """
    print(f"Generating DocType: {name}")
    if app:
        print(f"  Target app: {app}")
    print()
    print("⚠️  Not yet implemented. Coming in Phase 07.")
    print("    Will use LibCST for code generation")


# =============================================================================
# Docs Sub-App (Optional - registered via separate entry point if needed)
# =============================================================================

docs_app = cyclopts.App(
    name="docs",
    help="Documentation generation tools",
)


@docs_app.command(name="generate")
def docs_generate(
    output: Annotated[
        str,
        cyclopts.Parameter(
            name="--output",
            help="Output directory for documentation",
        ),
    ] = "./docs/api",
    openapi_url: Annotated[
        str | None,
        cyclopts.Parameter(
            name="--openapi-url",
            help="URL to fetch OpenAPI schema from (optional)",
        ),
    ] = None,
) -> None:
    """Generate API documentation from DocTypes.

    Examples:
        m docs generate --output ./docs/api
    """
    from pathlib import Path

    from framework_m_studio.docs_generator import run_docs_generate

    # Use current working directory as project root
    project_root = Path.cwd()

    # Look in src/doctypes if it exists, otherwise use project root
    doctypes_dir = project_root / "src" / "doctypes"
    scan_root = project_root / "src" if doctypes_dir.exists() else project_root

    run_docs_generate(
        output=output,
        project_root=str(scan_root),
        openapi_url=openapi_url,
    )


# =============================================================================
# Studio Sub-App (Main command to start Studio server)
# =============================================================================

studio_app = cyclopts.App(
    name="studio",
    help="Start Framework M Studio visual editor",
)


@studio_app.default
def studio_serve(
    port: Annotated[
        int,
        cyclopts.Parameter(
            name="--port",
            help="Port to run Studio on",
        ),
    ] = 9000,
    host: Annotated[
        str,
        cyclopts.Parameter(
            name="--host",
            help="Host to bind to",
        ),
    ] = "127.0.0.1",
    reload: Annotated[
        bool,
        cyclopts.Parameter(
            name="--reload",
            help="Enable auto-reload for development",
        ),
    ] = False,
    cloud: Annotated[
        bool,
        cyclopts.Parameter(
            name="--cloud",
            help="Enable cloud mode (Git-backed workspaces)",
        ),
    ] = False,
) -> None:
    """Start Framework M Studio.

    Examples:
        m studio              # Start on port 9000
        m studio --port 8000  # Custom port
        m studio --reload     # Development mode
        m studio --cloud      # Enable cloud mode
    """
    import os

    import uvicorn

    # Print startup banner
    print()
    print("🎨 Starting Framework M Studio")
    print(f"   ➜ Local:   http://{host}:{port}/studio/")
    print(f"   ➜ API:     http://{host}:{port}/studio/api/")
    print(f"  🔌 API Health:   http://{host}:{port}/studio/api/health")
    print()

    if cloud:
        print("☁️  Cloud mode enabled - Git-backed workspaces")
        os.environ["STUDIO_CLOUD_MODE"] = "1"
        print()

    # Start uvicorn
    uvicorn.run(
        "framework_m_studio.app:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )


__all__ = [
    "codegen_app",
    "codegen_client",
    "codegen_doctype",
    "docs_app",
    "docs_generate",
    "studio_app",
    "studio_serve",
]
