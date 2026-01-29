"""MCP server entry point for research-tools."""

import sys

from .server import mcp


def main() -> None:
    """Run the MCP server."""
    # Check if HTTP mode requested (for mcpize dev)
    if "--http" in sys.argv or any("HTTP" in arg for arg in sys.argv):
        mcp.run(transport="streamable-http", host="0.0.0.0", port=3000, path="/mcp")
    else:
        mcp.run()
