"""Hot storage for temporary search results."""

from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass, field
from typing import Any

# Approximate characters per token for chunking
CHARS_PER_TOKEN = 4


@dataclass
class HotStorage:
    """Temporary storage for filtered trajectory data."""

    search_id: str
    results: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    ttl_seconds: int = 300  # Auto-expire after 5 min

    def is_expired(self) -> bool:
        """Check if this storage entry has expired."""
        return time.time() - self.created_at > self.ttl_seconds

    def total_results(self) -> int:
        """Get total number of results."""
        return len(self.results)

    def estimate_tokens(self) -> int:
        """Estimate total tokens in stored results."""
        try:
            total_chars = len(json.dumps(self.results, default=str))
            return total_chars // CHARS_PER_TOKEN
        except (TypeError, ValueError):
            return 0


class HotStorageManager:
    """Manages temporary storage for search results."""

    def __init__(self, default_ttl: int = 300):
        self._storage: dict[str, HotStorage] = {}
        self._lock = asyncio.Lock()
        self._default_ttl = default_ttl

    async def store(
        self,
        search_id: str,
        results: list[dict[str, Any]],
        metadata: dict[str, Any] | None = None,
    ) -> HotStorage:
        """Store query results for analyst access."""
        async with self._lock:
            storage = HotStorage(
                search_id=search_id,
                results=results,
                metadata=metadata or {},
                ttl_seconds=self._default_ttl,
            )
            self._storage[search_id] = storage
            return storage

    async def append(
        self,
        search_id: str,
        results: list[dict[str, Any]],
    ) -> int:
        """Append additional results to existing storage."""
        async with self._lock:
            if search_id not in self._storage:
                raise KeyError(f"No hot storage found for search_id: {search_id}")
            self._storage[search_id].results.extend(results)
            return len(self._storage[search_id].results)

    async def get(self, search_id: str) -> HotStorage | None:
        """Get hot storage by search_id."""
        async with self._lock:
            storage = self._storage.get(search_id)
            if storage and storage.is_expired():
                del self._storage[search_id]
                return None
            return storage

    async def get_chunk(
        self,
        search_id: str,
        offset: int = 0,
        token_limit: int = 100_000,
    ) -> tuple[list[dict[str, Any]], int]:
        """
        Get next chunk of results within token budget.

        Returns:
            Tuple of (results, next_offset)
        """
        async with self._lock:
            storage = self._storage.get(search_id)
            if storage is None or storage.is_expired():
                return [], offset

            results = storage.results
            if offset >= len(results):
                return [], offset

            chunk = []
            token_count = 0
            current_idx = offset

            while current_idx < len(results) and token_count < token_limit:
                item = results[current_idx]
                item_tokens = len(json.dumps(item, default=str)) // CHARS_PER_TOKEN
                if token_count + item_tokens > token_limit and chunk:
                    break
                chunk.append(item)
                token_count += item_tokens
                current_idx += 1

            return chunk, current_idx

    async def get_stats(self, search_id: str) -> dict[str, Any]:
        """Get statistics for a hot storage entry."""
        async with self._lock:
            storage = self._storage.get(search_id)
            if storage is None:
                return {"exists": False}
            return {
                "exists": True,
                "total_results": storage.total_results(),
                "estimated_tokens": storage.estimate_tokens(),
                "is_expired": storage.is_expired(),
                "age_seconds": time.time() - storage.created_at,
                "metadata": storage.metadata,
            }

    async def delete(self, search_id: str) -> bool:
        """Delete hot storage entry."""
        async with self._lock:
            if search_id in self._storage:
                del self._storage[search_id]
                return True
            return False

    async def cleanup_expired(self) -> int:
        """Remove expired hot storage entries. Returns count of removed entries."""
        async with self._lock:
            expired = [
                sid for sid, storage in self._storage.items() if storage.is_expired()
            ]
            for sid in expired:
                del self._storage[sid]
            return len(expired)

    async def list_active(self) -> list[str]:
        """List all active (non-expired) search IDs."""
        async with self._lock:
            return [
                sid
                for sid, storage in self._storage.items()
                if not storage.is_expired()
            ]


# Global instance for the application
_hot_storage_manager: HotStorageManager | None = None


def get_hot_storage_manager() -> HotStorageManager:
    """Get or create the global hot storage manager."""
    global _hot_storage_manager
    if _hot_storage_manager is None:
        _hot_storage_manager = HotStorageManager()
    return _hot_storage_manager
