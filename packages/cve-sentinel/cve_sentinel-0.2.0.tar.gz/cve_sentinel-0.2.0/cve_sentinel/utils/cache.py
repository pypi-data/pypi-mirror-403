"""File-based cache for CVE data."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional


class Cache:
    """File-based cache with TTL support."""

    def __init__(self, cache_dir: Path, ttl_hours: int = 24) -> None:
        """Initialize cache with directory and TTL."""
        self.cache_dir = cache_dir
        self.ttl = timedelta(hours=ttl_hours)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_path(self, key: str) -> Path:
        """Get file path for a cache key."""
        # Sanitize key for filesystem
        safe_key = key.replace("/", "_").replace(":", "_")
        return self.cache_dir / f"{safe_key}.json"

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired."""
        cache_path = self._get_cache_path(key)

        if not cache_path.exists():
            return None

        try:
            data = json.loads(cache_path.read_text())
            cached_at = datetime.fromisoformat(data["cached_at"])
            now = datetime.now(timezone.utc)

            if now - cached_at > self.ttl:
                # Cache expired
                cache_path.unlink()
                return None

            return data["value"]
        except (json.JSONDecodeError, KeyError, ValueError):
            return None

    def set(self, key: str, value: Any) -> None:
        """Set value in cache."""
        cache_path = self._get_cache_path(key)

        data = {
            "cached_at": datetime.now(timezone.utc).isoformat(),
            "value": value,
        }

        cache_path.write_text(json.dumps(data, ensure_ascii=False))

    def clear(self) -> None:
        """Clear all cached data."""
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()
