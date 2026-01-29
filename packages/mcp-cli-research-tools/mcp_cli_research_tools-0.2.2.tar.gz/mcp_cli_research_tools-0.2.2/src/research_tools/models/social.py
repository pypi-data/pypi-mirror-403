"""Social media data models (Reddit)."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class RedditPost:
    """Reddit post data."""

    id: str
    title: str
    url: str
    permalink: str
    author: str
    subreddit: str
    score: int
    upvote_ratio: float
    comments: int
    created_at: datetime
    flair: str | None = None


@dataclass
class RedditResult:
    """Reddit posts result."""

    posts: list[RedditPost]
    subreddits: list[str]
    sort: str
    period: str
    from_cache: bool = False

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "subreddits": self.subreddits,
            "sort": self.sort,
            "period": self.period,
            "count": len(self.posts),
            "cached": self.from_cache,
            "posts": [
                {
                    "id": p.id,
                    "title": p.title,
                    "url": p.url,
                    "permalink": p.permalink,
                    "author": p.author,
                    "subreddit": p.subreddit,
                    "score": p.score,
                    "upvote_ratio": p.upvote_ratio,
                    "comments": p.comments,
                    "created_at": p.created_at.isoformat(),
                    "flair": p.flair,
                }
                for p in self.posts
            ],
        }
