"""Google AI Mode service - SSOT for AI-powered search."""

from ..clients import SearchAPIClient
from ..models.ai_mode import AiModeReference, AiModeWebResult, AiModeResult
from .base import BaseService
from .cache import CacheService


class AiModeService(BaseService):
    """Service for Google AI Mode via SearchAPI.io."""

    cache_prefix = "ai_mode"
    default_ttl = 12  # Shorter TTL as AI responses can change

    def __init__(self, api_key: str, cache: CacheService) -> None:
        super().__init__(cache)
        self._api_key = api_key

    async def search(
        self,
        query: str,
        location: str = "",
        skip_cache: bool = False,
    ) -> AiModeResult:
        """
        Get AI-generated response from Google AI Mode.

        Args:
            query: Search query
            location: Geographic location for results (e.g. "San Francisco")
            skip_cache: Force fresh fetch

        Returns:
            AiModeResult with AI-generated markdown and references
        """
        cache_key = self._cache_key("search", query, location)

        cached_data, from_cache = await self._cache.get_or_fetch_async(
            cache_key,
            lambda: self._fetch_ai_mode(query, location),
            self.default_ttl,
            skip_cache,
        )

        return self._parse_result(query, cached_data, from_cache)

    async def _fetch_ai_mode(self, query: str, location: str) -> dict:
        """Fetch AI Mode data from SearchAPI.io."""
        async with SearchAPIClient(self._api_key) as client:
            params = {"q": query}

            if location:
                params["location"] = location

            data = await client.raw_search("google_ai_mode", **params)

            return {
                "query": query,
                "location": location,
                "raw": data,
            }

    def _parse_result(self, query: str, data: dict, from_cache: bool) -> AiModeResult:
        """Parse cached data into AiModeResult."""
        raw = data.get("raw", {})

        # Parse AI response - API returns markdown/text_blocks at root level
        markdown = raw.get("markdown", "")

        # If markdown is not directly available, try to build from text_blocks
        if not markdown:
            text_blocks = raw.get("text_blocks", [])
            if text_blocks:
                markdown = self._build_markdown_from_blocks(text_blocks)

        # Parse references - at root level
        references = []
        for ref in raw.get("reference_links", []):
            references.append(
                AiModeReference(
                    title=ref.get("title", ""),
                    link=ref.get("link", ""),
                    snippet=ref.get("snippet", ""),
                )
            )

        # Parse web results
        web_results = []
        for i, result in enumerate(raw.get("web_results", raw.get("organic_results", [])), 1):
            web_results.append(
                AiModeWebResult(
                    position=result.get("position", i),
                    title=result.get("title", ""),
                    link=result.get("link", ""),
                    snippet=result.get("snippet", ""),
                )
            )

        return AiModeResult(
            query=query,
            markdown=markdown,
            references=references,
            web_results=web_results,
            from_cache=from_cache,
        )

    def _build_markdown_from_blocks(self, text_blocks: list) -> str:
        """Build markdown string from text blocks."""
        parts = []
        for block in text_blocks:
            block_type = block.get("type", "paragraph")
            text = block.get("text", "")

            if block_type == "header":
                parts.append(f"## {text}")
            elif block_type == "list":
                items = block.get("items", [])
                for item in items:
                    parts.append(f"- {item}")
            elif block_type == "code":
                language = block.get("language", "")
                parts.append(f"```{language}\n{text}\n```")
            else:
                parts.append(text)

        return "\n\n".join(parts)
