"""LLM citation tracking tool definitions."""

from ..registry import (
    ToolDefinition,
    ServiceConfig,
    OutputDefinition,
    TableSection,
    KeyValueSection,
    QUERY,
    DOMAIN,
    KEYWORDS,
    COMPETITOR,
    ENGINES,
    NO_CACHE,
    position_column,
    domain_column,
    Column,
    ColumnStyle,
)
from ..services import LlmTrackingService


# =============================================================================
# llm_track
# =============================================================================

llm_track = ToolDefinition(
    name="llm_track",
    description="Track citations for a query across LLM engines (Perplexity, Google AI)",
    group="llm",
    cli_name="track",
    params=[QUERY, ENGINES, NO_CACHE],
    service=ServiceConfig(
        service_class=LlmTrackingService,
        method="track",
        required_env=[],  # All keys are optional - service works with any available
        optional_env=["PERPLEXITY_API_KEY", "SEARCH_API_IO_KEY", "OPENAI_API_KEY"],
        cache_ttl=12 * 3600,
    ),
    output=OutputDefinition(
        title_template='LLM Citation Tracking: "{query}"',
        subtitle_template="Total: {total_citations} citations | Cached: {cached}",
        sections=[
            TableSection(
                title="Engine Results",
                data_path="engines",
                columns=[
                    Column(name="Engine", key="engine", style=ColumnStyle.CYAN, width=12),
                    Column(name="Citations", key="total_citations", width=10, justify="right"),
                    Column(
                        name="Status",
                        key="has_response",
                        width=8,
                        formatter=lambda x: "[green]OK[/green]" if x else "[red]FAIL[/red]",
                    ),
                    Column(name="Error", key="error", style=ColumnStyle.RED, max_width=40),
                ],
            ),
            TableSection(
                title="Top Citations",
                data_path="all_citations",
                max_rows=15,
                columns=[
                    position_column(),
                    domain_column(),
                    Column(name="Title", key="title", max_width=50, truncate_at=50),
                ],
            ),
            KeyValueSection(
                title="Domain Frequency",
                data_path="domain_frequency",
                key_style=ColumnStyle.CYAN,
                value_style=ColumnStyle.GREEN,
            ),
        ],
    ),
)


# =============================================================================
# llm_brand
# =============================================================================

llm_brand = ToolDefinition(
    name="llm_brand",
    description="Monitor brand visibility across keywords in LLM responses",
    group="llm",
    cli_name="brand",
    params=[DOMAIN, KEYWORDS, ENGINES, NO_CACHE],
    service=ServiceConfig(
        service_class=LlmTrackingService,
        method="brand",
        required_env=[],
        optional_env=["PERPLEXITY_API_KEY", "SEARCH_API_IO_KEY", "OPENAI_API_KEY"],
        cache_ttl=12 * 3600,
    ),
    output=OutputDefinition(
        title_template='Brand Visibility: "{domain}"',
        subtitle_template="Visibility Score: {visibility_score}% | Total Citations: {total_citations}",
        sections=[
            TableSection(
                title="Keywords",
                data_path="results",
                columns=[
                    Column(
                        name="Keyword",
                        key="keyword",
                        style=ColumnStyle.CYAN,
                        max_width=30,
                    ),
                    Column(
                        name="Cited",
                        key="cited",
                        style=ColumnStyle.BOLD,
                        width=6,
                        formatter=lambda x: "[green]Yes[/green]" if x else "[red]No[/red]",
                    ),
                    Column(
                        name="Count",
                        key="citation_count",
                        width=6,
                        formatter=lambda x: str(x) if x else "-",
                    ),
                    Column(
                        name="Engines",
                        key="engines",
                        style=ColumnStyle.DIM,
                        max_width=30,
                        formatter=lambda x: ", ".join(x) if x else "-",
                    ),
                ],
            ),
        ],
    ),
)


# =============================================================================
# llm_compare
# =============================================================================

llm_compare = ToolDefinition(
    name="llm_compare",
    description="Compare domain vs competitor in LLM citations",
    group="llm",
    cli_name="compare",
    params=[DOMAIN, COMPETITOR, KEYWORDS, ENGINES, NO_CACHE],
    service=ServiceConfig(
        service_class=LlmTrackingService,
        method="compare",
        required_env=[],
        optional_env=["PERPLEXITY_API_KEY", "SEARCH_API_IO_KEY", "OPENAI_API_KEY"],
        cache_ttl=12 * 3600,
    ),
    output=OutputDefinition(
        title_template='LLM Comparison: "{domain}" vs "{competitor}"',
        subtitle_template="Wins: {domain_wins} vs {competitor_wins} | Ties: {ties}",
        sections=[
            TableSection(
                title="Head-to-Head",
                data_path="comparisons",
                columns=[
                    Column(
                        name="Keyword",
                        key="keyword",
                        style=ColumnStyle.CYAN,
                        max_width=30,
                    ),
                    Column(
                        name="Domain",
                        key="domain_citations",
                        style=ColumnStyle.GREEN,
                        width=8,
                        justify="right",
                    ),
                    Column(
                        name="Competitor",
                        key="competitor_citations",
                        style=ColumnStyle.YELLOW,
                        width=10,
                        justify="right",
                    ),
                    Column(
                        name="Winner",
                        key="winner",
                        width=12,
                        formatter=lambda x: {
                            "domain": "[green]Domain[/green]",
                            "competitor": "[yellow]Competitor[/yellow]",
                            "tie": "[dim]Tie[/dim]",
                            "neither": "[dim]-[/dim]",
                        }.get(x, "-"),
                    ),
                ],
            ),
        ],
    ),
)


# All LLM tools
LLM_TOOLS = [
    llm_track,
    llm_brand,
    llm_compare,
]
