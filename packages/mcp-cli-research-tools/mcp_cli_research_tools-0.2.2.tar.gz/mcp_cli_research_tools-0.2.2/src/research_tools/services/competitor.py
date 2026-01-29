"""Competitor research service - SSOT for SearchAPI.io."""

from ..clients import SearchAPIClient
from ..models import (
    CompetitorOrganicResult,
    AdResult,
    AiOverview,
    CompetitorPeopleAlsoAsk,
    CompetitorSerpResult,
    CompetitorAdsResult,
)
from .base import BaseService
from .cache import CacheService


class CompetitorService(BaseService):
    """Service for competitor research via SearchAPI.io."""

    cache_prefix = "searchapi"
    default_ttl = 48

    def __init__(self, api_key: str, cache: CacheService) -> None:
        super().__init__(cache)
        self._api_key = api_key

    async def get_serp(
        self,
        query: str,
        num: int = 10,
        gl: str = "us",
        skip_cache: bool = False,
    ) -> CompetitorSerpResult:
        """
        Get full SERP with AI Overview and competitor ads.

        Args:
            query: Search query
            num: Number of results
            gl: Country code
            skip_cache: Force fresh fetch

        Returns:
            CompetitorSerpResult with organic, ads, AI overview, PAA, and related
        """
        cache_key = self._cache_key("serp", query, str(num), gl)

        cached_data, from_cache = await self._cache.get_or_fetch_async(
            cache_key,
            lambda: self._fetch_serp(query, num, gl),
            self.default_ttl,
            skip_cache,
        )

        return self._parse_serp_result(query, cached_data, from_cache)

    async def _fetch_serp(self, query: str, num: int, gl: str) -> dict:
        """Fetch SERP from API."""
        async with SearchAPIClient(self._api_key) as client:
            organic, ads, ai_overview, paa, related = await client.search(
                query, num=num, gl=gl
            )
            return {
                "query": query,
                "organic": [
                    {
                        "position": r.position,
                        "title": r.title,
                        "link": r.link,
                        "domain": r.domain,
                        "snippet": r.snippet,
                    }
                    for r in organic
                ],
                "ads": [
                    {
                        "position": a.position,
                        "block_position": a.block_position,
                        "title": a.title,
                        "link": a.link,
                        "domain": a.domain,
                        "snippet": a.snippet,
                    }
                    for a in ads
                ],
                "ai_overview": {
                    "markdown": ai_overview.markdown,
                    "references": ai_overview.references,
                }
                if ai_overview
                else None,
                "people_also_ask": [
                    {"question": p.question, "snippet": p.snippet, "link": p.link}
                    for p in paa
                ],
                "related_searches": related,
            }

    def _parse_serp_result(
        self, query: str, data: dict, from_cache: bool
    ) -> CompetitorSerpResult:
        """Parse cached data into CompetitorSerpResult."""
        ai_overview = None
        if data.get("ai_overview"):
            ai_overview = AiOverview(
                markdown=data["ai_overview"]["markdown"],
                references=data["ai_overview"]["references"],
            )

        return CompetitorSerpResult(
            query=query,
            organic=[CompetitorOrganicResult(**r) for r in data.get("organic", [])],
            ads=[AdResult(**a) for a in data.get("ads", [])],
            ai_overview=ai_overview,
            people_also_ask=[
                CompetitorPeopleAlsoAsk(**p) for p in data.get("people_also_ask", [])
            ],
            related_searches=data.get("related_searches", []),
            from_cache=from_cache,
        )

    async def get_ads(
        self,
        query: str,
        gl: str = "us",
        skip_cache: bool = False,
    ) -> CompetitorAdsResult:
        """
        Get competitor ads for a query.

        Args:
            query: Search query
            gl: Country code
            skip_cache: Force fresh fetch

        Returns:
            CompetitorAdsResult with ads list
        """
        cache_key = self._cache_key("ads", query, gl)

        cached_data, from_cache = await self._cache.get_or_fetch_async(
            cache_key,
            lambda: self._fetch_ads(query, gl),
            self.default_ttl,
            skip_cache,
        )

        return CompetitorAdsResult(
            query=query,
            ads=[AdResult(**a) for a in cached_data.get("ads", [])],
            from_cache=from_cache,
        )

    async def _fetch_ads(self, query: str, gl: str) -> dict:
        """Fetch ads from API."""
        async with SearchAPIClient(self._api_key) as client:
            _, ads, _, _, _ = await client.search(query, num=10, gl=gl)
            return {
                "ads": [
                    {
                        "position": a.position,
                        "block_position": a.block_position,
                        "title": a.title,
                        "link": a.link,
                        "domain": a.domain,
                        "snippet": a.snippet,
                    }
                    for a in ads
                ],
            }
