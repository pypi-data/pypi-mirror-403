"""Research tools - CLI toolkit for dev.to, Google/Serper, Reddit, YouTube and competitor research."""

from .db import CacheRepository, init_db, create_session, get_engine
from .clients import SerperClient, SerperError, SearchAPIClient, SearchAPIError
from .models import (
    Article,
    TagStats,
    AuthorStats,
    OrganicResult,
    PeopleAlsoAsk,
    VideoResult,
    RedditPost,
)
from .services import (
    CacheService,
    GoogleService,
    CompetitorService,
    RedditService,
    YouTubeService,
    DevToService,
)

__all__ = [
    # Database
    "CacheRepository",
    "init_db",
    "create_session",
    "get_engine",
    # Clients
    "SerperClient",
    "SerperError",
    "SearchAPIClient",
    "SearchAPIError",
    # Models
    "Article",
    "TagStats",
    "AuthorStats",
    "OrganicResult",
    "PeopleAlsoAsk",
    "VideoResult",
    "RedditPost",
    # Services
    "CacheService",
    "GoogleService",
    "CompetitorService",
    "RedditService",
    "YouTubeService",
    "DevToService",
]
