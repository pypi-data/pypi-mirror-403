"""Google AI Mode data models."""

from dataclasses import dataclass, field


@dataclass
class AiModeReference:
    """Reference link from AI Mode response."""

    title: str
    link: str
    snippet: str = ""


@dataclass
class AiModeWebResult:
    """Web result from AI Mode response."""

    position: int
    title: str
    link: str
    snippet: str = ""


@dataclass
class AiModeResult:
    """Result from Google AI Mode search."""

    query: str
    markdown: str = ""
    references: list[AiModeReference] = field(default_factory=list)
    web_results: list[AiModeWebResult] = field(default_factory=list)
    from_cache: bool = False

    @property
    def total_references(self) -> int:
        """Total number of references."""
        return len(self.references)

    @property
    def has_ai_response(self) -> bool:
        """Check if AI generated a response."""
        return bool(self.markdown)

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "query": self.query,
            "cached": self.from_cache,
            "has_ai_response": self.has_ai_response,
            "markdown": self.markdown,
            "total_references": self.total_references,
            "references": [
                {
                    "title": ref.title,
                    "link": ref.link,
                    "snippet": ref.snippet,
                }
                for ref in self.references
            ],
            "web_results": [
                {
                    "position": r.position,
                    "title": r.title,
                    "link": r.link,
                    "snippet": r.snippet,
                }
                for r in self.web_results
            ],
        }
