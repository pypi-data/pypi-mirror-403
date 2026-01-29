"""Hacker News API client (Firebase + Algolia)."""

import asyncio

import httpx


class HNClientError(Exception):
    """Hacker News API error."""

    pass


class HNClient:
    """Client for Hacker News API.

    Uses Firebase API for stories and Algolia for search.
    No authentication required.
    """

    FIREBASE_URL = "https://hacker-news.firebaseio.com/v0"
    ALGOLIA_URL = "https://hn.algolia.com/api/v1"

    def __init__(self) -> None:
        self._client = httpx.AsyncClient(timeout=30.0)

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    async def __aenter__(self) -> "HNClient":
        return self

    async def __aexit__(self, *args) -> None:
        await self.close()

    async def _get_story_ids(self, endpoint: str, limit: int = 30) -> list[int]:
        """Get story IDs from Firebase endpoint."""
        response = await self._client.get(f"{self.FIREBASE_URL}/{endpoint}.json")

        if response.status_code != 200:
            raise HNClientError(f"API error: {response.status_code}")

        ids = response.json()
        return ids[:limit] if limit else ids

    async def get_top_stories(self, limit: int = 30) -> list[int]:
        """Get top story IDs."""
        return await self._get_story_ids("topstories", limit)

    async def get_new_stories(self, limit: int = 30) -> list[int]:
        """Get newest story IDs."""
        return await self._get_story_ids("newstories", limit)

    async def get_best_stories(self, limit: int = 30) -> list[int]:
        """Get best story IDs."""
        return await self._get_story_ids("beststories", limit)

    async def get_ask_stories(self, limit: int = 30) -> list[int]:
        """Get Ask HN story IDs."""
        return await self._get_story_ids("askstories", limit)

    async def get_show_stories(self, limit: int = 30) -> list[int]:
        """Get Show HN story IDs."""
        return await self._get_story_ids("showstories", limit)

    async def get_item(self, item_id: int) -> dict | None:
        """Get a single item (story, comment, job, poll)."""
        response = await self._client.get(f"{self.FIREBASE_URL}/item/{item_id}.json")

        if response.status_code != 200:
            raise HNClientError(f"API error: {response.status_code}")

        return response.json()

    async def get_items_batch(self, item_ids: list[int]) -> list[dict]:
        """Get multiple items in parallel."""
        tasks = [self.get_item(item_id) for item_id in item_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        items = []
        for result in results:
            if isinstance(result, dict) and result is not None:
                items.append(result)

        return items

    async def search(
        self,
        query: str,
        limit: int = 30,
        tags: str | None = None,
    ) -> dict:
        """Search HN via Algolia (sorted by relevance).

        Args:
            query: Search query
            limit: Number of results
            tags: Filter by tags (story, comment, ask_hn, show_hn, front_page)

        Returns:
            Algolia search response with hits
        """
        params = {
            "query": query,
            "hitsPerPage": limit,
        }
        if tags:
            params["tags"] = tags

        response = await self._client.get(
            f"{self.ALGOLIA_URL}/search",
            params=params,
        )

        if response.status_code != 200:
            raise HNClientError(f"Algolia API error: {response.status_code}")

        return response.json()

    async def search_by_date(
        self,
        query: str,
        limit: int = 30,
        tags: str | None = None,
    ) -> dict:
        """Search HN via Algolia (sorted by date, newest first).

        Args:
            query: Search query
            limit: Number of results
            tags: Filter by tags (story, comment, ask_hn, show_hn, front_page)

        Returns:
            Algolia search response with hits
        """
        params = {
            "query": query,
            "hitsPerPage": limit,
        }
        if tags:
            params["tags"] = tags

        response = await self._client.get(
            f"{self.ALGOLIA_URL}/search_by_date",
            params=params,
        )

        if response.status_code != 200:
            raise HNClientError(f"Algolia API error: {response.status_code}")

        return response.json()
