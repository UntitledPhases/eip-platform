"""
engine.poller — Generic background polling cache.

Usage:
    cache = PollingCache(defaults={"items": [], "count": 0})
    cache.start(fetch_fn=my_fetch, interval=60)
    data = cache.get()

The caller supplies fetch_fn — a zero-argument callable that returns a dict.
PollingCache calls it every `interval` seconds, merges the result into its
state, and stamps last_updated / error automatically.
"""

import threading
import time
from datetime import datetime, timezone


class PollingCache:
    """Thread-safe cache driven by a caller-supplied fetch function."""

    def __init__(self, defaults: dict):
        self._defaults = dict(defaults)
        self._data     = {"last_updated": None, "error": None, **defaults}
        self._lock     = threading.Lock()
        self._thread: threading.Thread | None = None

    # ── Public ────────────────────────────────────────────────────────────────

    def get(self) -> dict:
        """Return a shallow copy of current cache state."""
        with self._lock:
            return dict(self._data)

    def start(self, fetch_fn, interval: int = 60) -> None:
        """Start background poll thread. Idempotent — safe to call multiple times."""
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(
            target=self._loop,
            args=(fetch_fn, interval),
            daemon=True,
        )
        self._thread.start()

    # ── Internal ──────────────────────────────────────────────────────────────

    def _loop(self, fetch_fn, interval: int):
        while True:
            try:
                result = fetch_fn()
                with self._lock:
                    self._data.update(result)
                    self._data["last_updated"] = datetime.now(timezone.utc).isoformat()
                    self._data["error"]        = None
            except Exception as exc:
                with self._lock:
                    self._data["error"]        = str(exc)
                    self._data["last_updated"] = datetime.now(timezone.utc).isoformat()
            time.sleep(interval)
