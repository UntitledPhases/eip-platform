"""
engine.notion — Reusable Notion HTTP client.

Any app that talks to Notion imports this. No app-specific logic here.
"""

import json
import urllib.request
import urllib.error

API_BASE    = "https://api.notion.com/v1"
API_VERSION = "2022-06-28"


class NotionClient:
    """Thin wrapper around the Notion REST API."""

    def __init__(self, token: str):
        if not token:
            raise RuntimeError("Notion token is required")
        self._headers = {
            "Authorization": f"Bearer {token}",
            "Notion-Version": API_VERSION,
            "Content-Type": "application/json",
        }

    def _request(self, method: str, path: str, data=None):
        url  = f"{API_BASE}{path}"
        body = json.dumps(data).encode("utf-8") if data else None
        req  = urllib.request.Request(url, data=body, headers=self._headers, method=method)
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def query_database(self, database_id: str, payload: dict | None = None) -> list:
        """Query a database. Returns result list (single page, up to 100)."""
        result = self._request("POST", f"/databases/{database_id}/query", payload or {})
        return result.get("results", [])

    def get_blocks(self, page_id: str, page_size: int = 50) -> list:
        """Return top-level child blocks for a page."""
        result = self._request("GET", f"/blocks/{page_id}/children?page_size={page_size}")
        return result.get("results", [])
