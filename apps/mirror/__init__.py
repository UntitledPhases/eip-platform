"""Smart Mirror — Flask Blueprint. All mirror routes, Notion polling, static serving."""

from flask import Blueprint, jsonify, send_from_directory
from datetime import datetime, timezone
import threading
import time
import os
import json
import urllib.request
import urllib.error

bp = Blueprint("mirror", __name__, static_folder=None)

NOTION_API = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"
_config = {}

def _get_config():
    if _config:
        return _config
    _config.update({
        "notion_token": os.environ.get("NOTION_TOKEN", ""),
        "goals_db_id": os.environ.get("MIRROR_GOALS_DB", "29e19e7bc7314ae88b81c25cc031a944"),
        "calendar_db_id": os.environ.get("MIRROR_CALENDAR_DB", "cfebfb2302304968b183a6f16a4d2c21"),
        "mirror_notes_page_id": os.environ.get("MIRROR_NOTES_PAGE", "32c062d6840b815589dfd964eb6d5e21"),
        "dist_path": os.environ.get("MIRROR_DIST", os.path.join(os.path.expanduser("~"), "Smart-Mirror", "dist")),
        "poll_interval": int(os.environ.get("MIRROR_POLL_INTERVAL", "60")),
    })
    return _config

_cache = {"goals": [], "calendar": [], "mirror_notes": [], "last_updated": None, "error": None}
_cache_lock = threading.Lock()

def _notion_request(method, path, data=None):
    cfg = _get_config()
    token = cfg["notion_token"]
    if not token:
        raise RuntimeError("NOTION_TOKEN not set")
    url = f"{NOTION_API}{path}"
    headers = {"Authorization": f"Bearer {token}", "Notion-Version": NOTION_VERSION, "Content-Type": "application/json"}
    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))

def _notion_query(database_id, payload=None):
    return _notion_request("POST", f"/databases/{database_id}/query", payload or {})

def _notion_get_blocks(page_id):
    return _notion_request("GET", f"/blocks/{page_id}/children?page_size=50")

def _extract_text(prop):
    if not prop: return ""
    entries = prop.get("title") or prop.get("rich_text") or []
    return "".join(t.get("plain_text", "") for t in entries)

def _extract_select(prop):
    if not prop: return None
    sel = prop.get("select")
    return sel.get("name") if sel else None

def _extract_status(prop):
    if not prop: return None
    sel = prop.get("status")
    return sel.get("name") if sel else None

def _extract_date(prop):
    if not prop: return None
    d = prop.get("date")
    if not d: return None
    return {"start": d.get("start"), "end": d.get("end")}

def _parse_goal(page):
    p = page.get("properties", {})
    return {"id": page["id"], "goal": _extract_text(p.get("Goal")), "status": _extract_status(p.get("Status")), "priority": _extract_select(p.get("Priority")), "horizon": _extract_select(p.get("Horizon")), "category": _extract_select(p.get("Category")), "target": _extract_date(p.get("Target")), "notes": _extract_text(p.get("Notes"))}

def _parse_event(page):
    p = page.get("properties", {})
    return {"id": page["id"], "event": _extract_text(p.get("Event")), "status": _extract_status(p.get("Status")), "priority": _extract_select(p.get("Priority")), "type": _extract_select(p.get("Type")), "when": _extract_date(p.get("When")), "location": _extract_text(p.get("Location")), "notes": _extract_text(p.get("Notes"))}

def _parse_mirror_notes(blocks_response):
    notes = []
    text_types = ("paragraph", "bulleted_list_item", "numbered_list_item", "heading_1", "heading_2", "heading_3", "to_do", "callout", "quote")
    for block in blocks_response.get("results", []):
        btype = block.get("type")
        if btype not in text_types: continue
        rich_text = block.get(btype, {}).get("rich_text", [])
        text = "".join(t.get("plain_text", "") for t in rich_text)
        if text.strip(): notes.append(text.strip())
    return notes

def _poll_notion():
    cfg = _get_config()
    try:
        goals = [_parse_goal(p) for p in _notion_query(cfg["goals_db_id"]).get("results", [])]
        calendar = [_parse_event(p) for p in _notion_query(cfg["calendar_db_id"]).get("results", [])]
        try:
            mirror_notes = _parse_mirror_notes(_notion_get_blocks(cfg["mirror_notes_page_id"]))
        except Exception:
            mirror_notes = []
        with _cache_lock:
            _cache["goals"] = goals
            _cache["calendar"] = calendar
            _cache["mirror_notes"] = mirror_notes
            _cache["last_updated"] = datetime.now(timezone.utc).isoformat()
            _cache["error"] = None
    except Exception as exc:
        with _cache_lock:
            _cache["error"] = str(exc)
            _cache["last_updated"] = datetime.now(timezone.utc).isoformat()

def _poll_loop():
    cfg = _get_config()
    while True:
        _poll_notion()
        time.sleep(cfg["poll_interval"])

_poll_thread_started = False

def init_app(app):
    global _poll_thread_started
    cfg = _get_config()
    if cfg["notion_token"] and not _poll_thread_started:
        t = threading.Thread(target=_poll_loop, daemon=True)
        t.start()
        _poll_thread_started = True
        print("[mirror] Notion polling started")

@bp.get("/api/data")
def mirror_data():
    with _cache_lock:
        return jsonify(_cache)

@bp.get("/")
@bp.get("/<path:filename>")
def mirror_static(filename="index.html"):
    cfg = _get_config()
    return send_from_directory(cfg["dist_path"], filename)
