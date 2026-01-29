"""Google News tool definitions."""

from ..registry import (
    ToolDefinition,
    ServiceConfig,
    OutputDefinition,
    TableSection,
    QUERY,
    TIME_PERIOD,
    SORT_BY,
    COUNTRY,
    LANGUAGE,
    NO_CACHE,
    position_column,
    title_column,
    date_column,
    Column,
    ColumnStyle,
)
from ..services import NewsService


# =============================================================================
# news_search
# =============================================================================

news_search = ToolDefinition(
    name="google_news",
    description="Search Google News",
    group="news",
    cli_name="search",
    params=[QUERY, TIME_PERIOD, SORT_BY, COUNTRY, LANGUAGE, NO_CACHE],
    service=ServiceConfig(
        service_class=NewsService,
        method="search",
        required_env=["SEARCH_API_IO_KEY"],
        cache_ttl=12 * 3600,
    ),
    output=OutputDefinition(
        title_template='Google News: "{query}"',
        sections=[
            TableSection(
                data_path="articles",
                columns=[
                    position_column(),
                    title_column(max_width=50),
                    Column(
                        name="Source",
                        key="source",
                        style=ColumnStyle.CYAN,
                        max_width=20,
                    ),
                    date_column(),
                ],
                footer_template="Showing {count} articles",
            ),
        ],
    ),
)


# All News tools
NEWS_TOOLS = [
    news_search,
]
