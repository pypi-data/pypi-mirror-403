"""Hacker News tool definitions."""

from datetime import datetime

from ..registry import (
    ToolDefinition,
    ServiceConfig,
    OutputDefinition,
    TableSection,
    QUERY,
    LIMIT,
    NO_CACHE,
    position_column,
    title_column,
    author_column,
    score_column,
    comments_column,
    Column,
    ColumnStyle,
)
from ..services import HNService


def _time_ago(dt_str: str) -> str:
    """Format ISO datetime string as time ago."""
    if not dt_str:
        return "-"
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()
        diff = now - dt

        seconds = int(diff.total_seconds())
        if seconds < 0:
            return "-"
        if seconds < 60:
            return f"{seconds}s"
        minutes = seconds // 60
        if minutes < 60:
            return f"{minutes}m"
        hours = minutes // 60
        if hours < 24:
            return f"{hours}h"
        days = hours // 24
        if days < 30:
            return f"{days}d"
        months = days // 30
        if months < 12:
            return f"{months}mo"
        years = months // 12
        return f"{years}y"
    except (ValueError, TypeError):
        return "-"


def _story_columns():
    """Common columns for HN story tables."""
    return [
        position_column(),
        title_column(max_width=50),
        score_column(),
        comments_column(),
        author_column(prefix=""),
        Column(
            name="Age",
            key="created_at",
            style=ColumnStyle.DIM,
            width=8,
            formatter=_time_ago,
        ),
    ]


# =============================================================================
# hn_top
# =============================================================================

hn_top = ToolDefinition(
    name="hn_top_stories",
    description="Get top stories from Hacker News",
    group="hn",
    cli_name="top",
    params=[LIMIT, NO_CACHE],
    service=ServiceConfig(
        service_class=HNService,
        method="get_top_stories",
        required_env=[],  # No API key needed
        cache_ttl=12 * 3600,
    ),
    output=OutputDefinition(
        title_template="Hacker News - Top Stories",
        sections=[
            TableSection(
                data_path="stories",
                columns=_story_columns(),
                footer_template="Showing {count} stories",
            ),
        ],
    ),
)


# =============================================================================
# hn_new
# =============================================================================

hn_new = ToolDefinition(
    name="hn_new_stories",
    description="Get newest stories from Hacker News",
    group="hn",
    cli_name="new",
    params=[LIMIT, NO_CACHE],
    service=ServiceConfig(
        service_class=HNService,
        method="get_new_stories",
        required_env=[],
        cache_ttl=12 * 3600,
    ),
    output=OutputDefinition(
        title_template="Hacker News - New Stories",
        sections=[
            TableSection(
                data_path="stories",
                columns=_story_columns(),
                footer_template="Showing {count} stories",
            ),
        ],
    ),
)


# =============================================================================
# hn_best
# =============================================================================

hn_best = ToolDefinition(
    name="hn_best_stories",
    description="Get best stories from Hacker News",
    group="hn",
    cli_name="best",
    params=[LIMIT, NO_CACHE],
    service=ServiceConfig(
        service_class=HNService,
        method="get_best_stories",
        required_env=[],
        cache_ttl=12 * 3600,
    ),
    output=OutputDefinition(
        title_template="Hacker News - Best Stories",
        sections=[
            TableSection(
                data_path="stories",
                columns=_story_columns(),
                footer_template="Showing {count} stories",
            ),
        ],
    ),
)


# =============================================================================
# hn_ask
# =============================================================================

hn_ask = ToolDefinition(
    name="hn_ask_stories",
    description="Get Ask HN stories",
    group="hn",
    cli_name="ask",
    params=[LIMIT, NO_CACHE],
    service=ServiceConfig(
        service_class=HNService,
        method="get_ask_stories",
        required_env=[],
        cache_ttl=12 * 3600,
    ),
    output=OutputDefinition(
        title_template="Hacker News - Ask HN",
        sections=[
            TableSection(
                data_path="stories",
                columns=_story_columns(),
                footer_template="Showing {count} stories",
            ),
        ],
    ),
)


# =============================================================================
# hn_show
# =============================================================================

hn_show = ToolDefinition(
    name="hn_show_stories",
    description="Get Show HN stories",
    group="hn",
    cli_name="show",
    params=[LIMIT, NO_CACHE],
    service=ServiceConfig(
        service_class=HNService,
        method="get_show_stories",
        required_env=[],
        cache_ttl=12 * 3600,
    ),
    output=OutputDefinition(
        title_template="Hacker News - Show HN",
        sections=[
            TableSection(
                data_path="stories",
                columns=_story_columns(),
                footer_template="Showing {count} stories",
            ),
        ],
    ),
)


# =============================================================================
# hn_search
# =============================================================================

hn_search = ToolDefinition(
    name="hn_search",
    description="Search Hacker News via Algolia",
    group="hn",
    cli_name="search",
    params=[QUERY, LIMIT, NO_CACHE],
    service=ServiceConfig(
        service_class=HNService,
        method="search",
        required_env=[],
        cache_ttl=12 * 3600,
    ),
    output=OutputDefinition(
        title_template='HN Search: "{query}" ({total_hits} hits)',
        sections=[
            TableSection(
                data_path="stories",
                columns=_story_columns(),
                footer_template="Showing {count} of {total} results",
            ),
        ],
    ),
)


# All HN tools
HN_TOOLS = [
    hn_top,
    hn_new,
    hn_best,
    hn_ask,
    hn_show,
    hn_search,
]
