"""Reddit tool definitions."""

from ..registry import (
    ToolDefinition,
    ServiceConfig,
    OutputDefinition,
    TableSection,
    SUBREDDITS,
    SORT,
    REDDIT_PERIOD,
    LIMIT,
    NO_CACHE,
    position_column,
    title_column,
    author_column,
    score_column,
    comments_column,
    Column,
    ColumnStyle,
)
from ..services import RedditService


# =============================================================================
# reddit_posts
# =============================================================================

reddit_posts = ToolDefinition(
    name="reddit_posts",
    description="Monitor subreddit posts (hot, new, rising, top, controversial)",
    group="reddit",
    params=[SUBREDDITS, SORT, REDDIT_PERIOD, LIMIT, NO_CACHE],
    service=ServiceConfig(
        service_class=RedditService,
        method="get_posts",
        required_env=[],  # No API key needed
        cache_ttl=12 * 3600,
    ),
    output=OutputDefinition(
        title_template="Reddit Posts ({sort})",
        sections=[
            TableSection(
                data_path="posts",
                columns=[
                    position_column(),
                    title_column(max_width=50),
                    Column(
                        name="Subreddit",
                        key="subreddit",
                        style=ColumnStyle.CYAN,
                        prefix="r/",
                        max_width=15,
                    ),
                    score_column(),
                    Column(
                        name="Ratio",
                        key="upvote_ratio",
                        style=ColumnStyle.YELLOW,
                        justify="right",
                        formatter=lambda x: f"{x:.0%}" if isinstance(x, (int, float)) else str(x),
                    ),
                    comments_column(),
                    author_column(key="author", prefix="u/"),
                ],
                footer_template="Showing {count} posts",
            ),
        ],
    ),
)


# All Reddit tools
REDDIT_TOOLS = [
    reddit_posts,
]
