"""Google Rank Tracking data models."""

from dataclasses import dataclass, field


@dataclass
class RankResult:
    """Single ranking result."""

    position: int
    title: str
    link: str
    domain: str
    snippet: str = ""
    sitelinks: list[dict] | None = None


@dataclass
class RankTrackingResult:
    """Result from Google Rank Tracking."""

    query: str
    device: str
    location: str
    gl: str
    results: list[RankResult] = field(default_factory=list)
    from_cache: bool = False

    @property
    def total_results(self) -> int:
        """Total number of results."""
        return len(self.results)

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "query": self.query,
            "device": self.device,
            "location": self.location,
            "gl": self.gl,
            "cached": self.from_cache,
            "total_results": self.total_results,
            "results": [
                {
                    "position": r.position,
                    "title": r.title,
                    "link": r.link,
                    "domain": r.domain,
                    "snippet": r.snippet,
                    "sitelinks": r.sitelinks,
                }
                for r in self.results
            ],
        }
