"""Tool definitions - SSOT for all research tools."""

from .google import (
    google_keywords,
    google_serp,
    google_paa,
    google_related,
    GOOGLE_TOOLS,
)

from .devto import (
    devto_trending,
    devto_tags,
    devto_authors,
    DEVTO_TOOLS,
)

from .competitor import (
    searchapi_serp,
    searchapi_ads,
    COMPETITOR_TOOLS,
)

from .reddit import (
    reddit_posts,
    REDDIT_TOOLS,
)

from .youtube import (
    youtube_search,
    youtube_channel,
    youtube_trending,
    YOUTUBE_TOOLS,
)

from .hackernews import (
    hn_top,
    hn_new,
    hn_best,
    hn_ask,
    hn_show,
    hn_search,
    HN_TOOLS,
)

from .trends import (
    trends_interest,
    trends_related,
    trends_topics,
    trends_geo,
    TRENDS_TOOLS,
)

from .news import (
    news_search,
    NEWS_TOOLS,
)

from .transparency import (
    ads_transparency,
    TRANSPARENCY_TOOLS,
)

from .ai import (
    ai_mode_search,
    AI_TOOLS,
)

from .rank import (
    rank_track,
    RANK_TOOLS,
)

from .llm import (
    llm_track,
    llm_brand,
    llm_compare,
    LLM_TOOLS,
)


# All tool definitions
ALL_TOOLS = [
    *GOOGLE_TOOLS,
    *DEVTO_TOOLS,
    *COMPETITOR_TOOLS,
    *REDDIT_TOOLS,
    *YOUTUBE_TOOLS,
    *HN_TOOLS,
    *TRENDS_TOOLS,
    *NEWS_TOOLS,
    *TRANSPARENCY_TOOLS,
    *AI_TOOLS,
    *RANK_TOOLS,
    *LLM_TOOLS,
]


# Group configuration for CLI
GROUP_CONFIGS = {
    "google": {"alias": "g", "help": "Google/Serper research commands"},
    "devto": {"alias": "d", "help": "Dev.to research commands"},
    "competitor": {"alias": "c", "help": "Competitor research via SearchAPI.io"},
    "reddit": {"alias": "rd", "help": "Reddit research commands"},
    "youtube": {"alias": "yt", "help": "YouTube research commands"},
    "hn": {"help": "Hacker News research commands"},
    "trends": {"alias": "t", "help": "Google Trends research commands"},
    "news": {"alias": "n", "help": "Google News research commands"},
    "transparency": {"alias": "at", "help": "Google Ads Transparency research"},
    "ai": {"help": "Google AI Mode research"},
    "rank": {"alias": "r", "help": "Google Rank Tracking"},
    "llm": {"alias": "l", "help": "LLM citation tracking"},
}


__all__ = [
    # Google tools
    "google_keywords",
    "google_serp",
    "google_paa",
    "google_related",
    "GOOGLE_TOOLS",
    # DevTo tools
    "devto_trending",
    "devto_tags",
    "devto_authors",
    "DEVTO_TOOLS",
    # Competitor tools
    "searchapi_serp",
    "searchapi_ads",
    "COMPETITOR_TOOLS",
    # Reddit tools
    "reddit_posts",
    "REDDIT_TOOLS",
    # YouTube tools
    "youtube_search",
    "youtube_channel",
    "youtube_trending",
    "YOUTUBE_TOOLS",
    # HN tools
    "hn_top",
    "hn_new",
    "hn_best",
    "hn_ask",
    "hn_show",
    "hn_search",
    "HN_TOOLS",
    # Trends tools
    "trends_interest",
    "trends_related",
    "trends_topics",
    "trends_geo",
    "TRENDS_TOOLS",
    # News tools
    "news_search",
    "NEWS_TOOLS",
    # Transparency tools
    "ads_transparency",
    "TRANSPARENCY_TOOLS",
    # AI tools
    "ai_mode_search",
    "AI_TOOLS",
    # Rank tools
    "rank_track",
    "RANK_TOOLS",
    # LLM tools
    "llm_track",
    "llm_brand",
    "llm_compare",
    "LLM_TOOLS",
    # All tools
    "ALL_TOOLS",
    "GROUP_CONFIGS",
]
