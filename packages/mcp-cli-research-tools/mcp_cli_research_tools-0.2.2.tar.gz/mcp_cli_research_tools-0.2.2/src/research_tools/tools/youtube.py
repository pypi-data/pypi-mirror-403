"""YouTube tool definitions."""

from ..registry import (
    ToolDefinition,
    ServiceConfig,
    OutputDefinition,
    TableSection,
    Param,
    ParamType,
    QUERY,
    LIMIT,
    NO_CACHE,
    CHANNEL,
    CATEGORY,
    REGION,
    position_column,
    title_column,
    date_column,
    Column,
    ColumnStyle,
)
from ..services import YouTubeService


# =============================================================================
# youtube_search
# =============================================================================

youtube_search = ToolDefinition(
    name="youtube_search",
    description="Search YouTube videos",
    group="youtube",
    cli_name="search",
    params=[QUERY, LIMIT, REGION, NO_CACHE],
    service=ServiceConfig(
        service_class=YouTubeService,
        method="search",
        required_env=["SERPER_API_KEY"],
        cache_ttl=24 * 3600,
    ),
    output=OutputDefinition(
        title_template='YouTube: "{query}"',
        sections=[
            TableSection(
                data_path="videos",
                columns=[
                    position_column(),
                    title_column(max_width=45),
                    Column(
                        name="Channel",
                        key="channel",
                        style=ColumnStyle.CYAN,
                        max_width=18,
                        overflow="ellipsis",
                    ),
                    Column(
                        name="Duration",
                        key="duration",
                        justify="right",
                    ),
                    Column(
                        name="Views",
                        key="views",
                        style=ColumnStyle.GREEN,
                        justify="right",
                    ),
                    date_column(),
                ],
                footer_template="Showing {count} videos",
            ),
        ],
    ),
)


# =============================================================================
# youtube_channel
# =============================================================================

youtube_channel = ToolDefinition(
    name="youtube_channel",
    description="Get videos from a specific YouTube channel",
    group="youtube",
    cli_name="channel",
    params=[CHANNEL, LIMIT, REGION, NO_CACHE],
    service=ServiceConfig(
        service_class=YouTubeService,
        method="channel_videos",
        required_env=["SERPER_API_KEY"],
        cache_ttl=24 * 3600,
    ),
    output=OutputDefinition(
        title_template='Channel: "{query}"',
        sections=[
            TableSection(
                data_path="videos",
                columns=[
                    position_column(),
                    title_column(max_width=50),
                    Column(
                        name="Duration",
                        key="duration",
                        justify="right",
                    ),
                    Column(
                        name="Views",
                        key="views",
                        style=ColumnStyle.GREEN,
                        justify="right",
                    ),
                    date_column(),
                ],
                footer_template="Showing {count} videos",
            ),
        ],
    ),
)


# =============================================================================
# youtube_trending
# =============================================================================

youtube_trending = ToolDefinition(
    name="youtube_trending",
    description="Get trending YouTube videos",
    group="youtube",
    cli_name="trending",
    params=[CATEGORY, REGION, LIMIT, NO_CACHE],
    service=ServiceConfig(
        service_class=YouTubeService,
        method="trending",
        required_env=["SERPER_API_KEY"],
        cache_ttl=24 * 3600,
    ),
    output=OutputDefinition(
        title_template="YouTube Trending",
        sections=[
            TableSection(
                data_path="videos",
                columns=[
                    position_column(),
                    title_column(max_width=45),
                    Column(
                        name="Channel",
                        key="channel",
                        style=ColumnStyle.CYAN,
                        max_width=18,
                        overflow="ellipsis",
                    ),
                    Column(
                        name="Duration",
                        key="duration",
                        justify="right",
                    ),
                    Column(
                        name="Views",
                        key="views",
                        style=ColumnStyle.GREEN,
                        justify="right",
                    ),
                    date_column(),
                ],
                footer_template="Showing {count} videos",
            ),
        ],
    ),
)


# All YouTube tools
YOUTUBE_TOOLS = [
    youtube_search,
    youtube_channel,
    youtube_trending,
]
