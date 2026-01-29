"""Perplexity API client for AI search with citations."""

import httpx


class PerplexityError(Exception):
    """Perplexity API error."""

    pass


class PerplexityClient:
    """Client for Perplexity AI search API."""

    BASE_URL = "https://api.perplexity.ai"

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        self._client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=60.0,  # Longer timeout for AI responses
        )

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    async def __aenter__(self) -> "PerplexityClient":
        return self

    async def __aexit__(self, *args) -> None:
        await self.close()

    async def search(self, query: str) -> dict:
        """
        Perform a search using Perplexity's sonar model.

        Args:
            query: Search query

        Returns:
            Dict with response text and citations
        """
        response = await self._client.post(
            f"{self.BASE_URL}/chat/completions",
            json={
                "model": "sonar",
                "messages": [
                    {
                        "role": "system",
                        "content": "Be precise and concise. Always cite sources.",
                    },
                    {
                        "role": "user",
                        "content": query,
                    },
                ],
                "return_citations": True,
            },
        )

        if response.status_code == 401:
            raise PerplexityError("Invalid API key")
        if response.status_code == 429:
            raise PerplexityError("Rate limit exceeded")
        if response.status_code != 200:
            raise PerplexityError(f"API error: {response.status_code} - {response.text}")

        return response.json()
