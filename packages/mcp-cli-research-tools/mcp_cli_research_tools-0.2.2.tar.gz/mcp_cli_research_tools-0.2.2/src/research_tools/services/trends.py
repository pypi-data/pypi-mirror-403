"""Google Trends service - SSOT for trends research."""

from ..clients import SearchAPIClient
from ..models.trends import (
    TrendsTimelinePoint,
    TrendsInterestResult,
    TrendsRelatedItem,
    TrendsRelatedResult,
    TrendsGeoItem,
    TrendsGeoResult,
)
from .base import BaseService
from .cache import CacheService


class TrendsService(BaseService):
    """Service for Google Trends research via SearchAPI.io."""

    cache_prefix = "trends"
    default_ttl = 24

    def __init__(self, api_key: str, cache: CacheService) -> None:
        super().__init__(cache)
        self._api_key = api_key

    async def get_interest(
        self,
        query: str,
        geo: str = "",
        time_range: str = "today 12-m",
        skip_cache: bool = False,
    ) -> TrendsInterestResult:
        """
        Get interest over time for a query.

        Args:
            query: Search query (up to 5 queries separated by comma)
            geo: Country code (us, gb, etc.) or empty for worldwide
            time_range: Time range (today 12-m, today 3-m, now 7-d, etc.)
            skip_cache: Force fresh fetch

        Returns:
            TrendsInterestResult with timeline data
        """
        cache_key = self._cache_key("interest", query, geo, time_range)

        cached_data, from_cache = await self._cache.get_or_fetch_async(
            cache_key,
            lambda: self._fetch_trends(query, "TIMESERIES", geo, time_range),
            self.default_ttl,
            skip_cache,
        )

        return self._parse_interest_result(query, cached_data, from_cache)

    async def get_related_queries(
        self,
        query: str,
        geo: str = "",
        time_range: str = "today 12-m",
        skip_cache: bool = False,
    ) -> TrendsRelatedResult:
        """
        Get related queries (top + rising).

        Args:
            query: Search query
            geo: Country code or empty for worldwide
            time_range: Time range
            skip_cache: Force fresh fetch

        Returns:
            TrendsRelatedResult with top and rising queries
        """
        cache_key = self._cache_key("related", query, geo, time_range)

        cached_data, from_cache = await self._cache.get_or_fetch_async(
            cache_key,
            lambda: self._fetch_trends(query, "RELATED_QUERIES", geo, time_range),
            self.default_ttl,
            skip_cache,
        )

        return self._parse_related_result(query, cached_data, from_cache)

    async def get_related_topics(
        self,
        query: str,
        geo: str = "",
        time_range: str = "today 12-m",
        skip_cache: bool = False,
    ) -> TrendsRelatedResult:
        """
        Get related topics (top + rising).

        Args:
            query: Search query
            geo: Country code or empty for worldwide
            time_range: Time range
            skip_cache: Force fresh fetch

        Returns:
            TrendsRelatedResult with top and rising topics
        """
        cache_key = self._cache_key("topics", query, geo, time_range)

        cached_data, from_cache = await self._cache.get_or_fetch_async(
            cache_key,
            lambda: self._fetch_trends(query, "RELATED_TOPICS", geo, time_range),
            self.default_ttl,
            skip_cache,
        )

        return self._parse_related_result(query, cached_data, from_cache)

    async def get_geo_interest(
        self,
        query: str,
        geo: str = "",
        time_range: str = "today 12-m",
        skip_cache: bool = False,
    ) -> TrendsGeoResult:
        """
        Get interest by region.

        Args:
            query: Search query
            geo: Country code for sub-region breakdown or empty for countries
            time_range: Time range
            skip_cache: Force fresh fetch

        Returns:
            TrendsGeoResult with regional data
        """
        cache_key = self._cache_key("geo", query, geo, time_range)

        cached_data, from_cache = await self._cache.get_or_fetch_async(
            cache_key,
            lambda: self._fetch_trends(query, "GEO_MAP", geo, time_range),
            self.default_ttl,
            skip_cache,
        )

        return self._parse_geo_result(query, cached_data, from_cache)

    async def _fetch_trends(
        self, query: str, data_type: str, geo: str, time_range: str
    ) -> dict:
        """Fetch trends data from API."""
        async with SearchAPIClient(self._api_key) as client:
            params = {
                "q": query,
                "data_type": data_type,
                "date": time_range,
            }
            if geo:
                params["geo"] = geo

            data = await client.raw_search("google_trends", **params)

            return {
                "query": query,
                "data_type": data_type,
                "raw": data,
            }

    def _parse_interest_result(
        self, query: str, data: dict, from_cache: bool
    ) -> TrendsInterestResult:
        """Parse cached data into TrendsInterestResult."""
        raw = data.get("raw", {})
        interest_data = raw.get("interest_over_time", {})

        averages = interest_data.get("averages", [])
        timeline = [
            TrendsTimelinePoint(
                date=point.get("date", ""),
                values=point.get("values", []),
            )
            for point in interest_data.get("timeline_data", [])
        ]

        return TrendsInterestResult(
            query=query,
            averages=averages,
            timeline=timeline,
            from_cache=from_cache,
        )

    def _parse_related_result(
        self, query: str, data: dict, from_cache: bool
    ) -> TrendsRelatedResult:
        """Parse cached data into TrendsRelatedResult."""
        raw = data.get("raw", {})
        data_type = data.get("data_type", "")

        # Determine root key based on data type
        if data_type == "RELATED_TOPICS":
            related_data = raw.get("related_topics", {})
        else:
            related_data = raw.get("related_queries", {})

        top = [
            TrendsRelatedItem(
                query=item.get("query", item.get("title", "")),
                value=item.get("extracted_value", item.get("value", 0)),
                link=item.get("link", ""),
            )
            for item in related_data.get("top", [])
        ]

        rising = [
            TrendsRelatedItem(
                query=item.get("query", item.get("title", "")),
                value=item.get("extracted_value", item.get("value", 0)),
                link=item.get("link", ""),
            )
            for item in related_data.get("rising", [])
        ]

        return TrendsRelatedResult(
            query=query,
            top=top,
            rising=rising,
            from_cache=from_cache,
        )

    def _parse_geo_result(
        self, query: str, data: dict, from_cache: bool
    ) -> TrendsGeoResult:
        """Parse cached data into TrendsGeoResult."""
        raw = data.get("raw", {})

        regions = []
        for item in raw.get("interest_by_region", []):
            # Get value from values array if present
            values = item.get("values", [])
            value = values[0].get("extracted_value", 0) if values else 0
            regions.append(
                TrendsGeoItem(
                    location=item.get("name", item.get("location", "")),
                    location_code=item.get("geo", item.get("location_code", "")),
                    value=value,
                )
            )

        return TrendsGeoResult(
            query=query,
            regions=regions,
            from_cache=from_cache,
        )
