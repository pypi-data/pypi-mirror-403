"""Competitor research tool definitions (SearchAPI.io)."""

from ..registry import (
    ToolDefinition,
    ServiceConfig,
    OutputDefinition,
    TableSection,
    ListSection,
    MarkdownSection,
    QUERY,
    NUM_RESULTS,
    COUNTRY,
    NO_CACHE,
    position_column,
    title_column,
    domain_column,
    Column,
    ColumnStyle,
)
from ..services import CompetitorService


# =============================================================================
# searchapi_serp (competitor_serp)
# =============================================================================

searchapi_serp = ToolDefinition(
    name="searchapi_serp",
    description="Get SERP with AI Overview and competitor ads via SearchAPI.io",
    group="competitor",
    cli_name="serp",
    params=[QUERY, NUM_RESULTS, COUNTRY, NO_CACHE],
    service=ServiceConfig(
        service_class=CompetitorService,
        method="get_serp",
        required_env=["SEARCH_API_IO_KEY"],
        cache_ttl=48 * 3600,
    ),
    output=OutputDefinition(
        title_template='Competitor SERP: "{query}"',
        sections=[
            # AI Overview (markdown)
            MarkdownSection(
                title="AI Overview",
                data_path="ai_overview.markdown",
                max_length=500,
                style=ColumnStyle.DIM,
            ),
            # Competitor Ads (table)
            TableSection(
                title="Competitor Ads",
                data_path="ads",
                columns=[
                    Column(
                        name="Pos",
                        key="block_position",
                        width=4,
                        formatter=lambda x: "TOP" if x == "top" else "BTM",
                    ),
                    domain_column(),
                    title_column(max_width=40),
                    Column(
                        name="Ad Copy",
                        key="snippet",
                        max_width=50,
                        truncate_at=100,
                        style=ColumnStyle.DIM,
                    ),
                ],
            ),
            # Organic Results (table)
            TableSection(
                title="Organic Results",
                data_path="organic",
                max_rows=10,
                columns=[
                    Column(
                        name="#",
                        key="position",
                        style=ColumnStyle.POSITION,
                        width=3,
                        justify="right",
                    ),
                    title_column(),
                    domain_column(),
                ],
            ),
            # Related Searches (list)
            ListSection(
                title="Related Searches",
                data_path="related_searches",
                max_items=5,
            ),
        ],
    ),
)


# =============================================================================
# searchapi_ads (competitor_ads)
# =============================================================================

searchapi_ads = ToolDefinition(
    name="searchapi_ads",
    description="Get competitor ads for a query via SearchAPI.io",
    group="competitor",
    cli_name="ads",
    params=[QUERY, COUNTRY, NO_CACHE],
    service=ServiceConfig(
        service_class=CompetitorService,
        method="get_ads",
        required_env=["SEARCH_API_IO_KEY"],
        cache_ttl=48 * 3600,
    ),
    output=OutputDefinition(
        title_template='Competitor Ads: "{query}"',
        sections=[
            TableSection(
                data_path="ads",
                show_lines=True,
                columns=[
                    Column(
                        name="Pos",
                        key="position",
                        width=4,
                        style=ColumnStyle.DIM,
                        formatter=lambda x: f"T{x}" if x else "-",
                    ),
                    domain_column(),
                    title_column(max_width=40),
                    Column(
                        name="Ad Copy",
                        key="snippet",
                        max_width=50,
                        truncate_at=100,
                        overflow="ellipsis",
                    ),
                ],
                footer_template="Showing {count} ads",
            ),
        ],
    ),
)


# All Competitor tools
COMPETITOR_TOOLS = [
    searchapi_serp,
    searchapi_ads,
]
