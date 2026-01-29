"""Google News data models."""

from dataclasses import dataclass, field


@dataclass
class NewsArticle:
    """Single news article from Google News."""

    position: int
    title: str
    link: str
    source: str
    date: str
    snippet: str = ""
    thumbnail: str | None = None


@dataclass
class NewsSearchResult:
    """Google News search result."""

    query: str
    articles: list[NewsArticle] = field(default_factory=list)
    from_cache: bool = False

    @property
    def total_articles(self) -> int:
        return len(self.articles)

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "query": self.query,
            "cached": self.from_cache,
            "total_articles": self.total_articles,
            "articles": [
                {
                    "position": a.position,
                    "title": a.title,
                    "link": a.link,
                    "source": a.source,
                    "date": a.date,
                    "snippet": a.snippet,
                    "thumbnail": a.thumbnail,
                }
                for a in self.articles
            ],
        }
