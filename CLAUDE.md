# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A standalone FastMCP server that gives Jarvis AI voice access to Paperless-NGX. It proxies requests from Jarvis to the Paperless REST API and returns plain-string responses formatted for voice readback.

## Running locally

```bash
pip install "mcp[cli]>=1.0.0" httpx
PAPERLESS_URL=http://192.168.7.203:8000 PAPERLESS_API_TOKEN=<token> python mcp/server.py
```

## Building and deploying

```bash
# Build and start the container
docker compose up -d --build

# View logs
docker compose logs -f

# Rebuild after code changes
docker compose up -d --build
```

## Architecture

All code lives in `mcp/server.py`. There is no framework beyond FastMCP — no routing layer, no database, no state.

- **Auth**: Paperless uses `Authorization: Token <token>` (not Bearer). The `_headers()` helper builds this from `PAPERLESS_API_TOKEN`.
- **Tools**: Each `@mcp.tool()` function maps to one Paperless API operation. Tools return plain human-readable strings — no JSON, no dicts.
- **Port**: 8013 (next in the Jarvis MCP port sequence after HomeStack on 8012).

## Adding a new tool

1. Add a `@mcp.tool()` async function in `mcp/server.py`
2. Use `httpx.AsyncClient` with `_headers()` and `_BASE`
3. Return a plain string formatted for voice — avoid raw JSON dumps
4. Check `r.status_code == 404` before `r.raise_for_status()` and return a friendly message
5. Include a full docstring with an `Args:` block — this is what Jarvis uses to decide when to call the tool

## Jarvis registration

The MCP server is registered in `~/jarvis-ai/mcp_servers.default.json` as `"paperless"` at `http://192.168.7.203:8013/mcp`. After any change, deploy on the Paperless server then rebuild the Jarvis agent:

```bash
# On 192.168.7.203
docker compose up -d --build

# On the Jarvis server
cd ~/jarvis-ai && git pull && docker compose up -d --build agent
```
