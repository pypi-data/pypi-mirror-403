"""Google Rank Tracking service - SSOT for SEO position monitoring."""

from ..clients import SearchAPIClient
from ..models.rank_tracking import RankResult, RankTrackingResult
from .base import BaseService
from .cache import CacheService


class RankTrackingService(BaseService):
    """Service for Google Rank Tracking via SearchAPI.io."""

    cache_prefix = "rank_tracking"
    default_ttl = 24

    def __init__(self, api_key: str, cache: CacheService) -> None:
        super().__init__(cache)
        self._api_key = api_key

    async def track(
        self,
        query: str,
        device: str = "desktop",
        location: str = "",
        gl: str = "us",
        hl: str = "en",
        num: int = 100,
        skip_cache: bool = False,
    ) -> RankTrackingResult:
        """
        Track keyword rankings in Google (up to 100 results).

        Args:
            query: Search query to track
            device: Device type (desktop, mobile, tablet)
            location: Geographic location (e.g. "New York")
            gl: Country code (default "us")
            hl: Language code (default "en")
            num: Number of results (10-100, default 100)
            skip_cache: Force fresh fetch

        Returns:
            RankTrackingResult with position data
        """
        cache_key = self._cache_key(
            "track", query, device, location, gl, hl, str(num)
        )

        cached_data, from_cache = await self._cache.get_or_fetch_async(
            cache_key,
            lambda: self._fetch_rankings(query, device, location, gl, hl, num),
            self.default_ttl,
            skip_cache,
        )

        return self._parse_result(cached_data, from_cache)

    async def _fetch_rankings(
        self,
        query: str,
        device: str,
        location: str,
        gl: str,
        hl: str,
        num: int,
    ) -> dict:
        """Fetch rankings data from SearchAPI.io."""
        async with SearchAPIClient(self._api_key) as client:
            params = {
                "q": query,
                "device": device,
                "gl": gl,
                "hl": hl,
                "num": min(max(num, 10), 100),  # Clamp between 10-100
            }

            if location:
                params["location"] = location

            data = await client.raw_search("google_rank_tracking", **params)

            return {
                "query": query,
                "device": device,
                "location": location,
                "gl": gl,
                "raw": data,
            }

    def _parse_result(self, data: dict, from_cache: bool) -> RankTrackingResult:
        """Parse cached data into RankTrackingResult."""
        raw = data.get("raw", {})

        results = []
        for result in raw.get("organic_results", []):
            # Extract domain from link
            link = result.get("link", "")
            domain = result.get("domain", "")
            if not domain and link:
                # Try to extract domain from link
                try:
                    from urllib.parse import urlparse
                    domain = urlparse(link).netloc
                except Exception:
                    domain = ""

            results.append(
                RankResult(
                    position=result.get("position", 0),
                    title=result.get("title", ""),
                    link=link,
                    domain=domain,
                    snippet=result.get("snippet", ""),
                    sitelinks=result.get("sitelinks"),
                )
            )

        return RankTrackingResult(
            query=data.get("query", ""),
            device=data.get("device", "desktop"),
            location=data.get("location", ""),
            gl=data.get("gl", "us"),
            results=results,
            from_cache=from_cache,
        )
