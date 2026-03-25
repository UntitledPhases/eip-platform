"""Background Notion poller + in-memory cache."""

import threading
import time
import os
from datetime import datetime, timezone

from .notion import NotionClient
from .parsers import parse_goal, parse_event, parse_mirror_notes


class DataCache:
    """Thread-safe cache populated by a background Notion poll loop."""

    _EMPTY = {"goals": [], "calendar": [], "mirror_notes": [], "last_updated": None, "error": None}

    def __init__(self):
        self._data = dict(self._EMPTY)
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None

    # ── Public API ────────────────────────────────────────────────────────────

    def get(self) -> dict:
        with self._lock:
            return dict(self._data)

    def start(self, notion_token: str, goals_db: str, calendar_db: str,
              notes_page: str, interval: int) -> None:
        """Start the background poll thread (idempotent — safe to call twice)."""
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(
            target=self._loop,
            args=(notion_token, goals_db, calendar_db, notes_page, interval),
            daemon=True,
        )
        self._thread.start()

    # ── Internal ──────────────────────────────────────────────────────────────

    def _poll(self, client: NotionClient, goals_db: str, calendar_db: str, notes_page: str):
        goals = [parse_goal(p) for p in client.query_database(goals_db)]
        calendar = [parse_event(p) for p in client.query_database(calendar_db)]
        try:
            notes = parse_mirror_notes(client.get_blocks(notes_page))
        except Exception:
            notes = []
        with self._lock:
            self._data.update({
                "goals": goals,
                "calendar": calendar,
                "mirror_notes": notes,
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "error": None,
            })

    def _loop(self, token: str, goals_db: str, calendar_db: str,
              notes_page: str, interval: int):
        client = NotionClient(token)
        while True:
            try:
                self._poll(client, goals_db, calendar_db, notes_page)
            except Exception as exc:
                with self._lock:
                    self._data["error"] = str(exc)
                    self._data["last_updated"] = datetime.now(timezone.utc).isoformat()
            time.sleep(interval)


# Module-level singleton — imported by __init__.py
cache = DataCache()
