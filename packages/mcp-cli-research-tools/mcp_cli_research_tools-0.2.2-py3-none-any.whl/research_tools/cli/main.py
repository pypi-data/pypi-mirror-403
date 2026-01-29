"""Main CLI entry point for research-tools."""

from cyclopts import App

from .cache import app as cache_app
from ..tools import ALL_TOOLS, GROUP_CONFIGS
from ..registry import register_tools_to_cli

app = App(
    name="rt",
    help="Research tools CLI - dev.to, Google/Serper, Reddit, YouTube, Trends, News, HN, SearchAPI",
)

# Auto-register all tool groups
register_tools_to_cli(app, ALL_TOOLS, GROUP_CONFIGS)

# Cache is a utility, not a tool - registered manually
app.command(cache_app, name="cache")


def main() -> None:
    """CLI entry point."""
    app()


if __name__ == "__main__":
    main()
