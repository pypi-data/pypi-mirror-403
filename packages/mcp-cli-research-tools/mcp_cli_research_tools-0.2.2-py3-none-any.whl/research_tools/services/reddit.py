"""Reddit service - SSOT for Reddit research."""

import asyncio
from datetime import datetime, timezone

import httpx

from ..models import RedditPost, RedditResult
from .base import BaseService
from .cache import CacheService


class RedditService(BaseService):
    """Service for Reddit subreddit research."""

    cache_prefix = "reddit"
    default_ttl = 12

    USER_AGENT = "blog-tools/1.0 (research)"
    BASE_URL = "https://www.reddit.com"
    HEADERS = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
    }

    def __init__(self, cache: CacheService) -> None:
        super().__init__(cache)

    async def get_posts(
        self,
        subreddits: list[str],
        sort: str = "hot",
        period: str = "week",
        limit: int = 25,
        skip_cache: bool = False,
    ) -> RedditResult:
        """
        Fetch posts from multiple subreddits.

        Args:
            subreddits: List of subreddit names (without r/)
            sort: hot, new, rising, top, controversial
            period: hour, day, week, month, year, all (for top/controversial)
            limit: Max posts per subreddit
            skip_cache: Force fresh fetch

        Returns:
            RedditResult with posts sorted by score
        """
        # Normalize subreddit names
        sub_list = [s.strip().lower() for s in subreddits if s.strip()]
        cache_key = self._cache_key(
            ",".join(sorted(sub_list)), sort, period, str(limit)
        )

        cached_data, from_cache = await self._cache.get_or_fetch_async(
            cache_key,
            lambda: self._fetch_posts(sub_list, sort, period, limit),
            self.default_ttl,
            skip_cache,
        )

        return RedditResult(
            posts=[self._dict_to_post(p) for p in cached_data["posts"]],
            subreddits=cached_data["subreddits"],
            sort=cached_data["sort"],
            period=cached_data["period"],
            from_cache=from_cache,
        )

    async def _fetch_posts(
        self, subreddits: list[str], sort: str, period: str, limit: int
    ) -> dict:
        """Fetch posts from Reddit API."""
        posts: list[dict] = []

        async with httpx.AsyncClient(timeout=30.0) as client:
            for subreddit in subreddits:
                sub_posts = await self._fetch_subreddit(
                    client, subreddit, sort, period, limit
                )
                posts.extend(sub_posts)
                if len(subreddits) > 1:
                    await asyncio.sleep(0.2)

        # Sort by score (highest first)
        posts.sort(key=lambda p: p["score"], reverse=True)

        return {
            "subreddits": subreddits,
            "sort": sort,
            "period": period,
            "posts": posts,
        }

    async def _fetch_subreddit(
        self,
        client: httpx.AsyncClient,
        subreddit: str,
        sort: str,
        period: str,
        limit: int,
    ) -> list[dict]:
        """Fetch posts from a single subreddit."""
        url = f"{self.BASE_URL}/r/{subreddit}/{sort}.json"
        params: dict = {"limit": min(limit, 100)}

        if sort in ("top", "controversial"):
            params["t"] = period

        try:
            response = await client.get(
                url,
                params=params,
                headers=self.HEADERS,
                follow_redirects=True,
            )
            response.raise_for_status()
            data = response.json()

            children = data.get("data", {}).get("children", [])
            return [self._parse_post(child) for child in children]
        except (httpx.HTTPStatusError, Exception):
            return []

    def _parse_post(self, data: dict) -> dict:
        """Parse Reddit API response into dict for caching."""
        post = data.get("data", {})
        created_utc = datetime.fromtimestamp(
            post.get("created_utc", 0), tz=timezone.utc
        )

        return {
            "id": post.get("id", ""),
            "title": post.get("title", ""),
            "url": post.get("url", ""),
            "permalink": f"https://reddit.com{post.get('permalink', '')}",
            "author": post.get("author", "[deleted]"),
            "subreddit": post.get("subreddit", ""),
            "score": post.get("score", 0),
            "upvote_ratio": post.get("upvote_ratio", 0),
            "comments": post.get("num_comments", 0),
            "created_at": created_utc.isoformat(),
            "flair": post.get("link_flair_text"),
        }

    def _dict_to_post(self, data: dict) -> RedditPost:
        """Convert cached dict to RedditPost."""
        return RedditPost(
            id=data["id"],
            title=data["title"],
            url=data["url"],
            permalink=data["permalink"],
            author=data["author"],
            subreddit=data["subreddit"],
            score=data["score"],
            upvote_ratio=data["upvote_ratio"],
            comments=data["comments"],
            created_at=datetime.fromisoformat(data["created_at"]),
            flair=data.get("flair"),
        )
