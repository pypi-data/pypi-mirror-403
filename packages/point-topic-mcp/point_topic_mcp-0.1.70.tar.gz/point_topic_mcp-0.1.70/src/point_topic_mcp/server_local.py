"""Local MCP server using stdio transport for Claude Desktop integration."""

import os
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from point_topic_mcp.tools import register_tools
from point_topic_mcp.prompts import register_prompts

# Load environment variables at module level
load_dotenv()

# Create FastMCP instance (at module level)
mcp = FastMCP(
    name="Point Topic MCP",
    instructions="UK broadband data analysis server for local development",
)

# Register tools and prompts at module level (so they're available when mcp CLI imports this)
register_tools(mcp)
register_prompts(mcp)


def main():
    """Main entry point for the MCP server."""
    # Run with stdio transport (default for local/Claude Desktop)
    mcp.run()


if __name__ == "__main__":
    main()
