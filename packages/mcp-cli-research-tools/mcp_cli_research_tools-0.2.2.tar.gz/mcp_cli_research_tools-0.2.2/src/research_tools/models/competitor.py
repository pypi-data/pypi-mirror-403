"""Competitor research data models (SearchAPI.io)."""

from dataclasses import dataclass, field


@dataclass
class CompetitorOrganicResult:
    """Single organic search result with domain."""

    position: int
    title: str
    link: str
    domain: str
    snippet: str


@dataclass
class AdResult:
    """Single ad result from SERP."""

    position: int
    block_position: str  # "top" or "bottom"
    title: str
    link: str
    domain: str
    snippet: str


@dataclass
class AiOverview:
    """AI Overview from Google SERP."""

    markdown: str
    references: list[dict] = field(default_factory=list)


@dataclass
class CompetitorPeopleAlsoAsk:
    """People Also Ask item."""

    question: str
    snippet: str
    link: str


@dataclass
class CompetitorSerpResult:
    """Full competitor SERP analysis result."""

    query: str
    organic: list[CompetitorOrganicResult] = field(default_factory=list)
    ads: list[AdResult] = field(default_factory=list)
    ai_overview: AiOverview | None = None
    people_also_ask: list[CompetitorPeopleAlsoAsk] = field(default_factory=list)
    related_searches: list[str] = field(default_factory=list)
    from_cache: bool = False

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "query": self.query,
            "cached": self.from_cache,
            "organic": [
                {
                    "position": r.position,
                    "title": r.title,
                    "link": r.link,
                    "domain": r.domain,
                    "snippet": r.snippet,
                }
                for r in self.organic
            ],
            "ads": [
                {
                    "position": a.position,
                    "block_position": a.block_position,
                    "title": a.title,
                    "link": a.link,
                    "domain": a.domain,
                    "snippet": a.snippet,
                }
                for a in self.ads
            ],
            "ai_overview": {
                "markdown": self.ai_overview.markdown,
                "references": self.ai_overview.references,
            }
            if self.ai_overview
            else None,
            "people_also_ask": [
                {"question": p.question, "snippet": p.snippet, "link": p.link}
                for p in self.people_also_ask
            ],
            "related_searches": self.related_searches,
        }


@dataclass
class CompetitorAdsResult:
    """Competitor ads analysis result."""

    query: str
    ads: list[AdResult] = field(default_factory=list)
    from_cache: bool = False

    @property
    def total_ads(self) -> int:
        return len(self.ads)

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "query": self.query,
            "total_ads": self.total_ads,
            "cached": self.from_cache,
            "ads": [
                {
                    "position": a.position,
                    "block_position": a.block_position,
                    "title": a.title,
                    "link": a.link,
                    "domain": a.domain,
                    "snippet": a.snippet,
                }
                for a in self.ads
            ],
        }
