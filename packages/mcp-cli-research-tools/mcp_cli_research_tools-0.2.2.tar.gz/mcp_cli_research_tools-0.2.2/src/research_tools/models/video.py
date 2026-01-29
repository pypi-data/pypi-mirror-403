"""Video data models (YouTube)."""

from dataclasses import dataclass, field


@dataclass
class VideoResult:
    """Single video search result."""

    position: int
    title: str
    link: str
    snippet: str
    channel: str
    duration: str
    views: str
    date: str
    thumbnail: str = ""


@dataclass
class YouTubeResult:
    """YouTube search result."""

    query: str
    videos: list[VideoResult] = field(default_factory=list)
    from_cache: bool = False

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "query": self.query,
            "count": len(self.videos),
            "cached": self.from_cache,
            "videos": [
                {
                    "position": v.position,
                    "title": v.title,
                    "link": v.link,
                    "snippet": v.snippet,
                    "channel": v.channel,
                    "duration": v.duration,
                    "views": v.views,
                    "date": v.date,
                }
                for v in self.videos
            ],
        }
