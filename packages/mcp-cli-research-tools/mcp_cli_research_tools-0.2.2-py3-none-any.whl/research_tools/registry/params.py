"""Reusable parameter definitions for tools."""

from dataclasses import dataclass
from typing import Any, Callable
from enum import Enum


class ParamType(Enum):
    """Supported parameter types."""

    STRING = "string"
    INT = "int"
    BOOL = "bool"
    FLOAT = "float"
    ENUM = "enum"
    LIST = "list"  # comma-separated string -> list


@dataclass
class Param:
    """Single parameter definition."""

    name: str
    type: ParamType
    description: str
    default: Any = None
    required: bool = False

    # CLI-specific
    cli_short: str | None = None  # e.g., "-q" for query
    cli_name: str | None = None  # e.g., "--query" (auto-generated if None)

    # Validation
    min_value: int | float | None = None
    max_value: int | float | None = None
    choices: list[str] | None = None  # For enum types

    # Transformation
    parser: Callable[[str], Any] | None = None  # Custom parser (e.g., comma-split)

    def to_cli_type(self) -> type:
        """Convert to Python type for Cyclopts."""
        mapping = {
            ParamType.STRING: str,
            ParamType.INT: int,
            ParamType.BOOL: bool,
            ParamType.FLOAT: float,
            ParamType.ENUM: str,
            ParamType.LIST: str,  # Parsed later
        }
        return mapping[self.type]

    def to_mcp_schema(self) -> dict:
        """Convert to JSON Schema for MCP."""
        schema: dict[str, Any] = {"description": self.description}

        if self.type == ParamType.STRING:
            schema["type"] = "string"
        elif self.type == ParamType.INT:
            schema["type"] = "integer"
            if self.min_value is not None:
                schema["minimum"] = self.min_value
            if self.max_value is not None:
                schema["maximum"] = self.max_value
        elif self.type == ParamType.BOOL:
            schema["type"] = "boolean"
        elif self.type == ParamType.ENUM:
            schema["type"] = "string"
            schema["enum"] = self.choices
        elif self.type == ParamType.LIST:
            schema["type"] = "string"
            schema["description"] += " (comma-separated)"
        elif self.type == ParamType.FLOAT:
            schema["type"] = "number"
            if self.min_value is not None:
                schema["minimum"] = self.min_value
            if self.max_value is not None:
                schema["maximum"] = self.max_value

        if self.default is not None:
            schema["default"] = self.default

        return schema


# =============================================================================
# Common Parameters (reused across tools)
# =============================================================================


def _parse_comma_list(s: str) -> list[str]:
    """Parse comma-separated string into list."""
    return [t.strip() for t in s.split(",") if t.strip()]


QUERY = Param(
    name="query",
    type=ParamType.STRING,
    description="Search query",
    required=True,
    cli_short="-q",
)

LIMIT = Param(
    name="limit",
    type=ParamType.INT,
    description="Maximum number of results",
    default=20,
    min_value=1,
    max_value=100,
    cli_short="-l",
)

NO_CACHE = Param(
    name="no_cache",
    type=ParamType.BOOL,
    description="Skip cache, force fresh fetch",
    default=False,
)

COUNTRY = Param(
    name="gl",
    type=ParamType.STRING,
    description="Country code (e.g., us, gb, de)",
    default="us",
)

PERIOD = Param(
    name="period",
    type=ParamType.INT,
    description="Time period in days",
    default=7,
    min_value=1,
    max_value=365,
    cli_short="-p",
)

TAGS = Param(
    name="tags",
    type=ParamType.LIST,
    description="Comma-separated tags to filter",
    cli_short="-t",
    parser=_parse_comma_list,
)

DEVICE = Param(
    name="device",
    type=ParamType.ENUM,
    description="Device type",
    default="desktop",
    choices=["desktop", "mobile", "tablet"],
)

DOMAIN = Param(
    name="domain",
    type=ParamType.STRING,
    description="Domain to analyze (e.g., example.com)",
    required=True,
    cli_short="-d",
)

REGION = Param(
    name="region",
    type=ParamType.STRING,
    description="Geographic region",
    default="us",
)

NUM_RESULTS = Param(
    name="num",
    type=ParamType.INT,
    description="Number of results",
    default=10,
    min_value=1,
    max_value=100,
    cli_short="-n",
)

SUBREDDITS = Param(
    name="subreddits",
    type=ParamType.LIST,
    description="Comma-separated subreddits",
    required=True,
    cli_short="-s",
    parser=lambda s: [r.strip().lower() for r in s.split(",") if r.strip()],
)

SORT = Param(
    name="sort",
    type=ParamType.ENUM,
    description="Sort order",
    default="hot",
    choices=["hot", "new", "rising", "top", "controversial"],
)

REDDIT_PERIOD = Param(
    name="period",
    type=ParamType.ENUM,
    description="Time period for top/controversial",
    default="week",
    choices=["hour", "day", "week", "month", "year", "all"],
)

CHANNEL = Param(
    name="channel",
    type=ParamType.STRING,
    description="YouTube channel name",
    required=True,
    cli_short="-c",
)

CATEGORY = Param(
    name="category",
    type=ParamType.STRING,
    description="Content category (music, gaming, tech, etc.)",
)

GEO = Param(
    name="geo",
    type=ParamType.STRING,
    description="Country code (us, gb, etc.) or empty for worldwide",
    default="",
)

TIME_RANGE = Param(
    name="time_range",
    type=ParamType.STRING,
    description="Time range (today 12-m, today 3-m, now 7-d)",
    default="today 12-m",
    cli_name="--time",
)

DATA_TYPE = Param(
    name="data_type",
    type=ParamType.ENUM,
    description="Type of trends data",
    default="interest",
    choices=["interest", "related", "topics", "geo"],
)

TIME_PERIOD = Param(
    name="time_period",
    type=ParamType.ENUM,
    description="Time filter: hour, day, week, month, year (empty = all time)",
    default="",
    choices=["", "hour", "day", "week", "month", "year"],
)

SORT_BY = Param(
    name="sort_by",
    type=ParamType.ENUM,
    description="Sort order for news",
    default="",
    choices=["", "relevance", "most_recent"],
)

AD_PLATFORM = Param(
    name="platform",
    type=ParamType.ENUM,
    description="Platform filter for ads",
    default="",
    choices=["", "search", "youtube", "maps", "shopping", "google_play"],
)

AD_FORMAT = Param(
    name="ad_format",
    type=ParamType.ENUM,
    description="Ad format filter",
    default="",
    choices=["", "text", "image", "video"],
)

AD_TIME_PERIOD = Param(
    name="time_period",
    type=ParamType.ENUM,
    description="Time range for ads",
    default="last_30_days",
    choices=["last_30_days", "last_90_days", "anytime"],
)

LOCATION = Param(
    name="location",
    type=ParamType.STRING,
    description="Geographic location (e.g., San Francisco)",
    default="",
)

LANGUAGE = Param(
    name="hl",
    type=ParamType.STRING,
    description="Language code",
    default="en",
)

KEYWORDS = Param(
    name="keywords",
    type=ParamType.LIST,
    description="Comma-separated keywords",
    required=True,
    cli_short="-k",
    parser=_parse_comma_list,
)

COMPETITOR = Param(
    name="competitor",
    type=ParamType.STRING,
    description="Competitor domain",
    required=True,
    cli_short="-c",
)

ENGINES = Param(
    name="engines",
    type=ParamType.LIST,
    description="Comma-separated LLM engines (perplexity, google_ai). Empty = all available",
    default="",
    parser=_parse_comma_list,
)
