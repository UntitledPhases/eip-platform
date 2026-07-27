"""Smart Mirror — Flask Blueprint. Routes, static serving, local data API."""

from flask import Blueprint, jsonify, send_from_directory
import os

from .store import load_data

bp = Blueprint("mirror", __name__, static_folder=None)


def _cfg():
    return {
        "dist_path": os.environ.get(
            "MIRROR_DIST",
            os.path.join(os.path.expanduser("~"), "Smart-Mirror", "dist"),
        ),
        "data_file": os.environ.get(
            "MIRROR_DATA_FILE",
            os.path.join(os.path.expanduser("~"), "mirror-data", "mirror.json"),
        ),
    }


def init_app(app):
    cfg = _cfg()
    print(f"[mirror] Local data file: {cfg['data_file']}")


@bp.get("/api/data")
def mirror_data():
    return jsonify(load_data(_cfg()["data_file"]))


@bp.get("/")
@bp.get("/<path:filename>")
def mirror_static(filename="index.html"):
    return send_from_directory(_cfg()["dist_path"], filename)
