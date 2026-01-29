"""Article-related data models."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Article:
    """Represents a fetched article."""

    id: int
    title: str
    url: str
    author: str
    reactions: int
    comments: int
    reading_time: int
    tags: list[str]
    published_at: datetime


@dataclass
class TagStats:
    """Aggregated statistics for a tag."""

    name: str
    article_count: int
    total_reactions: int
    total_comments: int
    avg_reactions: float
    avg_comments: float
    avg_reading_time: float


@dataclass
class AuthorStats:
    """Aggregated statistics for an author."""

    username: str
    article_count: int
    total_reactions: int
    total_comments: int
    avg_reactions: float
    articles: list[Article] = field(default_factory=list)


@dataclass
class TrendingResult:
    """Result from trending articles fetch."""

    articles: list[Article]
    period: int
    tags: list[str] | None
    from_cache: bool = False

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "source": "devto",
            "period": self.period,
            "tags": self.tags,
            "count": len(self.articles),
            "cached": self.from_cache,
            "articles": [
                {
                    "id": a.id,
                    "title": a.title,
                    "url": a.url,
                    "author": a.author,
                    "reactions": a.reactions,
                    "comments": a.comments,
                    "reading_time": a.reading_time,
                    "tags": a.tags,
                    "published_at": a.published_at.isoformat(),
                }
                for a in self.articles
            ],
        }


@dataclass
class TagStatsResult:
    """Result from tag stats aggregation."""

    stats: list[TagStats]
    sample_size: int
    period: int
    from_cache: bool = False

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "source": "devto",
            "period": self.period,
            "sample_size": self.sample_size,
            "cached": self.from_cache,
            "tags": [
                {
                    "name": t.name,
                    "article_count": t.article_count,
                    "total_reactions": t.total_reactions,
                    "total_comments": t.total_comments,
                    "avg_reactions": round(t.avg_reactions, 1),
                    "avg_comments": round(t.avg_comments, 1),
                    "avg_reading_time": round(t.avg_reading_time, 1),
                }
                for t in self.stats
            ],
        }


@dataclass
class AuthorStatsResult:
    """Result from author stats aggregation."""

    stats: list[AuthorStats]
    sample_size: int
    period: int
    tags: list[str] | None
    from_cache: bool = False

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "source": "devto",
            "period": self.period,
            "tags": self.tags,
            "sample_size": self.sample_size,
            "cached": self.from_cache,
            "authors": [
                {
                    "username": a.username,
                    "article_count": a.article_count,
                    "total_reactions": a.total_reactions,
                    "total_comments": a.total_comments,
                    "avg_reactions": round(a.avg_reactions, 1),
                }
                for a in self.stats
            ],
        }
