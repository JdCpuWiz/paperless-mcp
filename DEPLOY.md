# paperless-mcp — Deployment Guide

## Requirements

- Docker + Docker Compose v2 on the Paperless-NGX server (192.168.7.203)
- A running Paperless-NGX instance
- A Paperless API token (generate under Admin → Auth Token in the Paperless UI)

---

## 1. Get the files

On the Paperless server:

```bash
git clone https://github.com/JdCpuWiz/paperless-mcp.git
cd paperless-mcp
```

---

## 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env`:

```env
# URL of your Paperless-NGX instance
# If deploying on the same host as Paperless, use the internal Docker service name
# (e.g. http://paperless-webserver:8000) if on the same compose network,
# or the host IP if running standalone.
PAPERLESS_URL=http://192.168.7.203:8000

# API token — generate in Paperless under Admin → Auth Token
PAPERLESS_API_TOKEN=your-token-here
```

---

## 3. Deploy

```bash
docker compose up -d --build
```

Verify it started:

```bash
docker compose logs -f
```

You should see `Uvicorn running on http://0.0.0.0:8013`.

Test it responds:

```bash
curl http://localhost:8013/mcp
```

---

## 4. Register with Jarvis AI

On the Jarvis server, `jarvis-ai/mcp_servers.default.json` already includes this entry (committed alongside this server):

```json
{
  "name": "paperless",
  "url": "http://192.168.7.203:8013/mcp",
  "transport": "streamable_http",
  "timeout": 10.0
}
```

To activate it, rebuild the Jarvis agent:

```bash
cd ~/jarvis-ai
git pull
docker compose up -d --build agent
```

Jarvis will discover and register all 10 Paperless tools automatically on startup.

---

## Updating

```bash
cd ~/paperless-mcp
git pull
docker compose up -d --build
```

---

## Data & Persistence

This server is stateless — it proxies requests to Paperless-NGX. No local data is stored. All documents and metadata remain in Paperless.

---

## Troubleshooting

**Container exits immediately**
```bash
docker compose logs paperless-mcp
```
Usually a missing `.env` file or malformed token.

**401 Unauthorized from Paperless**
- Verify `PAPERLESS_API_TOKEN` is correct
- In Paperless: Admin → Auth Token → confirm the token exists and is active

**Connection refused / timeout**
- Confirm `PAPERLESS_URL` is reachable from the Docker container:
  ```bash
  docker compose exec paperless-mcp wget -qO- http://192.168.7.203:8000/api/
  ```
- If running alongside Paperless on the same compose network, use the internal service name instead of the host IP

**Jarvis can't reach the MCP server**
- Confirm port 8013 is open on the Paperless server firewall
- Test from the Jarvis server: `curl http://192.168.7.203:8013/mcp`
