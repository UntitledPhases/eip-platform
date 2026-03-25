"""Notion HTTP client — request building and pagination."""

import json
import urllib.request
import urllib.error
import os

API_BASE = "https://api.notion.com/v1"
API_VERSION = "2022-06-28"


class NotionClient:
    def __init__(self, token: str):
        if not token:
            raise RuntimeError("NOTION_TOKEN not set")
        self._headers = {
            "Authorization": f"Bearer {token}",
            "Notion-Version": API_VERSION,
            "Content-Type": "application/json",
        }

    def _request(self, method: str, path: str, data=None):
        url = f"{API_BASE}{path}"
        body = json.dumps(data).encode("utf-8") if data else None
        req = urllib.request.Request(url, data=body, headers=self._headers, method=method)
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def query_database(self, database_id: str, payload: dict | None = None) -> list:
        """Return all results from a database query (single page, up to 100)."""
        result = self._request("POST", f"/databases/{database_id}/query", payload or {})
        return result.get("results", [])

    def get_blocks(self, page_id: str, page_size: int = 50) -> list:
        """Return top-level child blocks for a page."""
        result = self._request("GET", f"/blocks/{page_id}/children?page_size={page_size}")
        return result.get("results", [])
