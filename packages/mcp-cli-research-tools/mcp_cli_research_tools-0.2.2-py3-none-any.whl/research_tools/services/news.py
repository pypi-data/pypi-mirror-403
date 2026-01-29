"""Google News service - SSOT for news research."""

from ..clients import SearchAPIClient
from ..models.news import NewsArticle, NewsSearchResult
from .base import BaseService
from .cache import CacheService


class NewsService(BaseService):
    """Service for Google News research via SearchAPI.io."""

    cache_prefix = "news"
    default_ttl = 12  # News changes frequently

    # Map CLI shorthand to API values
    TIME_PERIOD_MAP = {
        "hour": "last_hour",
        "day": "last_day",
        "week": "last_week",
        "month": "last_month",
        "year": "last_year",
    }

    def __init__(self, api_key: str, cache: CacheService) -> None:
        super().__init__(cache)
        self._api_key = api_key

    async def search(
        self,
        query: str,
        time_period: str = "",
        sort_by: str = "",
        gl: str = "us",
        hl: str = "en",
        skip_cache: bool = False,
    ) -> NewsSearchResult:
        """
        Search Google News.

        Args:
            query: Search query (supports operators like site:, inurl:, intitle:)
            time_period: Time filter (hour, day, week, month, year)
            sort_by: Sort order (relevance or most_recent)
            gl: Country code (us, gb, rs, etc.)
            hl: Language code (en, sr, etc.)
            skip_cache: Force fresh fetch

        Returns:
            NewsSearchResult with articles
        """
        cache_key = self._cache_key("search", query, time_period, sort_by, gl)

        cached_data, from_cache = await self._cache.get_or_fetch_async(
            cache_key,
            lambda: self._fetch_news(query, time_period, sort_by, gl, hl),
            self.default_ttl,
            skip_cache,
        )

        return self._parse_result(query, cached_data, from_cache)

    async def _fetch_news(
        self, query: str, time_period: str, sort_by: str, gl: str, hl: str
    ) -> dict:
        """Fetch news from API."""
        async with SearchAPIClient(self._api_key) as client:
            params = {
                "q": query,
                "gl": gl,
                "hl": hl,
            }
            if time_period:
                params["time_period"] = self.TIME_PERIOD_MAP.get(time_period, time_period)
            if sort_by:
                params["sort_by"] = sort_by

            data = await client.raw_search("google_news", **params)

            return {
                "query": query,
                "raw": data,
            }

    def _parse_result(
        self, query: str, data: dict, from_cache: bool
    ) -> NewsSearchResult:
        """Parse cached data into NewsSearchResult."""
        raw = data.get("raw", {})

        articles = [
            NewsArticle(
                position=item.get("position", i + 1),
                title=item.get("title", ""),
                link=item.get("link", ""),
                source=item.get("source", ""),
                date=item.get("date", ""),
                snippet=item.get("snippet", ""),
                thumbnail=item.get("thumbnail"),
            )
            for i, item in enumerate(raw.get("news_results", raw.get("organic_results", [])))
        ]

        return NewsSearchResult(
            query=query,
            articles=articles,
            from_cache=from_cache,
        )
