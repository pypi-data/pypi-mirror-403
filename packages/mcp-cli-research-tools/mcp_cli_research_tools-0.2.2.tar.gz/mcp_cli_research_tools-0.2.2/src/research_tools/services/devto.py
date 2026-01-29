"""DevTo service - SSOT for dev.to research."""

import asyncio
from collections import defaultdict
from datetime import datetime

import httpx

from ..models import Article, TagStats, AuthorStats, TrendingResult, TagStatsResult, AuthorStatsResult
from .base import BaseService
from .cache import CacheService


class DevToService(BaseService):
    """Service for dev.to research."""

    cache_prefix = "devto"
    default_ttl = 24

    API_BASE = "https://dev.to/api"
    MAX_PER_PAGE = 100

    def __init__(self, api_key: str, cache: CacheService) -> None:
        super().__init__(cache)
        self._api_key = api_key

    async def get_trending(
        self,
        tags: list[str] | None = None,
        period: int = 7,
        limit: int = 20,
        skip_cache: bool = False,
    ) -> TrendingResult:
        """
        Get trending articles from dev.to.

        Args:
            tags: Filter by tags (None = no filter)
            period: Trending period in days
            limit: Maximum articles to fetch
            skip_cache: Force fresh fetch

        Returns:
            TrendingResult with articles
        """
        tag_key = ",".join(sorted(tags)) if tags else "all"
        cache_key = self._cache_key("trending", tag_key, str(period), str(limit))

        cached_data, from_cache = await self._cache.get_or_fetch_async(
            cache_key,
            lambda: self._fetch_trending(tags, period, limit),
            self.default_ttl,
            skip_cache,
        )

        return TrendingResult(
            articles=[self._dict_to_article(a) for a in cached_data["articles"]],
            period=cached_data["period"],
            tags=cached_data.get("tags"),
            from_cache=from_cache,
        )

    async def _fetch_trending(
        self, tags: list[str] | None, period: int, limit: int
    ) -> dict:
        """Fetch trending articles from API."""
        articles = await self._fetch_articles(tags, period, limit)
        return {
            "period": period,
            "tags": tags,
            "articles": [self._article_to_dict(a) for a in articles],
        }

    async def get_tag_stats(
        self,
        tags: list[str],
        period: int = 7,
        limit: int = 10,
        skip_cache: bool = False,
    ) -> TagStatsResult:
        """
        Analyze engagement by tag.

        Args:
            tags: Tags to analyze
            period: Time period in days
            limit: Max tags to return
            skip_cache: Force fresh fetch

        Returns:
            TagStatsResult with tag statistics
        """
        tag_key = ",".join(sorted(tags))
        cache_key = self._cache_key("tags", tag_key, str(period), str(limit))

        cached_data, from_cache = await self._cache.get_or_fetch_async(
            cache_key,
            lambda: self._fetch_tag_stats(tags, period, limit),
            self.default_ttl,
            skip_cache,
        )

        return TagStatsResult(
            stats=[TagStats(**t) for t in cached_data["stats"]],
            sample_size=cached_data["sample_size"],
            period=cached_data["period"],
            from_cache=from_cache,
        )

    async def _fetch_tag_stats(
        self, tags: list[str], period: int, limit: int
    ) -> dict:
        """Fetch and aggregate tag stats from API."""
        sample_size = max(100, limit * 10)
        articles = await self._fetch_articles(tags, period, sample_size)

        # Aggregate by tag - SSOT for tag aggregation logic
        tag_data: dict[str, list[Article]] = defaultdict(list)
        for article in articles:
            for tag in article.tags:
                if tag in tags:
                    tag_data[tag].append(article)

        # Calculate stats
        stats: list[dict] = []
        for tag_name in tags:
            tag_articles = tag_data.get(tag_name, [])
            if not tag_articles:
                continue

            count = len(tag_articles)
            total_reactions = sum(a.reactions for a in tag_articles)
            total_comments = sum(a.comments for a in tag_articles)
            total_reading = sum(a.reading_time for a in tag_articles)

            stats.append({
                "name": tag_name,
                "article_count": count,
                "total_reactions": total_reactions,
                "total_comments": total_comments,
                "avg_reactions": total_reactions / count,
                "avg_comments": total_comments / count,
                "avg_reading_time": total_reading / count,
            })

        stats.sort(key=lambda t: t["avg_reactions"], reverse=True)
        stats = stats[:limit]

        return {
            "period": period,
            "sample_size": len(articles),
            "stats": stats,
        }

    async def get_author_stats(
        self,
        tags: list[str] | None = None,
        period: int = 7,
        limit: int = 10,
        skip_cache: bool = False,
    ) -> AuthorStatsResult:
        """
        Find top authors by engagement.

        Args:
            tags: Filter by tags (optional)
            period: Time period in days
            limit: Max authors to return
            skip_cache: Force fresh fetch

        Returns:
            AuthorStatsResult with author statistics
        """
        tag_key = ",".join(sorted(tags)) if tags else "all"
        cache_key = self._cache_key("authors", tag_key, str(period), str(limit))

        cached_data, from_cache = await self._cache.get_or_fetch_async(
            cache_key,
            lambda: self._fetch_author_stats(tags, period, limit),
            self.default_ttl,
            skip_cache,
        )

        return AuthorStatsResult(
            stats=[
                AuthorStats(
                    username=a["username"],
                    article_count=a["article_count"],
                    total_reactions=a["total_reactions"],
                    total_comments=a["total_comments"],
                    avg_reactions=a["avg_reactions"],
                )
                for a in cached_data["stats"]
            ],
            sample_size=cached_data["sample_size"],
            period=cached_data["period"],
            tags=cached_data.get("tags"),
            from_cache=from_cache,
        )

    async def _fetch_author_stats(
        self, tags: list[str] | None, period: int, limit: int
    ) -> dict:
        """Fetch and aggregate author stats from API."""
        sample_size = max(100, limit * 10)
        articles = await self._fetch_articles(tags, period, sample_size)

        # Aggregate by author - SSOT for author aggregation logic
        author_data: dict[str, list[Article]] = defaultdict(list)
        for article in articles:
            author_data[article.author].append(article)

        # Calculate stats
        stats: list[dict] = []
        for username, user_articles in author_data.items():
            count = len(user_articles)
            total_reactions = sum(a.reactions for a in user_articles)
            total_comments = sum(a.comments for a in user_articles)

            stats.append({
                "username": username,
                "article_count": count,
                "total_reactions": total_reactions,
                "total_comments": total_comments,
                "avg_reactions": total_reactions / count,
            })

        stats.sort(key=lambda a: a["total_reactions"], reverse=True)
        stats = stats[:limit]

        return {
            "period": period,
            "tags": tags,
            "sample_size": len(articles),
            "stats": stats,
        }

    async def _fetch_articles(
        self,
        tags: list[str] | None,
        period: int,
        limit: int,
    ) -> list[Article]:
        """Fetch articles from dev.to API."""
        seen_ids: set[int] = set()
        articles: list[Article] = []

        async with httpx.AsyncClient(timeout=30.0) as client:
            if tags:
                for tag in tags:
                    tag_articles = await self._fetch_for_tag(client, tag, period, limit)
                    for article in tag_articles:
                        if article.id not in seen_ids:
                            seen_ids.add(article.id)
                            articles.append(article)
                            if len(articles) >= limit:
                                break
                    if len(articles) >= limit:
                        break
                    await asyncio.sleep(0.1)
            else:
                articles = await self._fetch_for_tag(client, None, period, limit)

        articles.sort(key=lambda a: a.reactions, reverse=True)
        return articles[:limit]

    async def _fetch_for_tag(
        self,
        client: httpx.AsyncClient,
        tag: str | None,
        period: int,
        limit: int,
    ) -> list[Article]:
        """Fetch articles for a specific tag with pagination."""
        articles: list[Article] = []
        page = 1
        per_page = min(limit, self.MAX_PER_PAGE)

        while len(articles) < limit:
            try:
                data = await self._fetch_page(client, tag, period, page, per_page)
            except httpx.HTTPStatusError:
                break

            if not data:
                break

            for item in data:
                articles.append(self._parse_article(item))
                if len(articles) >= limit:
                    break

            if len(data) < per_page:
                break

            page += 1
            await asyncio.sleep(0.1)

        return articles

    async def _fetch_page(
        self,
        client: httpx.AsyncClient,
        tag: str | None,
        period: int,
        page: int,
        per_page: int,
    ) -> list[dict]:
        """Fetch a single page of articles."""
        params: dict = {
            "top": period,
            "page": page,
            "per_page": per_page,
        }
        if tag:
            params["tag"] = tag

        headers = {}
        if self._api_key:
            headers["api-key"] = self._api_key

        response = await client.get(
            f"{self.API_BASE}/articles",
            params=params,
            headers=headers,
        )
        response.raise_for_status()
        return response.json()

    def _parse_article(self, data: dict) -> Article:
        """Parse API response into Article object."""
        published = data.get("published_at") or data.get("published_timestamp")
        if isinstance(published, str):
            published = published.replace("Z", "+00:00")
            published_dt = datetime.fromisoformat(published)
        else:
            published_dt = datetime.now()

        tags = data.get("tag_list", [])
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(",") if t.strip()]

        return Article(
            id=data.get("id", 0),
            title=data.get("title", ""),
            url=data.get("url", ""),
            author=data.get("user", {}).get("username", "unknown"),
            reactions=data.get("public_reactions_count", 0),
            comments=data.get("comments_count", 0),
            reading_time=data.get("reading_time_minutes", 0),
            tags=tags,
            published_at=published_dt,
        )

    def _article_to_dict(self, article: Article) -> dict:
        """Convert Article to dict for caching."""
        return {
            "id": article.id,
            "title": article.title,
            "url": article.url,
            "author": article.author,
            "reactions": article.reactions,
            "comments": article.comments,
            "reading_time": article.reading_time,
            "tags": article.tags,
            "published_at": article.published_at.isoformat(),
        }

    def _dict_to_article(self, data: dict) -> Article:
        """Convert cached dict to Article."""
        return Article(
            id=data["id"],
            title=data["title"],
            url=data["url"],
            author=data["author"],
            reactions=data["reactions"],
            comments=data["comments"],
            reading_time=data["reading_time"],
            tags=data["tags"],
            published_at=datetime.fromisoformat(data["published_at"]),
        )
