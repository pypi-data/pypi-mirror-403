"""LLM citation tracking data models."""

from dataclasses import dataclass, field
from enum import Enum
from urllib.parse import urlparse


class LlmEngine(Enum):
    """Supported LLM engines for citation tracking."""

    PERPLEXITY = "perplexity"
    CHATGPT = "chatgpt"
    GOOGLE_AI = "google_ai"


@dataclass
class LlmCitation:
    """A citation/reference from an LLM response."""

    title: str
    url: str
    domain: str
    snippet: str = ""
    position: int = 0

    @classmethod
    def from_url(cls, url: str, title: str = "", snippet: str = "", position: int = 0) -> "LlmCitation":
        """Create citation from URL, extracting domain automatically."""
        domain = cls._extract_domain(url)
        return cls(title=title, url=url, domain=domain, snippet=snippet, position=position)

    @staticmethod
    def _extract_domain(url: str) -> str:
        """Extract domain from URL."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            # Remove www. prefix
            if domain.startswith("www."):
                domain = domain[4:]
            return domain
        except Exception:
            return ""


@dataclass
class LlmEngineResult:
    """Result from a single LLM engine."""

    engine: LlmEngine
    query: str
    citations: list[LlmCitation] = field(default_factory=list)
    response_text: str = ""
    error: str = ""

    @property
    def total_citations(self) -> int:
        """Total number of citations."""
        return len(self.citations)

    @property
    def has_response(self) -> bool:
        """Check if engine returned a valid response."""
        return bool(self.response_text or self.citations) and not self.error

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "engine": self.engine.value,
            "query": self.query,
            "total_citations": self.total_citations,
            "has_response": self.has_response,
            "response_text": self.response_text[:500] if self.response_text else "",
            "error": self.error,
            "citations": [
                {
                    "position": c.position,
                    "title": c.title,
                    "url": c.url,
                    "domain": c.domain,
                    "snippet": c.snippet,
                }
                for c in self.citations
            ],
        }


@dataclass
class LlmTrackingResult:
    """Result from tracking citations across LLM engines."""

    query: str
    engines: list[LlmEngineResult] = field(default_factory=list)
    from_cache: bool = False

    @property
    def all_citations(self) -> list[LlmCitation]:
        """Get all citations across all engines."""
        citations = []
        for engine_result in self.engines:
            citations.extend(engine_result.citations)
        return citations

    @property
    def domain_frequency(self) -> dict[str, int]:
        """Count how often each domain appears across all engines."""
        freq: dict[str, int] = {}
        for citation in self.all_citations:
            if citation.domain:
                freq[citation.domain] = freq.get(citation.domain, 0) + 1
        return dict(sorted(freq.items(), key=lambda x: x[1], reverse=True))

    @property
    def total_citations(self) -> int:
        """Total citations across all engines."""
        return sum(e.total_citations for e in self.engines)

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "query": self.query,
            "cached": self.from_cache,
            "total_citations": self.total_citations,
            "domain_frequency": self.domain_frequency,
            "engines": [e.to_dict() for e in self.engines],
            "all_citations": [
                {
                    "position": c.position,
                    "domain": c.domain,
                    "title": c.title,
                    "url": c.url,
                }
                for c in self.all_citations
            ],
        }


@dataclass
class BrandVisibilityEntry:
    """Visibility data for a single keyword."""

    keyword: str
    result: LlmTrackingResult
    domain_cited: bool = False
    citation_count: int = 0
    engines_cited: list[str] = field(default_factory=list)


@dataclass
class BrandVisibilityResult:
    """Result from brand visibility monitoring."""

    domain: str
    keywords: list[str]
    results: list[BrandVisibilityEntry] = field(default_factory=list)
    from_cache: bool = False

    @property
    def total_citations(self) -> int:
        """Total times domain was cited across all keywords."""
        return sum(e.citation_count for e in self.results)

    @property
    def visibility_score(self) -> float:
        """Percentage of keywords where domain was cited."""
        if not self.results:
            return 0.0
        cited_count = sum(1 for e in self.results if e.domain_cited)
        return (cited_count / len(self.results)) * 100

    @property
    def visibility_by_engine(self) -> dict[str, dict]:
        """Breakdown of visibility by engine."""
        engine_stats: dict[str, dict] = {}
        for entry in self.results:
            for engine_name in entry.engines_cited:
                if engine_name not in engine_stats:
                    engine_stats[engine_name] = {"keywords_cited": 0, "total_citations": 0}
                engine_stats[engine_name]["keywords_cited"] += 1
                # Count citations for this engine
                for er in entry.result.engines:
                    if er.engine.value == engine_name:
                        for c in er.citations:
                            if c.domain == self.domain:
                                engine_stats[engine_name]["total_citations"] += 1
        return engine_stats

    @property
    def visibility_by_keyword(self) -> dict[str, dict]:
        """Breakdown of visibility by keyword."""
        return {
            e.keyword: {
                "cited": e.domain_cited,
                "citation_count": e.citation_count,
                "engines": e.engines_cited,
            }
            for e in self.results
        }

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "domain": self.domain,
            "keywords": self.keywords,
            "cached": self.from_cache,
            "total_citations": self.total_citations,
            "visibility_score": round(self.visibility_score, 1),
            "visibility_by_engine": self.visibility_by_engine,
            "visibility_by_keyword": self.visibility_by_keyword,
            "results": [
                {
                    "keyword": e.keyword,
                    "cited": e.domain_cited,
                    "citation_count": e.citation_count,
                    "engines": e.engines_cited,
                }
                for e in self.results
            ],
        }


@dataclass
class ComparisonEntry:
    """Comparison data for a single keyword."""

    keyword: str
    domain_citations: int
    competitor_citations: int
    winner: str  # "domain", "competitor", "tie", "neither"


@dataclass
class LlmCompareResult:
    """Result from comparing domain vs competitor."""

    domain: str
    competitor: str
    keywords: list[str]
    comparisons: list[ComparisonEntry] = field(default_factory=list)
    from_cache: bool = False

    @property
    def domain_wins(self) -> int:
        """Number of keywords where domain has more citations."""
        return sum(1 for c in self.comparisons if c.winner == "domain")

    @property
    def competitor_wins(self) -> int:
        """Number of keywords where competitor has more citations."""
        return sum(1 for c in self.comparisons if c.winner == "competitor")

    @property
    def ties(self) -> int:
        """Number of keywords where both have equal citations."""
        return sum(1 for c in self.comparisons if c.winner == "tie")

    @property
    def neither(self) -> int:
        """Number of keywords where neither was cited."""
        return sum(1 for c in self.comparisons if c.winner == "neither")

    @property
    def domain_total_citations(self) -> int:
        """Total citations for domain across all keywords."""
        return sum(c.domain_citations for c in self.comparisons)

    @property
    def competitor_total_citations(self) -> int:
        """Total citations for competitor across all keywords."""
        return sum(c.competitor_citations for c in self.comparisons)

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "domain": self.domain,
            "competitor": self.competitor,
            "keywords": self.keywords,
            "cached": self.from_cache,
            # Flattened for template access
            "domain_wins": self.domain_wins,
            "competitor_wins": self.competitor_wins,
            "ties": self.ties,
            "neither": self.neither,
            "domain_total_citations": self.domain_total_citations,
            "competitor_total_citations": self.competitor_total_citations,
            # Nested for backwards compatibility
            "summary": {
                "domain_wins": self.domain_wins,
                "competitor_wins": self.competitor_wins,
                "ties": self.ties,
                "neither": self.neither,
                "domain_total_citations": self.domain_total_citations,
                "competitor_total_citations": self.competitor_total_citations,
            },
            "comparisons": [
                {
                    "keyword": c.keyword,
                    "domain_citations": c.domain_citations,
                    "competitor_citations": c.competitor_citations,
                    "winner": c.winner,
                }
                for c in self.comparisons
            ],
        }
