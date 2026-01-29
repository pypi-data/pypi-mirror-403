"""Composable output section primitives."""

from dataclasses import dataclass, field
from typing import Any, Callable
from enum import Enum


class ColumnStyle(Enum):
    """Predefined column styles."""

    DEFAULT = "default"
    BOLD = "bold"
    DIM = "dim"
    CYAN = "cyan"
    GREEN = "green"
    YELLOW = "yellow"
    MAGENTA = "magenta"
    RED = "red"
    POSITION = "position"  # Special: green <=3, yellow <=10, dim >10


@dataclass
class Column:
    """Table column definition."""

    name: str
    key: str  # Path to data (e.g., "title", "author.name", "tags[0]")
    style: ColumnStyle = ColumnStyle.DEFAULT
    width: int | None = None
    max_width: int | None = None
    justify: str = "left"  # left, right, center
    overflow: str = "ellipsis"

    # Formatting
    formatter: Callable[[Any], str] | None = None  # Custom formatter
    prefix: str = ""  # e.g., "@" for usernames, "#" for positions
    suffix: str = ""  # e.g., "min" for reading time

    # Truncation
    truncate_at: int | None = None  # Truncate text at N chars


@dataclass
class TableSection:
    """Table output section."""

    title: str | None = None
    columns: list[Column] = field(default_factory=list)
    data_path: str = ""  # Path to list in result (e.g., "articles", "results")
    max_rows: int | None = None  # Limit displayed rows
    show_index: bool = True  # Show row numbers
    show_lines: bool = False  # Table grid lines

    # Footer
    footer_template: str | None = None  # e.g., "Showing {count} of {total} results"


@dataclass
class ListSection:
    """Simple numbered/bulleted list section."""

    title: str | None = None
    data_path: str = ""  # Path to list
    item_template: str = "{item}"  # How to format each item
    numbered: bool = True
    max_items: int | None = 10
    style: ColumnStyle = ColumnStyle.DEFAULT


@dataclass
class MarkdownSection:
    """Markdown/text content section."""

    title: str | None = None
    data_path: str = ""  # Path to markdown string
    max_length: int | None = 500  # Truncate long content
    style: ColumnStyle = ColumnStyle.DIM


@dataclass
class KeyValueSection:
    """Key-value pairs section (for stats, metadata)."""

    title: str | None = None
    items: list[tuple[str, str]] | None = None  # Static items
    data_path: str | None = None  # Or dynamic from result
    key_style: ColumnStyle = ColumnStyle.BOLD
    value_style: ColumnStyle = ColumnStyle.GREEN


@dataclass
class StatsSection:
    """Summary statistics section."""

    title: str | None = None
    stats: list[tuple[str, str, ColumnStyle]] = field(default_factory=list)
    # Each stat: (label, data_path, style)


@dataclass
class SubtitleSection:
    """Metadata shown below title."""

    template: str  # e.g., "Device: {device} | Location: {location}"


# =============================================================================
# Output Definition
# =============================================================================


@dataclass
class OutputDefinition:
    """Complete output definition for a tool."""

    title_template: str  # e.g., 'SERP: "{query}"' - uses result fields
    sections: list[TableSection | ListSection | MarkdownSection | KeyValueSection | StatsSection]

    # Metadata shown below title
    subtitle_template: str | None = None  # e.g., "Device: {device} | Location: {location}"


# =============================================================================
# Predefined Column Templates
# =============================================================================


def position_column(name: str = "#", width: int = 3) -> Column:
    """Standard position/rank column."""
    return Column(
        name=name,
        key="_index",  # Special: row index
        style=ColumnStyle.POSITION,
        width=width,
        justify="right",
    )


def title_column(key: str = "title", max_width: int = 50) -> Column:
    """Standard title column."""
    return Column(
        name="Title",
        key=key,
        style=ColumnStyle.BOLD,
        max_width=max_width,
        overflow="ellipsis",
    )


def author_column(key: str = "author", prefix: str = "@") -> Column:
    """Standard author/username column."""
    return Column(
        name="Author",
        key=key,
        style=ColumnStyle.CYAN,
        prefix=prefix,
        max_width=15,
    )


def domain_column(key: str = "domain") -> Column:
    """Standard domain column."""
    return Column(
        name="Domain",
        key=key,
        style=ColumnStyle.CYAN,
        max_width=25,
    )


def count_column(name: str, key: str, style: ColumnStyle = ColumnStyle.GREEN) -> Column:
    """Standard count/metric column."""
    return Column(
        name=name,
        key=key,
        style=style,
        justify="right",
        formatter=lambda x: f"{x:,}" if isinstance(x, int) else str(x),
    )


def date_column(key: str = "date", name: str = "Date") -> Column:
    """Standard date column."""
    return Column(
        name=name,
        key=key,
        style=ColumnStyle.DIM,
        max_width=15,
    )


def tags_column(key: str = "tags", max_tags: int = 3) -> Column:
    """Standard tags column with truncation."""

    def format_tags(tags: list[str]) -> str:
        if not tags:
            return ""
        shown = tags[:max_tags]
        result = ", ".join(shown)
        if len(tags) > max_tags:
            result += "..."
        return result

    return Column(
        name="Tags",
        key=key,
        style=ColumnStyle.DIM,
        max_width=30,
        formatter=format_tags,
    )


def link_column(key: str = "link", max_width: int = 50) -> Column:
    """Standard URL/link column."""
    return Column(
        name="Link",
        key=key,
        style=ColumnStyle.DIM,
        max_width=max_width,
        overflow="ellipsis",
    )


def score_column(key: str = "score", name: str = "Score") -> Column:
    """Standard score column (green, right-aligned)."""
    return Column(
        name=name,
        key=key,
        style=ColumnStyle.GREEN,
        justify="right",
        formatter=lambda x: f"{x:,}" if isinstance(x, int) else str(x),
    )


def comments_column(key: str = "comments") -> Column:
    """Standard comments count column."""
    return Column(
        name="Comments",
        key=key,
        style=ColumnStyle.YELLOW,
        justify="right",
        formatter=lambda x: f"{x:,}" if isinstance(x, int) else str(x),
    )
