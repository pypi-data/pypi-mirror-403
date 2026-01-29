"""Google Ads Transparency tool definitions."""

from ..registry import (
    ToolDefinition,
    ServiceConfig,
    OutputDefinition,
    TableSection,
    DOMAIN,
    REGION,
    AD_PLATFORM,
    AD_FORMAT,
    AD_TIME_PERIOD,
    NUM_RESULTS,
    NO_CACHE,
    position_column,
    domain_column,
    date_column,
    Column,
    ColumnStyle,
)
from ..services import AdsTransparencyService


# =============================================================================
# ads_transparency
# =============================================================================

ads_transparency = ToolDefinition(
    name="google_ads_transparency",
    description="Get all ads for an advertiser from Google Ads Transparency Center",
    group="transparency",
    cli_name="ads",
    params=[DOMAIN, REGION, AD_PLATFORM, AD_FORMAT, AD_TIME_PERIOD, NUM_RESULTS, NO_CACHE],
    service=ServiceConfig(
        service_class=AdsTransparencyService,
        method="get_ads",
        required_env=["SEARCH_API_IO_KEY"],
        cache_ttl=24 * 3600,
    ),
    output=OutputDefinition(
        title_template='Ads Transparency: "{domain}"',
        subtitle_template="Region: {region} | Platform: {platform} | Period: {time_period}",
        sections=[
            TableSection(
                data_path="ads",
                columns=[
                    position_column(),
                    Column(
                        name="Advertiser",
                        key="advertiser_name",
                        style=ColumnStyle.CYAN,
                        max_width=25,
                    ),
                    Column(
                        name="Format",
                        key="format",
                        style=ColumnStyle.DIM,
                        width=8,
                    ),
                    Column(
                        name="First Shown",
                        key="first_shown",
                        style=ColumnStyle.DIM,
                        max_width=12,
                    ),
                    Column(
                        name="Last Shown",
                        key="last_shown",
                        style=ColumnStyle.DIM,
                        max_width=12,
                    ),
                    Column(
                        name="Days",
                        key="days_displayed",
                        style=ColumnStyle.GREEN,
                        justify="right",
                        width=6,
                    ),
                ],
                footer_template="Showing {count} ads",
            ),
        ],
    ),
)


# All Transparency tools
TRANSPARENCY_TOOLS = [
    ads_transparency,
]
