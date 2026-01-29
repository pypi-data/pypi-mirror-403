"""LLM citation tracking service - SSOT for tracking LLM citations."""

import asyncio

from ..clients import PerplexityClient, PerplexityError, SearchAPIClient, OpenAIClient, OpenAIError
from ..models.llm_tracking import (
    LlmCitation,
    LlmEngine,
    LlmEngineResult,
    LlmTrackingResult,
    BrandVisibilityEntry,
    BrandVisibilityResult,
    ComparisonEntry,
    LlmCompareResult,
)
from .base import BaseService
from .cache import CacheService


class LlmTrackingService(BaseService):
    """Service for tracking LLM citations across engines."""

    cache_prefix = "llm_tracking"
    default_ttl = 12  # 12 hours

    def __init__(
        self,
        perplexity_api_key: str | None,
        api_key: str | None,  # SearchAPI.io key (renamed from searchapi_key for factory compatibility)
        openai_api_key: str | None,
        cache: CacheService,
    ) -> None:
        super().__init__(cache)
        self._perplexity_key = perplexity_api_key
        self._searchapi_key = api_key  # internal name unchanged
        self._openai_key = openai_api_key

    @property
    def available_engines(self) -> list[LlmEngine]:
        """Get list of engines with configured API keys."""
        engines = []
        if self._perplexity_key:
            engines.append(LlmEngine.PERPLEXITY)
        if self._searchapi_key:
            engines.append(LlmEngine.GOOGLE_AI)
        if self._openai_key:
            engines.append(LlmEngine.CHATGPT)
        return engines

    async def track(
        self,
        query: str,
        engines: list[LlmEngine] | None = None,
        skip_cache: bool = False,
    ) -> LlmTrackingResult:
        """
        Track citations for a query across LLM engines.

        Args:
            query: Search query
            engines: List of engines to use (default: all available)
            skip_cache: Force fresh fetch

        Returns:
            LlmTrackingResult with citations from each engine
        """
        # Use all available engines if none specified (handles both None and empty list)
        if not engines:
            engines = self.available_engines
        else:
            # Filter to only available engines
            engines = [e for e in engines if e in self.available_engines]

        if not engines:
            return LlmTrackingResult(query=query, engines=[])

        cache_key = self._cache_key("track", query, ",".join(e.value for e in engines))

        cached_data, from_cache = await self._cache.get_or_fetch_async(
            cache_key,
            lambda: self._fetch_all_engines(query, engines),
            self.default_ttl,
            skip_cache,
        )

        return self._parse_tracking_result(query, cached_data, from_cache)

    async def brand(
        self,
        domain: str,
        keywords: list[str],
        engines: list[LlmEngine] | None = None,
        skip_cache: bool = False,
    ) -> BrandVisibilityResult:
        """
        Monitor brand visibility across keywords.

        Args:
            domain: Domain to track (e.g. "prisma.io")
            keywords: List of keywords to check
            engines: List of engines to use (default: all available)
            skip_cache: Force fresh fetch

        Returns:
            BrandVisibilityResult with visibility metrics
        """
        # Normalize domain
        domain = domain.lower()
        if domain.startswith("www."):
            domain = domain[4:]

        results = []
        for keyword in keywords:
            tracking_result = await self.track(keyword, engines=engines, skip_cache=skip_cache)

            # Check if domain appears in citations
            domain_cited = False
            citation_count = 0
            engines_cited = []

            for engine_result in tracking_result.engines:
                for citation in engine_result.citations:
                    if citation.domain == domain:
                        domain_cited = True
                        citation_count += 1
                        if engine_result.engine.value not in engines_cited:
                            engines_cited.append(engine_result.engine.value)

            results.append(
                BrandVisibilityEntry(
                    keyword=keyword,
                    result=tracking_result,
                    domain_cited=domain_cited,
                    citation_count=citation_count,
                    engines_cited=engines_cited,
                )
            )

        return BrandVisibilityResult(
            domain=domain,
            keywords=keywords,
            results=results,
            from_cache=all(r.result.from_cache for r in results),
        )

    async def compare(
        self,
        domain: str,
        competitor: str,
        keywords: list[str],
        engines: list[LlmEngine] | None = None,
        skip_cache: bool = False,
    ) -> LlmCompareResult:
        """
        Compare domain vs competitor across keywords.

        Args:
            domain: Your domain (e.g. "prisma.io")
            competitor: Competitor domain (e.g. "typeorm.io")
            keywords: Keywords to compare on
            engines: List of engines to use (default: all available)
            skip_cache: Force fresh fetch

        Returns:
            LlmCompareResult with head-to-head comparison
        """
        # Normalize domains
        domain = domain.lower()
        competitor = competitor.lower()
        if domain.startswith("www."):
            domain = domain[4:]
        if competitor.startswith("www."):
            competitor = competitor[4:]

        comparisons = []
        for keyword in keywords:
            tracking_result = await self.track(keyword, engines=engines, skip_cache=skip_cache)

            # Count citations for each
            domain_citations = 0
            competitor_citations = 0

            for engine_result in tracking_result.engines:
                for citation in engine_result.citations:
                    if citation.domain == domain:
                        domain_citations += 1
                    elif citation.domain == competitor:
                        competitor_citations += 1

            # Determine winner
            if domain_citations > competitor_citations:
                winner = "domain"
            elif competitor_citations > domain_citations:
                winner = "competitor"
            elif domain_citations > 0:  # Both equal and > 0
                winner = "tie"
            else:
                winner = "neither"

            comparisons.append(
                ComparisonEntry(
                    keyword=keyword,
                    domain_citations=domain_citations,
                    competitor_citations=competitor_citations,
                    winner=winner,
                )
            )

        return LlmCompareResult(
            domain=domain,
            competitor=competitor,
            keywords=keywords,
            comparisons=comparisons,
            from_cache=False,  # Aggregated result
        )

    async def _fetch_all_engines(
        self,
        query: str,
        engines: list[LlmEngine],
    ) -> dict:
        """Fetch data from all specified engines concurrently."""
        tasks = []
        engine_order = []

        for engine in engines:
            if engine == LlmEngine.PERPLEXITY:
                tasks.append(self._fetch_perplexity(query))
                engine_order.append(engine)
            elif engine == LlmEngine.GOOGLE_AI:
                tasks.append(self._fetch_google_ai(query))
                engine_order.append(engine)
            elif engine == LlmEngine.CHATGPT:
                tasks.append(self._fetch_openai(query))
                engine_order.append(engine)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        return {
            "query": query,
            "engines": [
                {
                    "engine": engine.value,
                    "data": result if not isinstance(result, Exception) else None,
                    "error": str(result) if isinstance(result, Exception) else None,
                }
                for engine, result in zip(engine_order, results)
            ],
        }

    async def _fetch_perplexity(self, query: str) -> dict:
        """Fetch data from Perplexity API."""
        if not self._perplexity_key:
            raise PerplexityError("Perplexity API key not configured")

        async with PerplexityClient(self._perplexity_key) as client:
            return await client.search(query)

    async def _fetch_google_ai(self, query: str) -> dict:
        """Fetch data from Google AI Mode via SearchAPI.io."""
        if not self._searchapi_key:
            raise ValueError("SearchAPI.io key not configured")

        async with SearchAPIClient(self._searchapi_key) as client:
            return await client.raw_search("google_ai_mode", q=query)

    async def _fetch_openai(self, query: str) -> dict:
        """Fetch data from OpenAI Responses API with web search."""
        if not self._openai_key:
            raise OpenAIError("OpenAI API key not configured")

        async with OpenAIClient(self._openai_key) as client:
            return await client.search(query)

    def _parse_tracking_result(
        self,
        query: str,
        data: dict,
        from_cache: bool,
    ) -> LlmTrackingResult:
        """Parse cached data into LlmTrackingResult."""
        engine_results = []

        for engine_data in data.get("engines", []):
            engine_name = engine_data.get("engine")
            raw_data = engine_data.get("data")
            error = engine_data.get("error")

            engine = LlmEngine(engine_name)

            if error:
                engine_results.append(
                    LlmEngineResult(engine=engine, query=query, error=error)
                )
                continue

            if not raw_data:
                engine_results.append(
                    LlmEngineResult(engine=engine, query=query, error="No data returned")
                )
                continue

            citations = self._extract_citations(engine, raw_data)
            response_text = self._extract_response_text(engine, raw_data)

            engine_results.append(
                LlmEngineResult(
                    engine=engine,
                    query=query,
                    citations=citations,
                    response_text=response_text,
                )
            )

        return LlmTrackingResult(
            query=query,
            engines=engine_results,
            from_cache=from_cache,
        )

    def _extract_citations(self, engine: LlmEngine, data: dict) -> list[LlmCitation]:
        """Extract citations from raw API response."""
        citations = []

        if engine == LlmEngine.PERPLEXITY:
            # Perplexity returns citations in choices[0].message.citations
            choices = data.get("choices", [])
            if choices:
                message = choices[0].get("message", {})
                citation_urls = message.get("citations", [])
                for i, url in enumerate(citation_urls):
                    citations.append(
                        LlmCitation.from_url(url=url, position=i + 1)
                    )

        elif engine == LlmEngine.GOOGLE_AI:
            # Google AI Mode returns references in ai_response.reference_links
            ai_response = data.get("ai_response", {})
            reference_links = ai_response.get("reference_links", data.get("reference_links", []))
            for i, ref in enumerate(reference_links):
                citations.append(
                    LlmCitation.from_url(
                        url=ref.get("link", ""),
                        title=ref.get("title", ""),
                        snippet=ref.get("snippet", ""),
                        position=i + 1,
                    )
                )

        elif engine == LlmEngine.CHATGPT:
            # OpenAI returns annotations in output[].content[].annotations
            output = data.get("output", [])
            position = 1
            for output_item in output:
                if output_item.get("type") == "message":
                    content = output_item.get("content", [])
                    for content_item in content:
                        if content_item.get("type") == "output_text":
                            annotations = content_item.get("annotations", [])
                            for ann in annotations:
                                if ann.get("type") == "url_citation":
                                    citations.append(
                                        LlmCitation.from_url(
                                            url=ann.get("url", ""),
                                            title=ann.get("title", ""),
                                            position=position,
                                        )
                                    )
                                    position += 1

        return citations

    def _extract_response_text(self, engine: LlmEngine, data: dict) -> str:
        """Extract response text from raw API response."""
        if engine == LlmEngine.PERPLEXITY:
            choices = data.get("choices", [])
            if choices:
                message = choices[0].get("message", {})
                return message.get("content", "")

        elif engine == LlmEngine.GOOGLE_AI:
            ai_response = data.get("ai_response", {})
            return ai_response.get("markdown", "")

        elif engine == LlmEngine.CHATGPT:
            # OpenAI returns text in output[].content[].text
            output = data.get("output", [])
            for output_item in output:
                if output_item.get("type") == "message":
                    content = output_item.get("content", [])
                    for content_item in content:
                        if content_item.get("type") == "output_text":
                            return content_item.get("text", "")

        return ""
