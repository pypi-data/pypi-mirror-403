"""Remote MCP server using streamable HTTP transport for FastMCP Cloud deployment."""

import os
from dotenv import load_dotenv
from fastmcp import FastMCP

from point_topic_mcp.tools import register_tools
from point_topic_mcp.prompts import register_prompts

# Load environment variables at module level
load_dotenv()

# Check if authentication is enabled
AUTH_ENABLED = os.getenv("AUTH_ENABLED", "false").lower() == "true"

if AUTH_ENABLED:
    # Import auth module only if auth is enabled
    from point_topic_mcp.auth import create_jwt_verifier

    # Create FastMCP instance with Auth0 JWT authentication
    auth = create_jwt_verifier()
    mcp = FastMCP(
        name="Point Topic MCP",
        instructions="UK broadband data analysis server - remote HTTP access with Auth0 authentication",
        auth=auth,
    )
    print("[MCP] Authentication enabled (Auth0 JWT)")
else:
    # Create FastMCP instance without authentication
    mcp = FastMCP(
        name="Point Topic MCP",
        instructions="UK broadband data analysis server - remote HTTP access",
    )
    print("[MCP] Authentication disabled (set AUTH_ENABLED=true to enable)")

# Register tools and prompts at module level
register_tools(mcp)
register_prompts(mcp)


def main():
    """Main entry point for the HTTP MCP server."""
    host = os.getenv("MCP_HTTP_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_HTTP_PORT", "8000"))

    # Run with HTTP transport and stateless mode for scalability
    mcp.run(transport="http", host=host, port=port, stateless_http=True)


if __name__ == "__main__":
    main()
