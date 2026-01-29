"""Serper.dev API client for Google SERP data."""

import httpx

from ..models import OrganicResult, PeopleAlsoAsk, VideoResult


class SerperError(Exception):
    """Serper API error."""

    pass


class SerperClient:
    """Client for Serper.dev Google SERP API."""

    BASE_URL = "https://google.serper.dev"

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        self._client = httpx.AsyncClient(
            headers={
                "X-API-KEY": api_key,
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    async def __aenter__(self) -> "SerperClient":
        return self

    async def __aexit__(self, *args) -> None:
        await self.close()

    async def search(
        self,
        query: str,
        num: int = 10,
        gl: str = "us",
        hl: str = "en",
    ) -> tuple[list[OrganicResult], list[PeopleAlsoAsk], list[str]]:
        """
        Perform a Google web search.

        Args:
            query: Search query
            num: Number of results (max 100)
            gl: Country code (us, gb, rs, etc.)
            hl: Language code (en, sr, etc.)

        Returns:
            Tuple of (organic_results, people_also_ask, related_searches)
        """
        response = await self._client.post(
            f"{self.BASE_URL}/search",
            json={
                "q": query,
                "num": num,
                "gl": gl,
                "hl": hl,
            },
        )

        if response.status_code == 401:
            raise SerperError("Invalid API key")
        if response.status_code == 429:
            raise SerperError("Rate limit exceeded")
        if response.status_code != 200:
            raise SerperError(f"API error: {response.status_code}")

        data = response.json()

        organic = [
            OrganicResult(
                position=item.get("position", i + 1),
                title=item.get("title", ""),
                link=item.get("link", ""),
                snippet=item.get("snippet", ""),
            )
            for i, item in enumerate(data.get("organic", []))
        ]

        paa = [
            PeopleAlsoAsk(
                question=item.get("question", ""),
                snippet=item.get("snippet", ""),
                link=item.get("link", ""),
            )
            for item in data.get("peopleAlsoAsk", [])
        ]

        related = [
            item.get("query", "")
            for item in data.get("relatedSearches", [])
            if item.get("query")
        ]

        return organic, paa, related

    async def autocomplete(self, query: str) -> list[str]:
        """
        Get search suggestions (autocomplete).

        Args:
            query: Partial search query

        Returns:
            List of search suggestions
        """
        response = await self._client.post(
            f"{self.BASE_URL}/autocomplete",
            json={"q": query},
        )

        if response.status_code == 401:
            raise SerperError("Invalid API key")
        if response.status_code == 429:
            raise SerperError("Rate limit exceeded")
        if response.status_code != 200:
            raise SerperError(f"API error: {response.status_code}")

        data = response.json()
        suggestions = data.get("suggestions", [])
        # Handle both string and dict formats
        return [
            s.get("value", s) if isinstance(s, dict) else s for s in suggestions
        ]

    async def videos(
        self,
        query: str,
        num: int = 10,
        gl: str = "us",
        hl: str = "en",
    ) -> list[VideoResult]:
        """
        Search Google Videos (includes YouTube results).

        Args:
            query: Search query
            num: Number of results (max 100)
            gl: Country code (us, gb, rs, etc.)
            hl: Language code (en, sr, etc.)

        Returns:
            List of VideoResult items
        """
        response = await self._client.post(
            f"{self.BASE_URL}/videos",
            json={
                "q": query,
                "num": num,
                "gl": gl,
                "hl": hl,
            },
        )

        if response.status_code == 401:
            raise SerperError("Invalid API key")
        if response.status_code == 429:
            raise SerperError("Rate limit exceeded")
        if response.status_code != 200:
            raise SerperError(f"API error: {response.status_code}")

        data = response.json()

        return [
            VideoResult(
                position=i + 1,
                title=item.get("title", ""),
                link=item.get("link", ""),
                snippet=item.get("snippet", ""),
                channel=item.get("channel", ""),
                duration=item.get("duration", ""),
                views=item.get("views", ""),
                date=item.get("date", ""),
                thumbnail=item.get("imageUrl", ""),
            )
            for i, item in enumerate(data.get("videos", []))
        ]
