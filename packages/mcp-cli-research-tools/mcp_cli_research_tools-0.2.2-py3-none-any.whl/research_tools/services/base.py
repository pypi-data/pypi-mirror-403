"""Base service class with common functionality."""

from abc import ABC, abstractmethod

from .cache import CacheService


class BaseService(ABC):
    """Abstract base class for all services."""

    def __init__(self, cache: CacheService) -> None:
        self._cache = cache

    @property
    @abstractmethod
    def cache_prefix(self) -> str:
        """Cache key prefix for this service."""
        pass

    @property
    def default_ttl(self) -> int:
        """Default cache TTL in hours."""
        return 24

    def _cache_key(self, *parts: str) -> str:
        """Build cache key from parts."""
        return f"{self.cache_prefix}:{':'.join(parts)}"
