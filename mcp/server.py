#!/usr/bin/env python3
"""Paperless-NGX MCP Server — document search, retrieval, and metadata management for Jarvis AI."""

import os
from datetime import date, timedelta

import httpx
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

mcp = FastMCP(
    "paperless",
    transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
)

_BASE = os.getenv("PAPERLESS_URL", "http://192.168.7.203:8000").rstrip("/")
_TOKEN = os.getenv("PAPERLESS_API_TOKEN", "")


def _headers() -> dict:
    return {"Authorization": f"Token {_TOKEN}"}


# ── Documents ──────────────────────────────────────────────────────────────────

@mcp.tool()
async def search_documents(query: str, limit: int = 10) -> str:
    """Search Paperless-NGX documents by keyword or phrase.

    Args:
        query: Search terms or keywords to find in document content or title.
        limit: Maximum number of results to return (default 10).
    """
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{_BASE}/api/documents/",
            headers=_headers(),
            params={"query": query, "page_size": limit, "ordering": "-created"},
            timeout=15,
        )
        r.raise_for_status()
        data = r.json()

    results = data.get("results", [])
    total = data.get("count", 0)

    if not results:
        return f"No documents found matching '{query}'."

    lines = [f"Found {total} document{'s' if total != 1 else ''} matching '{query}':"]
    for doc in results:
        created = doc.get("created", "")[:10] if doc.get("created") else "unknown date"
        corr = doc.get("correspondent") or "no correspondent"
        lines.append(f"  [{doc['id']}] {doc['title']} — {created} — {corr}")

    return "\n".join(lines)


@mcp.tool()
async def get_document(document_id: int) -> str:
    """Get full details of a specific Paperless-NGX document by ID.

    Args:
        document_id: The numeric ID of the document to retrieve.
    """
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{_BASE}/api/documents/{document_id}/",
            headers=_headers(),
            timeout=15,
        )
        if r.status_code == 404:
            return f"Document {document_id} not found."
        r.raise_for_status()
        doc = r.json()

    created = doc.get("created", "")[:10] if doc.get("created") else "unknown"
    modified = doc.get("modified", "")[:10] if doc.get("modified") else "unknown"
    corr = doc.get("correspondent") or "none"
    doc_type = doc.get("document_type") or "none"
    tags = doc.get("tags") or []
    asn = doc.get("archive_serial_number") or "none"

    lines = [
        f"Document {doc['id']}: {doc['title']}",
        f"  Created: {created}  Modified: {modified}",
        f"  Correspondent: {corr}  Type: {doc_type}",
        f"  Tags: {', '.join(str(t) for t in tags) if tags else 'none'}",
        f"  Archive serial: {asn}",
    ]

    content = doc.get("content", "").strip()
    if content:
        preview = content[:300].replace("\n", " ")
        lines.append(f"  Preview: {preview}{'...' if len(content) > 300 else ''}")

    return "\n".join(lines)


@mcp.tool()
async def get_recent_documents(limit: int = 10, filter: str = "") -> str:
    """Get recently added documents from Paperless-NGX, optionally filtered by date range.

    Args:
        limit: Number of documents to return (default 10).
        filter: Optional date filter — 'today', 'week', or 'month'. Leave empty for no filter.
    """
    params: dict = {"page_size": limit, "ordering": "-created"}

    if filter:
        today = date.today()
        if filter == "today":
            params["created__date__gte"] = today.isoformat()
        elif filter == "week":
            params["created__date__gte"] = (today - timedelta(days=7)).isoformat()
        elif filter == "month":
            params["created__date__gte"] = (today - timedelta(days=30)).isoformat()

    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{_BASE}/api/documents/",
            headers=_headers(),
            params=params,
            timeout=15,
        )
        r.raise_for_status()
        data = r.json()

    results = data.get("results", [])
    total = data.get("count", 0)

    if not results:
        return "No recent documents found."

    label = f"in the last {filter}" if filter else "recently"
    lines = [f"{total} document{'s' if total != 1 else ''} added {label}:"]
    for doc in results:
        created = doc.get("created", "")[:10] if doc.get("created") else "unknown"
        corr = doc.get("correspondent") or "no correspondent"
        lines.append(f"  [{doc['id']}] {doc['title']} — {created} — {corr}")

    return "\n".join(lines)


@mcp.tool()
async def update_document(
    document_id: int,
    title: str = "",
    tag_ids: str = "",
    correspondent_id: int = 0,
    document_type_id: int = 0,
    date: str = "",
    archive_serial_number: str = "",
) -> str:
    """Update metadata on a Paperless-NGX document.

    Args:
        document_id: The numeric ID of the document to update.
        title: New title for the document (leave empty to keep current).
        tag_ids: Comma-separated list of tag IDs to set (e.g. '1,3,7'). Replaces existing tags.
        correspondent_id: Correspondent ID to assign (use 0 to keep current, -1 to clear).
        document_type_id: Document type ID to assign (use 0 to keep current, -1 to clear).
        date: Document date in YYYY-MM-DD format (leave empty to keep current).
        archive_serial_number: Archive serial number string (leave empty to keep current).
    """
    body: dict = {}

    if title:
        body["title"] = title
    if tag_ids:
        body["tags"] = [int(t.strip()) for t in tag_ids.split(",") if t.strip()]
    if correspondent_id == -1:
        body["correspondent"] = None
    elif correspondent_id > 0:
        body["correspondent"] = correspondent_id
    if document_type_id == -1:
        body["document_type"] = None
    elif document_type_id > 0:
        body["document_type"] = document_type_id
    if date:
        body["created"] = date
    if archive_serial_number:
        body["archive_serial_number"] = archive_serial_number

    if not body:
        return "No changes specified."

    async with httpx.AsyncClient() as client:
        r = await client.patch(
            f"{_BASE}/api/documents/{document_id}/",
            headers=_headers(),
            json=body,
            timeout=15,
        )
        if r.status_code == 404:
            return f"Document {document_id} not found."
        r.raise_for_status()
        doc = r.json()

    fields = list(body.keys())
    return f"Updated document {doc['id']}: {doc['title']}. Changed fields: {', '.join(fields)}."


# ── Tags ───────────────────────────────────────────────────────────────────────

@mcp.tool()
async def list_tags() -> str:
    """List all tags defined in Paperless-NGX with their document counts and IDs.

    Use the IDs when calling update_document or get_documents_by_tag.
    """
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{_BASE}/api/tags/",
            headers=_headers(),
            params={"page_size": 100},
            timeout=15,
        )
        r.raise_for_status()
        data = r.json()

    tags = data.get("results", [])
    if not tags:
        return "No tags found."

    lines = [f"{len(tags)} tag{'s' if len(tags) != 1 else ''}:"]
    for t in tags:
        lines.append(f"  [{t['id']}] {t['name']} ({t.get('document_count', 0)} docs)")

    return "\n".join(lines)


@mcp.tool()
async def get_documents_by_tag(tag_name: str = "", tag_id: int = 0, limit: int = 10) -> str:
    """Get documents that have a specific tag in Paperless-NGX.

    Args:
        tag_name: Name of the tag to filter by (partial match supported).
        tag_id: Numeric ID of the tag (use this for exact matching, takes priority over tag_name).
        limit: Maximum number of documents to return (default 10).
    """
    params: dict = {"page_size": limit, "ordering": "-created"}
    if tag_id > 0:
        params["tags__id"] = tag_id
    elif tag_name:
        params["tags__name__icontains"] = tag_name
    else:
        return "Provide either a tag name or tag ID."

    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{_BASE}/api/documents/",
            headers=_headers(),
            params=params,
            timeout=15,
        )
        r.raise_for_status()
        data = r.json()

    results = data.get("results", [])
    total = data.get("count", 0)
    label = tag_name or f"ID {tag_id}"

    if not results:
        return f"No documents found with tag '{label}'."

    lines = [f"{total} document{'s' if total != 1 else ''} tagged '{label}':"]
    for doc in results:
        created = doc.get("created", "")[:10] if doc.get("created") else "unknown"
        lines.append(f"  [{doc['id']}] {doc['title']} — {created}")

    return "\n".join(lines)


# ── Correspondents ─────────────────────────────────────────────────────────────

@mcp.tool()
async def list_correspondents() -> str:
    """List all correspondents in Paperless-NGX with their document counts and IDs.

    Use the IDs when calling update_document or get_documents_by_correspondent.
    """
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{_BASE}/api/correspondents/",
            headers=_headers(),
            params={"page_size": 100},
            timeout=15,
        )
        r.raise_for_status()
        data = r.json()

    correspondents = data.get("results", [])
    if not correspondents:
        return "No correspondents found."

    lines = [f"{len(correspondents)} correspondent{'s' if len(correspondents) != 1 else ''}:"]
    for c in correspondents:
        lines.append(f"  [{c['id']}] {c['name']} ({c.get('document_count', 0)} docs)")

    return "\n".join(lines)


@mcp.tool()
async def get_documents_by_correspondent(
    correspondent_name: str = "", correspondent_id: int = 0, limit: int = 10
) -> str:
    """Get documents from a specific correspondent in Paperless-NGX.

    Args:
        correspondent_name: Name of the correspondent to filter by (partial match supported).
        correspondent_id: Numeric ID of the correspondent (takes priority over name).
        limit: Maximum number of documents to return (default 10).
    """
    params: dict = {"page_size": limit, "ordering": "-created"}
    if correspondent_id > 0:
        params["correspondent__id"] = correspondent_id
    elif correspondent_name:
        params["correspondent__name__icontains"] = correspondent_name
    else:
        return "Provide either a correspondent name or ID."

    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{_BASE}/api/documents/",
            headers=_headers(),
            params=params,
            timeout=15,
        )
        r.raise_for_status()
        data = r.json()

    results = data.get("results", [])
    total = data.get("count", 0)
    label = correspondent_name or f"ID {correspondent_id}"

    if not results:
        return f"No documents found from correspondent '{label}'."

    lines = [f"{total} document{'s' if total != 1 else ''} from '{label}':"]
    for doc in results:
        created = doc.get("created", "")[:10] if doc.get("created") else "unknown"
        lines.append(f"  [{doc['id']}] {doc['title']} — {created}")

    return "\n".join(lines)


# ── Document Types ─────────────────────────────────────────────────────────────

@mcp.tool()
async def list_document_types() -> str:
    """List all document types in Paperless-NGX with their document counts and IDs.

    Use the IDs when calling update_document or get_documents_by_type.
    """
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{_BASE}/api/document_types/",
            headers=_headers(),
            params={"page_size": 100},
            timeout=15,
        )
        r.raise_for_status()
        data = r.json()

    types = data.get("results", [])
    if not types:
        return "No document types found."

    lines = [f"{len(types)} document type{'s' if len(types) != 1 else ''}:"]
    for t in types:
        lines.append(f"  [{t['id']}] {t['name']} ({t.get('document_count', 0)} docs)")

    return "\n".join(lines)


@mcp.tool()
async def get_documents_by_type(
    type_name: str = "", type_id: int = 0, limit: int = 10
) -> str:
    """Get documents of a specific document type in Paperless-NGX.

    Args:
        type_name: Name of the document type to filter by (partial match supported).
        type_id: Numeric ID of the document type (takes priority over type_name).
        limit: Maximum number of documents to return (default 10).
    """
    params: dict = {"page_size": limit, "ordering": "-created"}
    if type_id > 0:
        params["document_type__id"] = type_id
    elif type_name:
        params["document_type__name__icontains"] = type_name
    else:
        return "Provide either a document type name or ID."

    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{_BASE}/api/documents/",
            headers=_headers(),
            params=params,
            timeout=15,
        )
        r.raise_for_status()
        data = r.json()

    results = data.get("results", [])
    total = data.get("count", 0)
    label = type_name or f"ID {type_id}"

    if not results:
        return f"No documents found of type '{label}'."

    lines = [f"{total} document{'s' if total != 1 else ''} of type '{label}':"]
    for doc in results:
        created = doc.get("created", "")[:10] if doc.get("created") else "unknown"
        lines.append(f"  [{doc['id']}] {doc['title']} — {created}")

    return "\n".join(lines)


if __name__ == "__main__":
    mcp.settings.host = "0.0.0.0"
    mcp.settings.port = 8013
    mcp.run(transport="streamable-http")
