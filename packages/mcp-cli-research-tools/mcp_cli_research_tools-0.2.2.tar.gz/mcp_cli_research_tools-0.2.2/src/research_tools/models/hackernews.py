"""Hacker News data models."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class HNStory:
    """Single Hacker News story."""

    id: int
    title: str
    url: str | None
    author: str
    score: int
    comments: int
    created_at: datetime
    story_type: str = "story"  # story, ask, show, job

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "id": self.id,
            "title": self.title,
            "url": self.url,
            "author": self.author,
            "score": self.score,
            "comments": self.comments,
            "created_at": self.created_at.isoformat(),
            "story_type": self.story_type,
        }


@dataclass
class HNStoriesResult:
    """Result containing multiple HN stories."""

    stories: list[HNStory] = field(default_factory=list)
    story_type: str = "top"  # top, new, best, ask, show
    from_cache: bool = False

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "story_type": self.story_type,
            "count": len(self.stories),
            "cached": self.from_cache,
            "stories": [s.to_dict() for s in self.stories],
        }


@dataclass
class HNSearchResult:
    """Hacker News search result."""

    query: str
    stories: list[HNStory] = field(default_factory=list)
    total_hits: int = 0
    from_cache: bool = False

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "query": self.query,
            "total_hits": self.total_hits,
            "count": len(self.stories),
            "cached": self.from_cache,
            "stories": [s.to_dict() for s in self.stories],
        }
