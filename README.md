# paperless-mcp

MCP server for [Paperless-NGX](https://docs.paperless-ngx.com) — gives Jarvis AI voice access to document search, retrieval, and metadata management.

---

## Tools

| Tool | Description |
|---|---|
| `search_documents` | Full-text search across all documents |
| `get_document` | Full details and content preview for a specific document |
| `get_recent_documents` | Recent documents, optionally filtered by today / week / month |
| `update_document` | Update title, tags, correspondent, document type, date, or ASN |
| `list_tags` | All tags with IDs and document counts |
| `get_documents_by_tag` | Documents filtered by tag name or ID |
| `list_correspondents` | All correspondents with IDs and document counts |
| `get_documents_by_correspondent` | Documents filtered by correspondent name or ID |
| `list_document_types` | All document types with IDs and document counts |
| `get_documents_by_type` | Documents filtered by type name or ID |

---

## Quick Start

**Requirements**
- Docker + Docker Compose v2
- A running Paperless-NGX instance
- A Paperless API token (Admin → Auth Token)

```bash
# 1. Get the files
git clone https://github.com/JdCpuWiz/paperless-mcp.git
cd paperless-mcp

# 2. Configure
cp .env.example .env
# Edit .env — set PAPERLESS_URL and PAPERLESS_API_TOKEN

# 3. Start
docker compose up -d --build
```

The MCP server starts on port **8013** and is reachable at `http://<host>:8013/mcp`.

See **[DEPLOY.md](DEPLOY.md)** for full deployment details and Jarvis AI registration.

---

## Architecture

Runs as a standalone Docker container (or sidecar alongside Paperless) and connects to the Paperless-NGX REST API using a token. Jarvis AI reaches it over the LAN.

```
[Jarvis agent] ──HTTP──► [paperless-mcp:8013/mcp] ──HTTP──► [Paperless-NGX:8000]
```

---

## License

[MIT](LICENSE)
