"""Google Trends tool definitions."""

from ..registry import (
    ToolDefinition,
    ServiceConfig,
    OutputDefinition,
    TableSection,
    ListSection,
    KeyValueSection,
    QUERY,
    GEO,
    TIME_RANGE,
    NO_CACHE,
    position_column,
    Column,
    ColumnStyle,
)
from ..services import TrendsService


# =============================================================================
# trends_interest
# =============================================================================

trends_interest = ToolDefinition(
    name="google_trends_interest",
    description="Get Google Trends interest over time",
    group="trends",
    cli_name="interest",
    params=[QUERY, GEO, TIME_RANGE, NO_CACHE],
    service=ServiceConfig(
        service_class=TrendsService,
        method="get_interest",
        required_env=["SEARCH_API_IO_KEY"],
        cache_ttl=24 * 3600,
    ),
    output=OutputDefinition(
        title_template='Interest Over Time: "{query}"',
        sections=[
            TableSection(
                title="Timeline",
                data_path="timeline",
                max_rows=12,
                columns=[
                    Column(
                        name="Date",
                        key="date",
                        style=ColumnStyle.DIM,
                    ),
                    Column(
                        name="Interest",
                        key="value",
                        style=ColumnStyle.GREEN,
                        justify="right",
                    ),
                ],
                footer_template="Showing last {count} data points",
            ),
        ],
    ),
)


# =============================================================================
# trends_related
# =============================================================================

trends_related = ToolDefinition(
    name="google_trends_related",
    description="Get related queries from Google Trends",
    group="trends",
    cli_name="related",
    params=[QUERY, GEO, TIME_RANGE, NO_CACHE],
    service=ServiceConfig(
        service_class=TrendsService,
        method="get_related_queries",
        required_env=["SEARCH_API_IO_KEY"],
        cache_ttl=24 * 3600,
    ),
    output=OutputDefinition(
        title_template='Related Queries: "{query}"',
        sections=[
            TableSection(
                title="Top Queries",
                data_path="top",
                max_rows=10,
                columns=[
                    position_column(),
                    Column(
                        name="Query",
                        key="query",
                        style=ColumnStyle.BOLD,
                    ),
                    Column(
                        name="Value",
                        key="value",
                        style=ColumnStyle.GREEN,
                        justify="right",
                    ),
                ],
            ),
            TableSection(
                title="Rising Queries",
                data_path="rising",
                max_rows=10,
                columns=[
                    position_column(),
                    Column(
                        name="Query",
                        key="query",
                        style=ColumnStyle.BOLD,
                    ),
                    Column(
                        name="Value",
                        key="value",
                        style=ColumnStyle.CYAN,
                        justify="right",
                        formatter=lambda x: f"+{x}%" if isinstance(x, int) and x > 0 else str(x),
                    ),
                ],
            ),
        ],
    ),
)


# =============================================================================
# trends_topics
# =============================================================================

trends_topics = ToolDefinition(
    name="google_trends_topics",
    description="Get related topics from Google Trends",
    group="trends",
    cli_name="topics",
    params=[QUERY, GEO, TIME_RANGE, NO_CACHE],
    service=ServiceConfig(
        service_class=TrendsService,
        method="get_related_topics",
        required_env=["SEARCH_API_IO_KEY"],
        cache_ttl=24 * 3600,
    ),
    output=OutputDefinition(
        title_template='Related Topics: "{query}"',
        sections=[
            TableSection(
                title="Top Topics",
                data_path="top",
                max_rows=10,
                columns=[
                    position_column(),
                    Column(
                        name="Topic",
                        key="query",
                        style=ColumnStyle.BOLD,
                    ),
                    Column(
                        name="Value",
                        key="value",
                        style=ColumnStyle.GREEN,
                        justify="right",
                    ),
                ],
            ),
            TableSection(
                title="Rising Topics",
                data_path="rising",
                max_rows=10,
                columns=[
                    position_column(),
                    Column(
                        name="Topic",
                        key="query",
                        style=ColumnStyle.BOLD,
                    ),
                    Column(
                        name="Value",
                        key="value",
                        style=ColumnStyle.CYAN,
                        justify="right",
                        formatter=lambda x: f"+{x}%" if isinstance(x, int) and x > 0 else str(x),
                    ),
                ],
            ),
        ],
    ),
)


# =============================================================================
# trends_geo
# =============================================================================

trends_geo = ToolDefinition(
    name="google_trends_geo",
    description="Get Google Trends interest by region",
    group="trends",
    cli_name="geo",
    params=[QUERY, GEO, TIME_RANGE, NO_CACHE],
    service=ServiceConfig(
        service_class=TrendsService,
        method="get_geo_interest",
        required_env=["SEARCH_API_IO_KEY"],
        cache_ttl=24 * 3600,
    ),
    output=OutputDefinition(
        title_template='Interest by Region: "{query}"',
        sections=[
            TableSection(
                data_path="regions",
                max_rows=20,
                columns=[
                    position_column(),
                    Column(
                        name="Region",
                        key="location",
                        style=ColumnStyle.BOLD,
                    ),
                    Column(
                        name="Code",
                        key="location_code",
                        style=ColumnStyle.DIM,
                    ),
                    Column(
                        name="Interest",
                        key="value",
                        style=ColumnStyle.GREEN,
                        justify="right",
                    ),
                ],
                footer_template="Showing {count} regions",
            ),
        ],
    ),
)


# All Trends tools
TRENDS_TOOLS = [
    trends_interest,
    trends_related,
    trends_topics,
    trends_geo,
]
