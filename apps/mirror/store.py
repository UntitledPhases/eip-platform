"""Local JSON storage for the Smart Mirror API.

The frontend contract intentionally stays small:
    {
      "goals": [...],
      "calendar": [...],
      "mirror_notes": [...],
      "last_updated": "...",
      "error": null
    }

Updates happen outside the app by copying a new JSON file onto the Pi. The app
loads the file on each request, so no background poller or external service is
needed.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EMPTY_DATA = {
    "goals": [],
    "calendar": [],
    "mirror_notes": [],
    "last_updated": None,
    "error": None,
}


def load_data(path: str | Path) -> dict[str, Any]:
    """Load, normalize, and return mirror data from a local JSON file."""
    data_path = Path(path).expanduser()
    if not data_path.exists():
        return {
            **EMPTY_DATA,
            "error": f"Mirror data file not found: {data_path}",
        }

    try:
        raw = json.loads(data_path.read_text(encoding="utf-8"))
        data = normalize_data(raw)
        if data.get("last_updated") is None:
            data["last_updated"] = _mtime_iso(data_path)
        return data
    except Exception as exc:
        return {
            **EMPTY_DATA,
            "last_updated": _now_iso(),
            "error": f"Could not load mirror data: {exc}",
        }


def normalize_data(raw: Any) -> dict[str, Any]:
    """Return a frontend-safe data shape from arbitrary JSON-ish input."""
    if not isinstance(raw, dict):
        raise ValueError("top-level JSON must be an object")

    return {
        "goals": [_normalize_goal(item) for item in _list(raw.get("goals"))],
        "calendar": [_normalize_event(item) for item in _list(raw.get("calendar"))],
        "mirror_notes": [str(item) for item in _list(raw.get("mirror_notes")) if str(item).strip()],
        "last_updated": raw.get("last_updated"),
        "error": raw.get("error"),
    }


def _normalize_goal(item: Any) -> dict[str, Any]:
    if not isinstance(item, dict):
        item = {"goal": str(item)}
    return {
        "id": _str(item.get("id")),
        "goal": _str(item.get("goal")),
        "status": item.get("status"),
        "priority": item.get("priority"),
        "horizon": item.get("horizon") or "Daily",
        "category": item.get("category"),
        "target": _date_range(item.get("target")),
        "notes": _str(item.get("notes")),
    }


def _normalize_event(item: Any) -> dict[str, Any]:
    if not isinstance(item, dict):
        item = {"event": str(item)}
    return {
        "id": _str(item.get("id")),
        "event": _str(item.get("event")),
        "status": item.get("status"),
        "priority": item.get("priority"),
        "type": item.get("type"),
        "when": _date_range(item.get("when")),
        "location": _str(item.get("location")),
        "notes": _str(item.get("notes")),
        "days": [str(day) for day in _list(item.get("days"))],
        "start_time": _str(item.get("start_time")),
        "end_time": _str(item.get("end_time")),
    }


def _date_range(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {"start": None, "end": None}
    return {
        "start": value.get("start"),
        "end": value.get("end"),
    }


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _str(value: Any) -> str:
    return "" if value is None else str(value)


def _mtime_iso(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
