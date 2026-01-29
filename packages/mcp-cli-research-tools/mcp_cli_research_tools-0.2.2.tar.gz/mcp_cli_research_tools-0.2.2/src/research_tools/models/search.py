"""Search-related data models (Google/Serper)."""

from dataclasses import dataclass, field


@dataclass
class OrganicResult:
    """Single organic search result."""

    position: int
    title: str
    link: str
    snippet: str


@dataclass
class PeopleAlsoAsk:
    """People Also Ask item."""

    question: str
    snippet: str
    link: str


@dataclass
class KeywordResult:
    """Keyword autocomplete result."""

    query: str
    suggestions: list[str] = field(default_factory=list)
    from_cache: bool = False

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "query": self.query,
            "suggestions": self.suggestions,
            "cached": self.from_cache,
        }


@dataclass
class SerpResult:
    """SERP analysis result."""

    query: str
    results: list[OrganicResult] = field(default_factory=list)
    people_also_ask: list[PeopleAlsoAsk] = field(default_factory=list)
    related_searches: list[str] = field(default_factory=list)
    from_cache: bool = False

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "query": self.query,
            "cached": self.from_cache,
            "results": [
                {
                    "position": r.position,
                    "title": r.title,
                    "link": r.link,
                    "snippet": r.snippet,
                }
                for r in self.results
            ],
            "people_also_ask": [
                {"question": p.question, "snippet": p.snippet, "link": p.link}
                for p in self.people_also_ask
            ],
            "related_searches": self.related_searches,
        }


@dataclass
class PaaResult:
    """People Also Ask result."""

    query: str
    questions: list[PeopleAlsoAsk] = field(default_factory=list)
    from_cache: bool = False

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "query": self.query,
            "cached": self.from_cache,
            "questions": [
                {"question": p.question, "snippet": p.snippet, "link": p.link}
                for p in self.questions
            ],
        }


@dataclass
class RelatedResult:
    """Related searches result."""

    query: str
    related_searches: list[str] = field(default_factory=list)
    from_cache: bool = False

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "query": self.query,
            "cached": self.from_cache,
            "related_searches": self.related_searches,
        }
