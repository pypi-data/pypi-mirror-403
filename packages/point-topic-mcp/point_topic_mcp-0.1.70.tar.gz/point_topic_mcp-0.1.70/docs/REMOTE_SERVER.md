# Remote MCP Server

Deploy and connect to the Point Topic MCP server remotely via FastMCP Cloud.

## Overview

This guide covers deploying the MCP server to FastMCP Cloud and connecting from various MCP clients.

## Prerequisites

- FastMCP Cloud account (sign up at https://fastmcp.cloud)
- GitHub repository access
- Environment variables configured (Snowflake credentials)

## Deployment

### 1. Sign up at FastMCP Cloud

Visit https://fastmcp.cloud and create an account.

### 2. Connect GitHub Repository

1. Go to FastMCP Cloud dashboard
2. Click "Connect Repository"
3. Select `Point-Topic/point-topic-mcp`
4. Authorize FastMCP Cloud to access your repository

### 3. Configure Environment Variables

In FastMCP Cloud dashboard, set these environment variables:

```env
# Required for Snowflake
SNOWFLAKE_USER=<your-snowflake-user>
SNOWFLAKE_PASSWORD=<your-snowflake-password>
SNOWFLAKE_ACCOUNT=<your-account>
SNOWFLAKE_WAREHOUSE=<your-warehouse>
SNOWFLAKE_DATABASE=<your-database>
SNOWFLAKE_SCHEMA=<your-schema>

# Optional: Enable Auth0 authentication
AUTH_ENABLED=true
AUTH0_DOMAIN=point-topic.eu.auth0.com
AUTH0_AUDIENCE=http://mcp-api

# Server configuration
MCP_HTTP_HOST=0.0.0.0
MCP_HTTP_PORT=8000
```

### 4. Deploy

FastMCP Cloud automatically:
- Builds the Python package
- Handles TLS/HTTPS certificates
- Provides deployment URL
- Scales based on traffic

After deployment, you'll get a URL like:
```
https://point-topic-mcp.fastmcp.cloud/mcp
```

## Client Connection

### Claude Desktop

Install `mcp-remote` and configure:

```json
{
  "mcpServers": {
    "point-topic": {
      "command": "npx",
      "args": [
        "-y",
        "mcp-remote",
        "https://point-topic-mcp.fastmcp.cloud/mcp",
        "--header",
        "Authorization: Bearer YOUR_TOKEN"
      ]
    }
  }
}
```

### Cursor

Configure directly in Cursor settings:

```json
{
  "mcpServers": {
    "point-topic": {
      "url": "https://point-topic-mcp.fastmcp.cloud/mcp",
      "transport": "http",
      "headers": {
        "Authorization": "Bearer YOUR_TOKEN"
      }
    }
  }
}
```

### Claude Web

Use the deployment URL directly in Claude web interface when connecting to MCP servers.

## Local Development

Run locally without FastMCP Cloud:

```bash
# Without authentication
point-topic-mcp-http

# With authentication
AUTH_ENABLED=true \
  AUTH0_DOMAIN=point-topic.eu.auth0.com \
  AUTH0_AUDIENCE=http://mcp-api \
  point-topic-mcp-http
```

Server will be available at: `http://localhost:8000/mcp`

## Architecture

### Server Files

- **`server_local.py`** - stdio transport for local Claude Desktop
- **`server_http.py`** - HTTP transport for remote access

Both use the same tools and prompts:
- `point_topic_mcp.tools.register_tools(mcp)`
- `point_topic_mcp.prompts.register_prompts(mcp)`

### Transport Differences

| Feature | server_local.py | server_http.py |
|---------|----------------|----------------|
| Transport | stdio | HTTP |
| Use case | Local Claude Desktop | Remote clients |
| Authentication | None | JWT (optional) |
| Entry point | `point-topic-mcp` | `point-topic-mcp-http` |

## Troubleshooting

### Connection refused

Ensure environment variables are set correctly in FastMCP Cloud dashboard.

### Authentication errors

If using Auth0, ensure:
- `AUTH_ENABLED=true` is set
- `AUTH0_DOMAIN` and `AUTH0_AUDIENCE` are correct
- User has valid Auth0 token

### Snowflake errors

Check all `SNOWFLAKE_*` environment variables are set in FastMCP Cloud.

## Support

For issues with:
- **Server code** → Open issue at https://github.com/point-topic/point-topic-mcp
- **FastMCP Cloud** → Contact FastMCP Cloud support
- **Auth0** → Check sub-site Auth0 configuration
