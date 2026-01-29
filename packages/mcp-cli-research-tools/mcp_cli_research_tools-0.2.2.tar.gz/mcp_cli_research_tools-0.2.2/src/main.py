"""MCPize dev entry point - runs HTTP mode for mcpize dev."""

import sys
sys.argv.append("--http")

from research_tools.mcp import main

if __name__ == "__main__":
    main()
