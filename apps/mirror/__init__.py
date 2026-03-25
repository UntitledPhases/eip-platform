"""Smart Mirror — Flask Blueprint. Routes, static serving, app init."""

from flask import Blueprint, jsonify, send_from_directory
import os

from .poller import cache, start as _start_poller

bp = Blueprint("mirror", __name__, static_folder=None)


def _cfg():
    return {
        "notion_token":     os.environ.get("NOTION_TOKEN", ""),
        "goals_db":         os.environ.get("MIRROR_GOALS_DB", "29e19e7bc7314ae88b81c25cc031a944"),
        "calendar_db":      os.environ.get("MIRROR_CALENDAR_DB", "cfebfb2302304968b183a6f16a4d2c21"),
        "notes_page":       os.environ.get("MIRROR_NOTES_PAGE", "32c062d6840b815589dfd964eb6d5e21"),
        "dist_path":        os.environ.get("MIRROR_DIST", os.path.join(os.path.expanduser("~"), "Smart-Mirror", "dist")),
        "poll_interval":    int(os.environ.get("MIRROR_POLL_INTERVAL", "60")),
    }


def init_app(app):
    cfg = _cfg()
    if cfg["notion_token"]:
        _start_poller(
            notion_token=cfg["notion_token"],
            goals_db=cfg["goals_db"],
            calendar_db=cfg["calendar_db"],
            notes_page=cfg["notes_page"],
            interval=cfg["poll_interval"],
        )
        print("[mirror] Notion polling started")


@bp.get("/api/data")
def mirror_data():
    return jsonify(cache.get())


@bp.get("/")
@bp.get("/<path:filename>")
def mirror_static(filename="index.html"):
    return send_from_directory(_cfg()["dist_path"], filename)
