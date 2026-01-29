"""Data models for research-tools."""

from .articles import Article, TagStats, AuthorStats, TrendingResult, TagStatsResult, AuthorStatsResult
from .search import (
    OrganicResult,
    PeopleAlsoAsk,
    KeywordResult,
    SerpResult,
    PaaResult,
    RelatedResult,
)
from .social import RedditPost, RedditResult
from .video import VideoResult, YouTubeResult
from .competitor import (
    CompetitorOrganicResult,
    AdResult,
    AiOverview,
    CompetitorPeopleAlsoAsk,
    CompetitorSerpResult,
    CompetitorAdsResult,
)
from .hackernews import HNStory, HNStoriesResult, HNSearchResult

__all__ = [
    # Articles
    "Article",
    "TagStats",
    "AuthorStats",
    "TrendingResult",
    "TagStatsResult",
    "AuthorStatsResult",
    # Search
    "OrganicResult",
    "PeopleAlsoAsk",
    "KeywordResult",
    "SerpResult",
    "PaaResult",
    "RelatedResult",
    # Social
    "RedditPost",
    "RedditResult",
    # Video
    "VideoResult",
    "YouTubeResult",
    # Competitor
    "CompetitorOrganicResult",
    "AdResult",
    "AiOverview",
    "CompetitorPeopleAlsoAsk",
    "CompetitorSerpResult",
    "CompetitorAdsResult",
    # Hacker News
    "HNStory",
    "HNStoriesResult",
    "HNSearchResult",
]
