"""Google/Serper service - SSOT for Google search research."""

from ..clients import SerperClient
from ..models import (
    OrganicResult,
    PeopleAlsoAsk,
    KeywordResult,
    SerpResult,
    PaaResult,
    RelatedResult,
)
from .base import BaseService
from .cache import CacheService


class GoogleService(BaseService):
    """Service for Google search research via Serper API."""

    cache_prefix = "serper"
    default_ttl = 48

    def __init__(self, api_key: str, cache: CacheService) -> None:
        super().__init__(cache)
        self._api_key = api_key

    async def get_keywords(
        self,
        query: str,
        skip_cache: bool = False,
    ) -> KeywordResult:
        """
        Get keyword autocomplete suggestions.

        Args:
            query: Seed keyword
            skip_cache: Force fresh fetch

        Returns:
            KeywordResult with suggestions
        """
        cache_key = self._cache_key("keywords", query)

        cached_data, from_cache = await self._cache.get_or_fetch_async(
            cache_key,
            lambda: self._fetch_keywords(query),
            self.default_ttl,
            skip_cache,
        )

        if from_cache:
            return KeywordResult(
                query=cached_data["query"],
                suggestions=cached_data["suggestions"],
                from_cache=True,
            )

        return KeywordResult(
            query=cached_data["query"],
            suggestions=cached_data["suggestions"],
            from_cache=False,
        )

    async def _fetch_keywords(self, query: str) -> dict:
        """Fetch keywords from API."""
        async with SerperClient(self._api_key) as client:
            suggestions = await client.autocomplete(query)
            return {"query": query, "suggestions": suggestions}

    async def get_serp(
        self,
        query: str,
        num: int = 10,
        gl: str = "us",
        skip_cache: bool = False,
    ) -> SerpResult:
        """
        Get SERP analysis.

        Args:
            query: Search query
            num: Number of results
            gl: Country code
            skip_cache: Force fresh fetch

        Returns:
            SerpResult with organic results, PAA, and related searches
        """
        cache_key = self._cache_key("serp", query, str(num), gl)

        cached_data, from_cache = await self._cache.get_or_fetch_async(
            cache_key,
            lambda: self._fetch_serp(query, num, gl),
            self.default_ttl,
            skip_cache,
        )

        return SerpResult(
            query=cached_data["query"],
            results=[OrganicResult(**r) for r in cached_data["results"]],
            people_also_ask=[PeopleAlsoAsk(**p) for p in cached_data.get("people_also_ask", [])],
            related_searches=cached_data.get("related_searches", []),
            from_cache=from_cache,
        )

    async def _fetch_serp(self, query: str, num: int, gl: str) -> dict:
        """Fetch SERP from API."""
        async with SerperClient(self._api_key) as client:
            organic, paa, related = await client.search(query, num=num, gl=gl)
            return {
                "query": query,
                "results": [
                    {"position": r.position, "title": r.title, "link": r.link, "snippet": r.snippet}
                    for r in organic
                ],
                "people_also_ask": [
                    {"question": p.question, "snippet": p.snippet, "link": p.link}
                    for p in paa
                ],
                "related_searches": related,
            }

    async def get_paa(
        self,
        query: str,
        gl: str = "us",
        skip_cache: bool = False,
    ) -> PaaResult:
        """
        Get People Also Ask questions.

        Args:
            query: Search query
            gl: Country code
            skip_cache: Force fresh fetch

        Returns:
            PaaResult with questions
        """
        cache_key = self._cache_key("paa", query, gl)

        cached_data, from_cache = await self._cache.get_or_fetch_async(
            cache_key,
            lambda: self._fetch_paa(query, gl),
            self.default_ttl,
            skip_cache,
        )

        return PaaResult(
            query=query,
            questions=[PeopleAlsoAsk(**p) for p in cached_data["questions"]],
            from_cache=from_cache,
        )

    async def _fetch_paa(self, query: str, gl: str) -> dict:
        """Fetch PAA from API."""
        async with SerperClient(self._api_key) as client:
            _, paa, _ = await client.search(query, num=10, gl=gl)
            return {
                "questions": [
                    {"question": p.question, "snippet": p.snippet, "link": p.link}
                    for p in paa
                ],
            }

    async def get_related(
        self,
        query: str,
        gl: str = "us",
        skip_cache: bool = False,
    ) -> RelatedResult:
        """
        Get related searches.

        Args:
            query: Search query
            gl: Country code
            skip_cache: Force fresh fetch

        Returns:
            RelatedResult with related search queries
        """
        cache_key = self._cache_key("related", query, gl)

        cached_data, from_cache = await self._cache.get_or_fetch_async(
            cache_key,
            lambda: self._fetch_related(query, gl),
            self.default_ttl,
            skip_cache,
        )

        return RelatedResult(
            query=query,
            related_searches=cached_data["related_searches"],
            from_cache=from_cache,
        )

    async def _fetch_related(self, query: str, gl: str) -> dict:
        """Fetch related searches from API."""
        async with SerperClient(self._api_key) as client:
            _, _, related = await client.search(query, num=10, gl=gl)
            return {"related_searches": related}
