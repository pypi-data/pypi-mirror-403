"""
FastAPI application for PinkyClawd server.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from pinkyclawd.server.routes import chat, mcp, session


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan events."""
    # Startup
    print("Starting PinkyClawd server...")

    # Initialize storage
    from pinkyclawd.config.storage import get_storage
    get_storage()

    # Initialize provider registry
    from pinkyclawd.provider.registry import get_provider_registry
    await get_provider_registry()

    yield

    # Shutdown
    print("Shutting down PinkyClawd server...")

    # Cleanup MCP clients
    from pinkyclawd.mcp import get_mcp_client
    await get_mcp_client().remove_all()

    # Cleanup LSP clients
    from pinkyclawd.lsp import get_lsp_client
    await get_lsp_client().stop_all()


def create_app(
    debug: bool = False,
    working_directory: Path | None = None,
) -> FastAPI:
    """
    Create the FastAPI application.

    Args:
        debug: Enable debug mode
        working_directory: Default working directory

    Returns:
        FastAPI application
    """
    app = FastAPI(
        title="PinkyClawd",
        description="AI-powered development tool with RLM context management",
        version="1.0.0",
        lifespan=lifespan,
        debug=debug,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Store working directory in app state
    if working_directory:
        app.state.working_directory = working_directory
    else:
        app.state.working_directory = Path.cwd()

    # Exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_error",
                "message": str(exc),
            },
        )

    # Health check
    @app.get("/health")
    async def health_check():
        return {"status": "ok"}

    # Version info
    @app.get("/version")
    async def version_info():
        from pinkyclawd import __version__
        return {
            "version": __version__,
            "name": "PinkyClawd",
        }

    # Include routers
    app.include_router(session.router, prefix="/session", tags=["session"])
    app.include_router(chat.router, prefix="/chat", tags=["chat"])
    app.include_router(mcp.router, prefix="/mcp", tags=["mcp"])

    return app


def run_server(
    host: str = "127.0.0.1",
    port: int = 4096,
    debug: bool = False,
    working_directory: Path | None = None,
) -> None:
    """
    Run the server.

    Args:
        host: Host to bind to
        port: Port to listen on
        debug: Enable debug mode
        working_directory: Default working directory
    """
    import uvicorn

    app = create_app(debug=debug, working_directory=working_directory)

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="debug" if debug else "info",
    )
