"""OpenAI Responses API client for web search with citations."""

import httpx


class OpenAIError(Exception):
    """OpenAI API error."""

    pass


class OpenAIClient:
    """Client for OpenAI Responses API with web search."""

    BASE_URL = "https://api.openai.com/v1"

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

    async def __aenter__(self) -> "OpenAIClient":
        return self

    async def __aexit__(self, *args) -> None:
        await self.close()

    async def search(self, query: str) -> dict:
        """
        Perform a web search using OpenAI's Responses API with web_search tool.

        Args:
            query: Search query

        Returns:
            Dict with response text and citations (annotations)
        """
        response = await self._client.post(
            f"{self.BASE_URL}/responses",
            json={
                "model": "gpt-4o",
                "tools": [{"type": "web_search"}],
                "input": query,
            },
        )

        if response.status_code == 401:
            raise OpenAIError("Invalid API key")
        if response.status_code == 429:
            raise OpenAIError("Rate limit exceeded")
        if response.status_code != 200:
            raise OpenAIError(f"API error: {response.status_code} - {response.text}")

        return response.json()
