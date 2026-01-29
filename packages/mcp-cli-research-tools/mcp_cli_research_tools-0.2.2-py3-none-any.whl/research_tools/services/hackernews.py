"""Hacker News service - SSOT for HN research."""

from datetime import datetime

from ..clients import HNClient
from ..models import HNStory, HNStoriesResult, HNSearchResult
from .base import BaseService
from .cache import CacheService


class HNService(BaseService):
    """Service for Hacker News research."""

    cache_prefix = "hn"
    default_ttl = 12  # HN updates frequently

    def __init__(self, cache: CacheService) -> None:
        super().__init__(cache)

    def _parse_story(self, item: dict, story_type: str = "story") -> HNStory:
        """Parse Firebase item to HNStory."""
        return HNStory(
            id=item.get("id", 0),
            title=item.get("title", ""),
            url=item.get("url"),
            author=item.get("by", ""),
            score=item.get("score", 0),
            comments=item.get("descendants", 0),
            created_at=datetime.fromtimestamp(item.get("time", 0)),
            story_type=story_type,
        )

    def _parse_algolia_hit(self, hit: dict) -> HNStory:
        """Parse Algolia hit to HNStory."""
        # Determine story type from tags
        tags = hit.get("_tags", [])
        story_type = "story"
        if "ask_hn" in tags:
            story_type = "ask"
        elif "show_hn" in tags:
            story_type = "show"
        elif "job" in tags:
            story_type = "job"

        return HNStory(
            id=int(hit.get("objectID", 0)),
            title=hit.get("title", "") or hit.get("story_title", ""),
            url=hit.get("url"),
            author=hit.get("author", ""),
            score=hit.get("points", 0) or 0,
            comments=hit.get("num_comments", 0) or 0,
            created_at=datetime.fromtimestamp(hit.get("created_at_i", 0)),
            story_type=story_type,
        )

    async def _fetch_stories(self, story_type: str, limit: int) -> dict:
        """Fetch stories from Firebase API."""
        async with HNClient() as client:
            # Get story IDs based on type
            if story_type == "top":
                ids = await client.get_top_stories(limit)
            elif story_type == "new":
                ids = await client.get_new_stories(limit)
            elif story_type == "best":
                ids = await client.get_best_stories(limit)
            elif story_type == "ask":
                ids = await client.get_ask_stories(limit)
            elif story_type == "show":
                ids = await client.get_show_stories(limit)
            else:
                ids = await client.get_top_stories(limit)

            # Fetch items in parallel
            items = await client.get_items_batch(ids)

            return {
                "story_type": story_type,
                "stories": [
                    {
                        "id": item.get("id", 0),
                        "title": item.get("title", ""),
                        "url": item.get("url"),
                        "author": item.get("by", ""),
                        "score": item.get("score", 0),
                        "comments": item.get("descendants", 0),
                        "created_at": item.get("time", 0),
                        "story_type": story_type if story_type in ("ask", "show") else "story",
                    }
                    for item in items
                    if item and item.get("title")  # Filter out None and deleted
                ],
            }

    async def _get_stories(
        self,
        story_type: str,
        limit: int = 30,
        skip_cache: bool = False,
    ) -> HNStoriesResult:
        """Generic method to get stories by type."""
        cache_key = self._cache_key(story_type, str(limit))

        cached_data, from_cache = await self._cache.get_or_fetch_async(
            cache_key,
            lambda: self._fetch_stories(story_type, limit),
            self.default_ttl,
            skip_cache,
        )

        stories = [
            HNStory(
                id=s["id"],
                title=s["title"],
                url=s.get("url"),
                author=s["author"],
                score=s["score"],
                comments=s["comments"],
                created_at=datetime.fromtimestamp(s["created_at"]),
                story_type=s["story_type"],
            )
            for s in cached_data["stories"]
        ]

        return HNStoriesResult(
            stories=stories,
            story_type=story_type,
            from_cache=from_cache,
        )

    async def get_top_stories(
        self,
        limit: int = 30,
        skip_cache: bool = False,
    ) -> HNStoriesResult:
        """Get top stories from Hacker News."""
        return await self._get_stories("top", limit, skip_cache)

    async def get_new_stories(
        self,
        limit: int = 30,
        skip_cache: bool = False,
    ) -> HNStoriesResult:
        """Get newest stories from Hacker News."""
        return await self._get_stories("new", limit, skip_cache)

    async def get_best_stories(
        self,
        limit: int = 30,
        skip_cache: bool = False,
    ) -> HNStoriesResult:
        """Get best stories from Hacker News."""
        return await self._get_stories("best", limit, skip_cache)

    async def get_ask_stories(
        self,
        limit: int = 30,
        skip_cache: bool = False,
    ) -> HNStoriesResult:
        """Get Ask HN stories."""
        return await self._get_stories("ask", limit, skip_cache)

    async def get_show_stories(
        self,
        limit: int = 30,
        skip_cache: bool = False,
    ) -> HNStoriesResult:
        """Get Show HN stories."""
        return await self._get_stories("show", limit, skip_cache)

    async def search(
        self,
        query: str,
        limit: int = 30,
        skip_cache: bool = False,
    ) -> HNSearchResult:
        """Search Hacker News via Algolia (sorted by relevance)."""
        cache_key = self._cache_key("search", query, str(limit))

        cached_data, from_cache = await self._cache.get_or_fetch_async(
            cache_key,
            lambda: self._fetch_search(query, limit),
            self.default_ttl,
            skip_cache,
        )

        stories = [
            HNStory(
                id=s["id"],
                title=s["title"],
                url=s.get("url"),
                author=s["author"],
                score=s["score"],
                comments=s["comments"],
                created_at=datetime.fromtimestamp(s["created_at"]),
                story_type=s["story_type"],
            )
            for s in cached_data["stories"]
        ]

        return HNSearchResult(
            query=query,
            stories=stories,
            total_hits=cached_data["total_hits"],
            from_cache=from_cache,
        )

    async def _fetch_search(self, query: str, limit: int) -> dict:
        """Fetch search results from Algolia."""
        async with HNClient() as client:
            data = await client.search(query, limit=limit, tags="story")

            stories = []
            for hit in data.get("hits", []):
                # Determine story type from tags
                tags = hit.get("_tags", [])
                story_type = "story"
                if "ask_hn" in tags:
                    story_type = "ask"
                elif "show_hn" in tags:
                    story_type = "show"

                stories.append({
                    "id": int(hit.get("objectID", 0)),
                    "title": hit.get("title", "") or "",
                    "url": hit.get("url"),
                    "author": hit.get("author", ""),
                    "score": hit.get("points", 0) or 0,
                    "comments": hit.get("num_comments", 0) or 0,
                    "created_at": hit.get("created_at_i", 0),
                    "story_type": story_type,
                })

            return {
                "query": query,
                "stories": stories,
                "total_hits": data.get("nbHits", 0),
            }
