"""Composable renderer engine."""

import sys
from typing import Any

from rich.console import Console
from rich.table import Table

from .sections import (
    OutputDefinition,
    TableSection,
    ListSection,
    MarkdownSection,
    KeyValueSection,
    StatsSection,
    Column,
    ColumnStyle,
)


# Force UTF-8 on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

console = Console(force_terminal=True)


def _get_nested_value(obj: dict | object, path: str) -> Any:
    """
    Get nested value from dict/object using dot notation.

    Examples:
        _get_nested_value({"a": {"b": 1}}, "a.b") -> 1
        _get_nested_value({"items": [1,2,3]}, "items[0]") -> 1
        _get_nested_value(data, "results[:10]") -> first 10 results
    """
    if not path:
        return obj

    current = obj
    for part in path.replace("[", ".[").split("."):
        if not part:
            continue

        if part.startswith("["):
            # Array access: [0], [:10], [-1]
            idx = part[1:-1]
            if ":" in idx:
                # Slice
                parts = idx.split(":")
                start = int(parts[0]) if parts[0] else None
                end = int(parts[1]) if parts[1] else None
                current = current[start:end]
            else:
                current = current[int(idx)]
        elif isinstance(current, dict):
            current = current.get(part)
        else:
            current = getattr(current, part, None)

        if current is None:
            return None

    return current


def _apply_style(text: str, style: ColumnStyle, value: Any = None) -> str:
    """Apply Rich style markup to text."""
    if style == ColumnStyle.POSITION:
        # Special position styling: green <=3, yellow <=10, dim >10
        try:
            pos = int(value) if value is not None else int(text)
            if pos <= 3:
                return f"[green]{text}[/green]"
            elif pos <= 10:
                return f"[yellow]{text}[/yellow]"
            else:
                return f"[dim]{text}[/dim]"
        except (ValueError, TypeError):
            return f"[dim]{text}[/dim]"

    style_map = {
        ColumnStyle.DEFAULT: text,
        ColumnStyle.BOLD: f"[bold]{text}[/bold]",
        ColumnStyle.DIM: f"[dim]{text}[/dim]",
        ColumnStyle.CYAN: f"[cyan]{text}[/cyan]",
        ColumnStyle.GREEN: f"[green]{text}[/green]",
        ColumnStyle.YELLOW: f"[yellow]{text}[/yellow]",
        ColumnStyle.MAGENTA: f"[magenta]{text}[/magenta]",
        ColumnStyle.RED: f"[red]{text}[/red]",
    }
    return style_map.get(style, text)


def _format_column_value(col: Column, value: Any, row_index: int) -> str:
    """Format a single column value."""
    # Handle special _index key
    if col.key == "_index":
        value = row_index + 1

    # Apply custom formatter
    if col.formatter and value is not None:
        value = col.formatter(value)

    # Convert to string
    if value is None:
        text = "-"
    elif isinstance(value, (list, tuple)):
        text = ", ".join(str(v) for v in value)
    else:
        text = str(value)

    # Apply prefix/suffix
    if col.prefix and text != "-":
        text = f"{col.prefix}{text}"
    if col.suffix and text != "-":
        text = f"{text}{col.suffix}"

    # Truncate if needed
    if col.truncate_at and len(text) > col.truncate_at:
        text = text[: col.truncate_at] + "..."

    return text


def _render_table_section(section: TableSection, data: dict) -> None:
    """Render a table section."""
    # Get data list
    items = _get_nested_value(data, section.data_path) if section.data_path else data
    if not items:
        console.print("[dim]No data found[/dim]")
        return

    if not isinstance(items, list):
        items = [items]

    # Apply max_rows limit
    total_count = len(items)
    if section.max_rows:
        items = items[: section.max_rows]

    # Create table
    table = Table(title=section.title, show_lines=section.show_lines)

    # Add columns
    for col in section.columns:
        kwargs: dict[str, Any] = {}
        if col.width:
            kwargs["width"] = col.width
        if col.max_width:
            kwargs["max_width"] = col.max_width
        if col.justify != "left":
            kwargs["justify"] = col.justify
        if col.overflow:
            kwargs["overflow"] = col.overflow

        # Base style (without position logic)
        style = None
        if col.style not in (ColumnStyle.DEFAULT, ColumnStyle.POSITION):
            style = col.style.value

        table.add_column(col.name, style=style, **kwargs)

    # Add rows
    for i, item in enumerate(items):
        row_values = []
        for col in section.columns:
            raw_value = _get_nested_value(item, col.key) if col.key != "_index" else i + 1
            formatted = _format_column_value(col, raw_value, i)

            # Apply position styling if needed
            if col.style == ColumnStyle.POSITION:
                formatted = _apply_style(formatted, col.style, raw_value)

            row_values.append(formatted)

        table.add_row(*row_values)

    console.print()
    console.print(table)

    # Footer
    if section.footer_template:
        footer = section.footer_template.format(count=len(items), total=total_count)
        console.print(f"[dim]{footer}[/dim]")


def _render_list_section(section: ListSection, data: dict) -> None:
    """Render a list section."""
    items = _get_nested_value(data, section.data_path)
    if not items:
        console.print("[dim]No items found[/dim]")
        return

    if section.title:
        console.print()
        console.print(f"[bold]{section.title}[/bold]")
        console.print("-" * 40)

    max_items = section.max_items or len(items)
    for i, item in enumerate(items[:max_items], 1):
        if isinstance(item, dict):
            text = section.item_template.format(**item)
        else:
            text = section.item_template.format(item=item)

        styled_text = _apply_style(text, section.style)

        if section.numbered:
            console.print(f"  {i:2}. {styled_text}")
        else:
            console.print(f"  - {styled_text}")


def _render_markdown_section(section: MarkdownSection, data: dict) -> None:
    """Render a markdown/text section."""
    content = _get_nested_value(data, section.data_path)
    if not content:
        return

    if section.title:
        console.print()
        console.print(f"[bold {section.style.value}]{section.title}[/bold {section.style.value}]")
        console.print("-" * 40)

    # Truncate if needed
    if section.max_length and len(content) > section.max_length:
        content = content[: section.max_length] + "\n\n[dim]... (truncated)[/dim]"

    console.print(_apply_style(content, section.style))


def _render_key_value_section(section: KeyValueSection, data: dict) -> None:
    """Render a key-value pairs section."""
    if section.title:
        console.print()
        console.print(f"[bold]{section.title}[/bold]")
        console.print("-" * 40)

    items = section.items
    if section.data_path:
        raw = _get_nested_value(data, section.data_path)
        if isinstance(raw, dict):
            items = list(raw.items())

    if not items:
        return

    for key, value in items:
        key_styled = _apply_style(str(key), section.key_style)
        value_styled = _apply_style(str(value), section.value_style)
        console.print(f"  {key_styled}: {value_styled}")


def _render_stats_section(section: StatsSection, data: dict) -> None:
    """Render a statistics section."""
    if section.title:
        console.print()
        console.print(f"[bold]{section.title}[/bold]")
        console.print("-" * 40)

    for label, path, style in section.stats:
        value = _get_nested_value(data, path)
        value_styled = _apply_style(str(value), style)
        console.print(f"  [bold]{label}:[/bold] {value_styled}")


def render(output_def: OutputDefinition, data: dict) -> None:
    """
    Render complete output from definition and data.

    Args:
        output_def: Output definition with sections
        data: Result data (dict from to_dict())
    """
    # Render title
    console.print()
    try:
        title = output_def.title_template.format(**data)
    except KeyError:
        title = output_def.title_template
    console.print(f"[bold]{title}[/bold]")

    # Render subtitle if present
    if output_def.subtitle_template:
        try:
            subtitle = output_def.subtitle_template.format(**data)
        except KeyError:
            subtitle = output_def.subtitle_template
        console.print(f"[dim]{subtitle}[/dim]")

    console.print("=" * 60)

    # Render each section
    for section in output_def.sections:
        if isinstance(section, TableSection):
            _render_table_section(section, data)
        elif isinstance(section, ListSection):
            _render_list_section(section, data)
        elif isinstance(section, MarkdownSection):
            _render_markdown_section(section, data)
        elif isinstance(section, KeyValueSection):
            _render_key_value_section(section, data)
        elif isinstance(section, StatsSection):
            _render_stats_section(section, data)

    console.print()
