# FastMCP Cloud Migration - Planning Complete

**status**: ready for implementation  
**parent issue**: [#6 - Add remote MCP server capability](https://github.com/Point-Topic/point-topic-mcp/issues/6)  
**date**: 2026-01-27

---

## what happened

revised deployment strategy from generic fly.io approach to FastMCP Cloud hosting.

consolidated from 4-phase plan to 3-phase plan by removing redundant "production hardening" phase (FastMCP Cloud handles all that infrastructure automatically).

all github issues updated and aligned:
- phase 1: HTTP transport (issue #7)
- phase 2: Auth0 JWT validation (issue #8)
- phase 3: deployment & docs - FastMCP Cloud (issue #10)
- old phase 3 production hardening (issue #9): **closed** - redundant with FastMCP Cloud features

---

## current state

**working**:
- local MCP server via stdio (`server_local.py`)
- all tools and prompts registered correctly
- snowflake connectivity established

**not yet implemented**:
- remote HTTP transport
- authentication layer
- FastMCP Cloud deployment

---

## next steps

start with **phase 1** (issue #7):

1. create `src/point_topic_mcp/server_http.py`:
   - use `transport="streamable-http"` (not SSE)
   - set `stateless_http=True` for multi-node deployments
   - register tools and prompts (same as local)
   - host/port from env vars with sensible defaults

2. update `pyproject.toml`:
   - add `point-topic-mcp-http` script entry point

3. test locally:
   ```bash
   point-topic-mcp-http
   # verify runs on http://0.0.0.0:8000
   ```

**important**: `server_local.py` stays unchanged - keeps local dev workflow intact.

---

## key decisions

**fastmcp cloud chosen because**:
- one-command deployment (`mcp deploy`)
- automatic TLS/HTTPS
- built-in auth support (Auth0 integration ready)
- scaling/monitoring/health checks included
- no infrastructure config needed (no Dockerfile/fly.toml)

**no fallbacks**: committed to FastMCP Cloud path.

---

## code reference

full `server_http.py` implementation detailed in issue #10.

key imports:
```python
from mcp.server.fastmcp import FastMCP
from point_topic_mcp.tools import register_tools
from point_topic_mcp.prompts import register_prompts
```

key config:
```python
mcp = FastMCP(
    name="Point Topic MCP",
    instructions="UK broadband data analysis server",
    stateless_http=True,
)
```

---

## environment vars needed

**phase 1 (http transport)**:
- `MCP_HTTP_HOST` (default: "0.0.0.0")
- `MCP_HTTP_PORT` (default: "8000")

**phase 2 (auth0 jwt)**:
- `AUTH0_DOMAIN`
- `AUTH0_AUDIENCE`

**existing (snowflake)**:
- `SNOWFLAKE_USER`
- `SNOWFLAKE_PASSWORD`
- `SNOWFLAKE_ACCOUNT`

---

## verification checklist

after phase 1:
- [ ] `point-topic-mcp-http` command exists and runs
- [ ] server responds on configured port
- [ ] tools/prompts registered correctly
- [ ] local server still works (`point-topic-mcp`)

---

## links

- parent: https://github.com/Point-Topic/point-topic-mcp/issues/6
- phase 1: https://github.com/Point-Topic/point-topic-mcp/issues/7
- phase 2: https://github.com/Point-Topic/point-topic-mcp/issues/8
- phase 3: https://github.com/Point-Topic/point-topic-mcp/issues/10

---

**ready to start phase 1 implementation.**
