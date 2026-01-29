"""FastAPI router for terminal tools."""

from __future__ import annotations

from fastapi import APIRouter

from namespaces.terminal.models import (
    GlobRequest,
    GlobResponse,
    GrepRequest,
    GrepResponse,
    TerminalExecuteRequest,
    TerminalExecuteResponse,
)
from namespaces.terminal.service import get_terminal_service

router = APIRouter()


@router.post(
    "/execute",
    name="execute",
    operation_id="terminal-execute",
    summary="Execute a terminal command.",
    description="Run a shell command and return output, exit code, and optional summary.",
)
async def execute(request: TerminalExecuteRequest) -> TerminalExecuteResponse:
    """Execute a terminal command and return captured output."""
    service = get_terminal_service()
    return await service.execute(request)


@router.post(
    "/glob",
    name="glob",
    operation_id="terminal-glob",
    summary="Find files matching a glob pattern.",
    description="Search for files using glob patterns like '**/*.py' or 'src/*.ts'.",
)
async def glob(request: GlobRequest) -> GlobResponse:
    """Find files matching a glob pattern."""
    service = get_terminal_service()
    return await service.glob(request)


@router.post(
    "/grep",
    name="grep",
    operation_id="terminal-grep",
    summary="Search file contents using regex.",
    description="Search for text patterns in files with optional context lines.",
)
async def grep(request: GrepRequest) -> GrepResponse:
    """Search file contents using regex patterns."""
    service = get_terminal_service()
    return await service.grep(request)
