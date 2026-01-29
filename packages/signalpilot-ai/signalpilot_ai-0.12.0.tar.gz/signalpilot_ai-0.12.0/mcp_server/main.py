"""FastAPI entrypoint for MCP tools."""

from __future__ import annotations

import logging
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi_mcp import FastApiMCP

from namespaces.files.router import router as files_router
from namespaces.schema_search.router import router as schema_search_router
from namespaces.terminal.router import router as terminal_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _load_dotenv() -> None:
    env_path = Path(__file__).with_name(".env")
    if env_path.exists():
        load_dotenv(env_path)
    else:
        logger.warning(".env file not found, using environment variables")


def create_app() -> FastAPI:
    _load_dotenv()
    app = FastAPI(title="SignalPilot MCP Server")

    app.include_router(terminal_router, prefix="/terminal", tags=["terminal"])
    app.include_router(
        schema_search_router,
        prefix="/schema-search",
        tags=["schema-search"],
    )
    app.include_router(
        files_router,
        prefix="/files",
        tags=["files"],
    )

    mcp = FastApiMCP(app)
    mcp.mount()
    return app


app = create_app()
