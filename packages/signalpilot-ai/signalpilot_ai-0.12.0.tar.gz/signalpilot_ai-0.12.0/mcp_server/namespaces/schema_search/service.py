"""Schema search tool service."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

from fastapi import HTTPException
from schema_search import SchemaSearch
from sqlalchemy import create_engine

from namespaces.base.output_processor import OutputProcessor
from namespaces.base.service import BaseService
from namespaces.schema_search.models import (
    SchemaSearchDatabasesResponse,
    SchemaSearchRequest,
    SchemaSearchResponse,
)

logger = logging.getLogger(__name__)


class SchemaSearchService(BaseService):
    """Coordinates schema search with cached SchemaSearch instances."""

    def __init__(self, *, config_path: Optional[Path] = None) -> None:
        super().__init__("schema_search")
        self._config_path = config_path or (
            Path(__file__).resolve().parents[2] / "configs" / "schema_search.yml"
        )
        self._searchers: dict[str, SchemaSearch] = {}

    def _get_prompt_path(self) -> Path:
        """Return path to prompt.md in schema_search namespace."""
        return Path(__file__).parent / self.prompt_file

    async def search(self, request: SchemaSearchRequest) -> SchemaSearchResponse:
        """Execute schema search and return results."""
        try:
            searcher = self._get_searcher(request.database_id)
            results_text = self._run_search(searcher, request)

            output, truncated, summary = await self._output_processor.process(
                query=request.query,
                output=results_text,
                prompt=self._system_prompt,
                force_refresh=request.force_refresh,
            )

            return SchemaSearchResponse(
                database_id=request.database_id,
                output=output,
                truncated=truncated,
                summary=summary,
            )
        except HTTPException:
            raise
        except Exception as exc:
            logger.error(f"schema search failed: {exc}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"{type(exc).__name__}: {exc}")

    def list_databases(self) -> SchemaSearchDatabasesResponse:
        """List available database ids from environment."""
        prefix = "DATABASE_"
        suffix = "_URL"
        databases = []
        for key in os.environ:
            if key.startswith(prefix) and key.endswith(suffix):
                raw_id = key[len(prefix) : -len(suffix)]
                if raw_id:
                    databases.append(raw_id)
        databases = sorted(set(databases))
        return SchemaSearchDatabasesResponse(databases=databases, count=len(databases))

    def _get_searcher(self, database_id: str) -> SchemaSearch:
        """Get or create a cached SchemaSearch instance."""
        if database_id in self._searchers:
            return self._searchers[database_id]

        database_url = self._resolve_database_url(database_id)
        config_path = self._resolve_config_path()
        engine = create_engine(database_url)
        searcher = SchemaSearch(engine=engine, config_path=config_path)
        self._searchers[database_id] = searcher
        return searcher

    def _run_search(self, searcher: SchemaSearch, request: SchemaSearchRequest) -> str:
        """Run the actual search operation."""
        searcher.index(force=request.force_reindex)
        results = searcher.search(request.query, limit=request.limit)
        return str(results)

    def _resolve_database_url(self, database_id: str) -> str:
        """Resolve database URL from environment variable."""
        normalized = database_id.strip().upper().replace("-", "_").replace(" ", "_")
        env_key = f"DATABASE_{normalized}_URL"
        database_url = os.getenv(env_key)
        if not database_url:
            raise HTTPException(
                status_code=404, detail=f"Environment variable {env_key} is not set."
            )
        return database_url

    def _resolve_config_path(self) -> str:
        """Resolve and validate config file path."""
        resolved = self._config_path.resolve()
        if not resolved.exists():
            raise HTTPException(
                status_code=404, detail=f"Config file not found: {resolved}"
            )
        return str(resolved)


_schema_search_service: Optional[SchemaSearchService] = None


def get_schema_search_service() -> SchemaSearchService:
    """Get or create the singleton service instance."""
    global _schema_search_service
    if _schema_search_service is None:
        _schema_search_service = SchemaSearchService()
    return _schema_search_service
