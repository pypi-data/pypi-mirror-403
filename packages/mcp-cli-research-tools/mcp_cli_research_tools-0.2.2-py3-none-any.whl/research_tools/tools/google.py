"""Google/Serper tool definitions."""

from ..registry import (
    ToolDefinition,
    ServiceConfig,
    OutputDefinition,
    TableSection,
    ListSection,
    Param,
    ParamType,
    QUERY,
    NUM_RESULTS,
    COUNTRY,
    NO_CACHE,
    position_column,
    title_column,
    link_column,
    Column,
    ColumnStyle,
)
from ..services import GoogleService


# =============================================================================
# google_keywords
# =============================================================================

google_keywords = ToolDefinition(
    name="google_keywords",
    description="Get Google autocomplete keyword suggestions",
    group="google",
    params=[QUERY, NO_CACHE],
    service=ServiceConfig(
        service_class=GoogleService,
        method="get_keywords",
        required_env=["SERPER_API_KEY"],
        cache_ttl=48 * 3600,
    ),
    output=OutputDefinition(
        title_template='Keyword Suggestions for "{query}"',
        sections=[
            ListSection(
                data_path="suggestions",
                numbered=True,
                max_items=20,
            ),
        ],
    ),
)


# =============================================================================
# google_serp
# =============================================================================

google_serp = ToolDefinition(
    name="google_serp",
    description="Analyze Google SERP results (who ranks for a query)",
    group="google",
    params=[QUERY, NUM_RESULTS, COUNTRY, NO_CACHE],
    service=ServiceConfig(
        service_class=GoogleService,
        method="get_serp",
        required_env=["SERPER_API_KEY"],
        cache_ttl=48 * 3600,
    ),
    output=OutputDefinition(
        title_template='Top Results: "{query}"',
        sections=[
            TableSection(
                data_path="results",
                columns=[
                    Column(
                        name="#",
                        key="position",
                        style=ColumnStyle.POSITION,
                        width=3,
                        justify="right",
                    ),
                    title_column(max_width=50),
                    link_column(max_width=50),
                ],
                footer_template="Showing {count} results",
            ),
        ],
    ),
)


# =============================================================================
# google_paa
# =============================================================================

google_paa = ToolDefinition(
    name="google_paa",
    description="Get People Also Ask questions from Google",
    group="google",
    params=[QUERY, COUNTRY, NO_CACHE],
    service=ServiceConfig(
        service_class=GoogleService,
        method="get_paa",
        required_env=["SERPER_API_KEY"],
        cache_ttl=48 * 3600,
    ),
    output=OutputDefinition(
        title_template='People Also Ask: "{query}"',
        sections=[
            TableSection(
                data_path="questions",
                columns=[
                    position_column(),
                    Column(
                        name="Question",
                        key="question",
                        style=ColumnStyle.BOLD,
                        max_width=60,
                    ),
                    Column(
                        name="Answer",
                        key="snippet",
                        style=ColumnStyle.DIM,
                        max_width=60,
                        truncate_at=100,
                    ),
                ],
            ),
        ],
    ),
)


# =============================================================================
# google_related
# =============================================================================

google_related = ToolDefinition(
    name="google_related",
    description="Get related searches from Google",
    group="google",
    params=[QUERY, COUNTRY, NO_CACHE],
    service=ServiceConfig(
        service_class=GoogleService,
        method="get_related",
        required_env=["SERPER_API_KEY"],
        cache_ttl=48 * 3600,
    ),
    output=OutputDefinition(
        title_template='Related Searches: "{query}"',
        sections=[
            ListSection(
                data_path="related_searches",
                numbered=True,
                max_items=10,
            ),
        ],
    ),
)


# All Google tools
GOOGLE_TOOLS = [
    google_keywords,
    google_serp,
    google_paa,
    google_related,
]
