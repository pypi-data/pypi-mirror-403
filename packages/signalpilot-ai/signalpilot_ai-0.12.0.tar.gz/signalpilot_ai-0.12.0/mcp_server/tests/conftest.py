"""Shared pytest fixtures."""

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from main import app


@pytest.fixture
def client():
    """Sync test client for FastAPI app."""
    with TestClient(app) as client:
        yield client
