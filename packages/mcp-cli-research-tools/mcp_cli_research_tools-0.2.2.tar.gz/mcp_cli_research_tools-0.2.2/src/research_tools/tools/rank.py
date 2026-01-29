"""Google Rank Tracking tool definitions."""

from ..registry import (
    ToolDefinition,
    ServiceConfig,
    OutputDefinition,
    TableSection,
    QUERY,
    DEVICE,
    LOCATION,
    COUNTRY,
    LANGUAGE,
    NUM_RESULTS,
    NO_CACHE,
    position_column,
    title_column,
    domain_column,
    Column,
    ColumnStyle,
)
from ..services import RankTrackingService


# =============================================================================
# rank_track
# =============================================================================

rank_track = ToolDefinition(
    name="google_rank_tracking",
    description="Track keyword rankings in Google (up to 100 results)",
    group="rank",
    cli_name="track",
    params=[QUERY, DEVICE, LOCATION, COUNTRY, LANGUAGE, NUM_RESULTS, NO_CACHE],
    service=ServiceConfig(
        service_class=RankTrackingService,
        method="track",
        required_env=["SEARCH_API_IO_KEY"],
        cache_ttl=24 * 3600,
    ),
    output=OutputDefinition(
        title_template='Rank Tracking: "{query}"',
        subtitle_template="Device: {device} | Location: {location} | Country: {gl}",
        sections=[
            TableSection(
                data_path="results",
                columns=[
                    position_column(),
                    title_column(max_width=40),
                    domain_column(),
                    Column(
                        name="Snippet",
                        key="snippet",
                        style=ColumnStyle.DIM,
                        max_width=40,
                        truncate_at=80,
                    ),
                ],
                footer_template="Showing {count} results",
            ),
        ],
    ),
)


# All Rank tools
RANK_TOOLS = [
    rank_track,
]
