"""Tests for schema search tool."""

from namespaces.schema_search.service import SchemaSearchService


def test_list_databases(client):
    """Test listing available databases."""
    response = client.post("/schema-search/databases", json={})
    assert response.status_code == 200
    data = response.json()
    assert "databases" in data
    assert "count" in data
    assert isinstance(data["databases"], list)
    assert data["count"] == len(data["databases"])


def test_search_requires_database(client):
    """Test search with non-existent database returns 404."""
    response = client.post(
        "/schema-search/search",
        json={"query": "test query", "database_id": "nonexistent_db"},
    )
    assert response.status_code == 404


def test_search_postgres(client, monkeypatch):
    """Test search returns results using a stubbed schema searcher."""
    def _fake_get_searcher(self, database_id):
        return object()

    def _fake_run_search(self, searcher, request):
        return "fake schema search results"

    monkeypatch.setenv("DATABASE_TEST_URL", "postgresql://user:pass@localhost/db")
    monkeypatch.setattr(SchemaSearchService, "_get_searcher", _fake_get_searcher)
    monkeypatch.setattr(SchemaSearchService, "_run_search", _fake_run_search)

    response = client.post(
        "/schema-search/search",
        json={"query": "list tables", "database_id": "test", "limit": 3},
    )
    assert response.status_code == 200
    data = response.json()
    assert "output" in data
    assert data["database_id"] == "test"
    assert data["output"] == "fake schema search results"
