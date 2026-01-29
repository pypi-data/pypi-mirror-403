"""Disk-based cache for LLM responses."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Optional

from diskcache import Cache


class DiskCache:
    """Disk-based cache with namespace support and size limits."""

    def __init__(self, cache_dir: Path, namespace: str, size_limit_mb: int) -> None:
        self._cache_path = cache_dir / namespace
        self._cache_path.mkdir(parents=True, exist_ok=True)
        self._cache = Cache(
            str(self._cache_path),
            size_limit=size_limit_mb * 1024 * 1024,
            eviction_policy="least-recently-used",
        )

    def get(self, content: str) -> Optional[str]:
        """Get a cached value by content hash."""
        key = self._make_key(content)
        value = self._cache.get(key)
        if value is None:
            return None
        return str(value)

    def set(self, content: str, value: str) -> None:
        """Set a cached value by content hash."""
        key = self._make_key(content)
        self._cache.set(key, value)

    def _make_key(self, content: str) -> str:
        """Create cache key from content."""
        return hashlib.sha256(content.encode()).hexdigest()
