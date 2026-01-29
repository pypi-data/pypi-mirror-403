"""SearchAPI.io client for multi-engine search."""

from typing import Any

import httpx

from ..models import (
    CompetitorOrganicResult,
    AdResult,
    AiOverview,
    CompetitorPeopleAlsoAsk,
)


class SearchAPIError(Exception):
    """SearchAPI.io API error."""

    pass


class SearchAPIClient:
    """Client for SearchAPI.io multi-engine search."""

    BASE_URL = "https://www.searchapi.io/api/v1/search"

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        self._client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {api_key}",
            },
            timeout=120.0,  # Google Trends RELATED_QUERIES needs very long timeout
        )

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    async def __aenter__(self) -> "SearchAPIClient":
        return self

    async def __aexit__(self, *args) -> None:
        await self.close()

    async def raw_search(self, engine: str, **params: Any) -> dict:
        """
        Generic search across any SearchAPI.io engine.

        Args:
            engine: Engine name (google, google_trends, google_news, etc.)
            **params: Engine-specific parameters

        Returns:
            Raw JSON response from API
        """
        response = await self._client.get(
            self.BASE_URL,
            params={"engine": engine, **params},
        )

        if response.status_code == 401:
            raise SearchAPIError("Invalid API key")
        if response.status_code == 429:
            raise SearchAPIError("Rate limit exceeded")
        if response.status_code != 200:
            raise SearchAPIError(f"API error: {response.status_code}")

        return response.json()

    async def search(
        self,
        query: str,
        num: int = 10,
        gl: str = "us",
        hl: str = "en",
    ) -> tuple[
        list[CompetitorOrganicResult],
        list[AdResult],
        AiOverview | None,
        list[CompetitorPeopleAlsoAsk],
        list[str],
    ]:
        """
        Perform a Google search via SearchAPI.io.

        Args:
            query: Search query
            num: Number of results (max 100)
            gl: Country code (us, gb, rs, etc.)
            hl: Language code (en, sr, etc.)

        Returns:
            Tuple of (organic, ads, ai_overview, people_also_ask, related_searches)
        """
        data = await self.raw_search("google", q=query, num=num, gl=gl, hl=hl)

        # Parse organic results
        organic = [
            CompetitorOrganicResult(
                position=item.get("position", i + 1),
                title=item.get("title", ""),
                link=item.get("link", ""),
                domain=item.get("domain", ""),
                snippet=item.get("snippet", ""),
            )
            for i, item in enumerate(data.get("organic_results", []))
        ]

        # Parse ads
        ads = [
            AdResult(
                position=item.get("position", i + 1),
                block_position=item.get("block_position", "top"),
                title=item.get("title", ""),
                link=item.get("link", ""),
                domain=item.get("domain", ""),
                snippet=item.get("snippet", ""),
            )
            for i, item in enumerate(data.get("ads", []))
        ]

        # Parse AI overview
        ai_overview = None
        if ai_data := data.get("ai_overview"):
            ai_overview = AiOverview(
                markdown=ai_data.get("markdown", ""),
                references=[
                    {
                        "title": ref.get("title", ""),
                        "link": ref.get("link", ""),
                        "source": ref.get("source", ""),
                    }
                    for ref in ai_data.get("reference_links", [])
                ],
            )

        # Parse People Also Ask
        paa = [
            CompetitorPeopleAlsoAsk(
                question=item.get("question", ""),
                snippet=item.get("snippet", ""),
                link=item.get("link", ""),
            )
            for item in data.get("related_questions", [])
        ]

        # Parse related searches
        related = [
            item.get("query", "")
            for item in data.get("related_searches", [])
            if item.get("query")
        ]

        return organic, ads, ai_overview, paa, related
