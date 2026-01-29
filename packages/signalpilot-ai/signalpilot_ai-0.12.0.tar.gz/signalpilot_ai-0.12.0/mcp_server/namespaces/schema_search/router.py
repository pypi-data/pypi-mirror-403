"""FastAPI router for schema search tools."""

from __future__ import annotations

from fastapi import APIRouter

from namespaces.schema_search.models import (
    SchemaSearchDatabasesResponse,
    SchemaSearchRequest,
    SchemaSearchResponse,
)
from namespaces.schema_search.service import get_schema_search_service

router = APIRouter()


@router.post(
    "/search",
    name="search",
    operation_id="schema_search-search",
    summary="Search database schema by natural language query.",
    description=(
        "Run a schema search against a configured database id and return "
        "ranked table matches with relationships."
    ),
)
async def schema_search(request: SchemaSearchRequest) -> SchemaSearchResponse:
    """Search database schemas using a natural language query."""
    service = get_schema_search_service()
    return await service.search(request)


@router.get(
    "/databases",
    name="databases",
    operation_id="schema_search-list_databases",
    summary="List available schema-search databases.",
    description=(
        "Enumerate DATABASE_<ID>_URL entries from the environment and return "
        "their database ids."
    ),
)
async def list_databases() -> SchemaSearchDatabasesResponse:
    """List database ids configured for schema search."""
    service = get_schema_search_service()
    return service.list_databases()
