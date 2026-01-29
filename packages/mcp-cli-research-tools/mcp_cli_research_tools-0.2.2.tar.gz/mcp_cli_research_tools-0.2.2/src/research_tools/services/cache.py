"""Cache service - centralized caching with get-or-fetch pattern."""

from typing import Any, Callable, TypeVar

from ..db import CacheRepository, get_session, init_db

T = TypeVar("T")


class CacheService:
    """Centralized cache service with get-or-fetch pattern."""

    def __init__(self) -> None:
        init_db()

    def get(self, key: str) -> Any | None:
        """Get cached data if exists and not expired."""
        with get_session() as session:
            repo = CacheRepository(session)
            return repo.get(key)

    def set(self, key: str, data: Any, ttl_hours: int = 24) -> None:
        """Cache data with TTL."""
        with get_session() as session:
            repo = CacheRepository(session)
            repo.set(key, data, ttl_hours=ttl_hours)

    def get_or_fetch(
        self,
        key: str,
        fetch_fn: Callable[[], T],
        ttl_hours: int = 24,
        skip_cache: bool = False,
    ) -> tuple[T, bool]:
        """
        Universal get-or-fetch pattern.

        Args:
            key: Cache key
            fetch_fn: Function to call if cache miss
            ttl_hours: TTL for cached data
            skip_cache: If True, always fetch fresh data

        Returns:
            Tuple of (result, from_cache)
        """
        if not skip_cache:
            cached = self.get(key)
            if cached is not None:
                return cached, True

        result = fetch_fn()
        self.set(key, result, ttl_hours=ttl_hours)
        return result, False

    async def get_or_fetch_async(
        self,
        key: str,
        fetch_fn: Callable[[], Any],
        ttl_hours: int = 24,
        skip_cache: bool = False,
    ) -> tuple[Any, bool]:
        """
        Async version of get-or-fetch pattern.

        Args:
            key: Cache key
            fetch_fn: Async function to call if cache miss
            ttl_hours: TTL for cached data
            skip_cache: If True, always fetch fresh data

        Returns:
            Tuple of (result, from_cache)
        """
        if not skip_cache:
            cached = self.get(key)
            if cached is not None:
                return cached, True

        result = await fetch_fn()
        self.set(key, result, ttl_hours=ttl_hours)
        return result, False

    def invalidate(self, key: str) -> bool:
        """Remove a specific cache entry."""
        with get_session() as session:
            repo = CacheRepository(session)
            return repo.invalidate(key)

    def cleanup(self) -> int:
        """Remove all expired cache entries."""
        with get_session() as session:
            repo = CacheRepository(session)
            return repo.cleanup()

    def clear_all(self) -> int:
        """Clear entire cache."""
        with get_session() as session:
            repo = CacheRepository(session)
            return repo.clear_all()

    def stats(self) -> dict:
        """Get cache statistics."""
        with get_session() as session:
            repo = CacheRepository(session)
            return repo.stats()
