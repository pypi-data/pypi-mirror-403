"""Pydantic models for schema search tool inputs/outputs."""

from __future__ import annotations

from pydantic import BaseModel, Field

from namespaces.base.models import BaseRequest, BaseResponse
from namespaces.schema_search.constants import (
    DEFAULT_SCHEMA_SEARCH_LIMIT,
    MAX_SCHEMA_SEARCH_LIMIT,
    MIN_SCHEMA_SEARCH_LIMIT,
)


class SchemaSearchRequest(BaseRequest):
    """Request to search database schema."""

    query: str = Field(..., description="Natural language query for schema search.")
    database_id: str = Field(
        ...,
        description="Database id used to resolve DATABASE_<ID>_URL from .env.",
    )
    limit: int = Field(
        DEFAULT_SCHEMA_SEARCH_LIMIT,
        description=f"Max number of tables to return. Default is {DEFAULT_SCHEMA_SEARCH_LIMIT}.",
        ge=MIN_SCHEMA_SEARCH_LIMIT,
        le=MAX_SCHEMA_SEARCH_LIMIT,
    )
    force_reindex: bool = Field(
        False,
        description="Force reindexing schema metadata. Default is False.",
    )


class SchemaSearchResponse(BaseResponse):
    """Response from schema search."""

    database_id: str = Field(..., description="Database id used for the query.")


class SchemaSearchDatabasesResponse(BaseModel):
    """Response listing available databases."""

    databases: list[str] = Field(
        ..., description="Available database ids derived from DATABASE_<ID>_URL."
    )
    count: int = Field(..., description="Number of available databases.")
