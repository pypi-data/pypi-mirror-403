"""Research tools MCP server."""

from fastmcp import FastMCP

from ..tools import ALL_TOOLS
from ..registry import register_all_mcp_tools

mcp = FastMCP("research-tools")
register_all_mcp_tools(mcp, ALL_TOOLS)
