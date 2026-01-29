"""Google AI Mode tool definitions."""

from ..registry import (
    ToolDefinition,
    ServiceConfig,
    OutputDefinition,
    TableSection,
    MarkdownSection,
    QUERY,
    LOCATION,
    NO_CACHE,
    position_column,
    title_column,
    link_column,
    Column,
    ColumnStyle,
)
from ..services import AiModeService


# =============================================================================
# ai_mode_search
# =============================================================================

ai_mode_search = ToolDefinition(
    name="google_ai_mode",
    description="Get AI-generated response from Google AI Mode",
    group="ai",
    cli_name="search",
    params=[QUERY, LOCATION, NO_CACHE],
    service=ServiceConfig(
        service_class=AiModeService,
        method="search",
        required_env=["SEARCH_API_IO_KEY"],
        cache_ttl=12 * 3600,
    ),
    output=OutputDefinition(
        title_template='Google AI Mode: "{query}"',
        sections=[
            MarkdownSection(
                title="AI Response",
                data_path="markdown",
                max_length=1000,
                style=ColumnStyle.DEFAULT,
            ),
            TableSection(
                title="References",
                data_path="references",
                max_rows=10,
                columns=[
                    position_column(),
                    title_column(max_width=40),
                    link_column(max_width=50),
                ],
            ),
            TableSection(
                title="Web Results",
                data_path="web_results",
                max_rows=5,
                columns=[
                    position_column(),
                    title_column(max_width=40),
                    link_column(max_width=50),
                ],
            ),
        ],
    ),
)


# All AI tools
AI_TOOLS = [
    ai_mode_search,
]
