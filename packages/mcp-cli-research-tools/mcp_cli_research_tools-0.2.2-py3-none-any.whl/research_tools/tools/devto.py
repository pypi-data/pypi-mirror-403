"""DevTo tool definitions."""

from ..registry import (
    ToolDefinition,
    ServiceConfig,
    OutputDefinition,
    TableSection,
    Param,
    ParamType,
    TAGS,
    PERIOD,
    LIMIT,
    NO_CACHE,
    position_column,
    title_column,
    author_column,
    count_column,
    tags_column,
    Column,
    ColumnStyle,
)
from ..services import DevToService
from ..registry.params import _parse_comma_list


# Required tags param (for devto_tags command)
TAGS_REQUIRED = Param(
    name="tags",
    type=ParamType.LIST,
    description="Comma-separated tags to analyze (required)",
    required=True,
    cli_short="-t",
    parser=_parse_comma_list,
)


# =============================================================================
# devto_trending
# =============================================================================

devto_trending = ToolDefinition(
    name="devto_trending",
    description="Get trending posts from dev.to",
    group="devto",
    params=[TAGS, PERIOD, LIMIT, NO_CACHE],
    service=ServiceConfig(
        service_class=DevToService,
        method="get_trending",
        optional_env=["DEVTO_API_KEY"],
        cache_ttl=24 * 3600,
    ),
    output=OutputDefinition(
        title_template="Trending Posts ({period}d)",
        sections=[
            TableSection(
                data_path="articles",
                columns=[
                    position_column(),
                    title_column(max_width=50),
                    author_column(),
                    count_column("Reactions", "reactions", ColumnStyle.GREEN),
                    count_column("Comments", "comments", ColumnStyle.YELLOW),
                    Column(
                        name="Read",
                        key="reading_time",
                        suffix="min",
                        justify="right",
                    ),
                    tags_column(),
                ],
                footer_template="Showing {count} articles",
            ),
        ],
    ),
)


# =============================================================================
# devto_tags
# =============================================================================

devto_tags = ToolDefinition(
    name="devto_tags",
    description="Analyze engagement by tag on dev.to",
    group="devto",
    cli_name="tags",
    params=[
        TAGS_REQUIRED,
        PERIOD,
        LIMIT,
        NO_CACHE,
    ],
    service=ServiceConfig(
        service_class=DevToService,
        method="get_tag_stats",
        optional_env=["DEVTO_API_KEY"],
        cache_ttl=24 * 3600,
    ),
    output=OutputDefinition(
        title_template="Tag Analysis ({period}d, {sample_size} articles sampled)",
        sections=[
            TableSection(
                data_path="tags",
                columns=[
                    Column(
                        name="Tag",
                        key="name",
                        style=ColumnStyle.BOLD,
                    ),
                    count_column("Articles", "article_count", ColumnStyle.DEFAULT),
                    Column(
                        name="Avg Reactions",
                        key="avg_reactions",
                        style=ColumnStyle.GREEN,
                        justify="right",
                        formatter=lambda x: f"{x:.1f}" if isinstance(x, float) else str(x),
                    ),
                    Column(
                        name="Avg Comments",
                        key="avg_comments",
                        style=ColumnStyle.YELLOW,
                        justify="right",
                        formatter=lambda x: f"{x:.1f}" if isinstance(x, float) else str(x),
                    ),
                    Column(
                        name="Avg Read Time",
                        key="avg_reading_time",
                        justify="right",
                        formatter=lambda x: f"{x:.1f}min" if isinstance(x, float) else str(x),
                    ),
                ],
            ),
        ],
    ),
)


# =============================================================================
# devto_authors
# =============================================================================

devto_authors = ToolDefinition(
    name="devto_authors",
    description="Find top authors by engagement on dev.to",
    group="devto",
    cli_name="authors",
    params=[TAGS, PERIOD, LIMIT, NO_CACHE],
    service=ServiceConfig(
        service_class=DevToService,
        method="get_author_stats",
        optional_env=["DEVTO_API_KEY"],
        cache_ttl=24 * 3600,
    ),
    output=OutputDefinition(
        title_template="Top Authors ({period}d, {sample_size} articles sampled)",
        sections=[
            TableSection(
                data_path="authors",
                columns=[
                    position_column(),
                    author_column(key="username"),
                    count_column("Articles", "article_count", ColumnStyle.DEFAULT),
                    count_column("Total Reactions", "total_reactions", ColumnStyle.GREEN),
                    Column(
                        name="Avg Reactions",
                        key="avg_reactions",
                        style=ColumnStyle.GREEN,
                        justify="right",
                        formatter=lambda x: f"{x:.1f}" if isinstance(x, float) else str(x),
                    ),
                    count_column("Total Comments", "total_comments", ColumnStyle.YELLOW),
                ],
            ),
        ],
    ),
)


# All DevTo tools
DEVTO_TOOLS = [
    devto_trending,
    devto_tags,
    devto_authors,
]
