"""
EIP Platform — Universal Flask Application Server

BOUNDARY RULES:
Platform owns: Flask boot, env loading, Blueprint discovery, shared middleware.
Apps own: All routes, business logic, data fetching, background tasks, static files.

Attribution test: "Would this code need to exist if no apps were registered?"
  Yes → Platform.  No → App Blueprint.
"""

from flask import Flask, jsonify
from datetime import datetime, timezone
import importlib
import os
import sys


def load_env(path=None):
    if path is None:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if not os.path.exists(path):
        return
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            os.environ.setdefault(key, value)


def create_app():
    load_env()
    app = Flask(__name__)
    _registered_apps = {}

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "not found"}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "internal server error"}), 500

    app_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "apps")

    if os.path.isdir(app_dir):
        if app_dir not in sys.path:
            sys.path.insert(0, app_dir)

        for name in sorted(os.listdir(app_dir)):
            init = os.path.join(app_dir, name, "__init__.py")
            if not os.path.isfile(init):
                continue

            prefix = f"/{name}"
            manifest = os.path.join(app_dir, name, "manifest.json")
            if os.path.isfile(manifest):
                import json
                with open(manifest) as f:
                    app_meta = json.load(f)
                prefix = app_meta.get("url_prefix", prefix)

            try:
                module = importlib.import_module(name)
                bp = getattr(module, "bp", None) or getattr(module, "blueprint", None)
                if bp is None:
                    print(f"[platform] SKIP {name}: no 'bp' or 'blueprint' found")
                    continue

                app.register_blueprint(bp, url_prefix=prefix)
                _registered_apps[name] = prefix

                init_fn = getattr(module, "init_app", None)
                if callable(init_fn):
                    init_fn(app)

                print(f"[platform] Registered: {name} → {prefix}")
            except Exception as e:
                print(f"[platform] FAILED to load {name}: {e}")

    app._registered_apps = _registered_apps

    @app.get("/health")
    def health():
        return jsonify({
            "status": "ok",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "apps": {name: prefix for name, prefix in app._registered_apps.items()},
        })

    return app


if __name__ == "__main__":
    app = create_app()
    host = os.environ.get("PLATFORM_HOST", "0.0.0.0")
    port = int(os.environ.get("PLATFORM_PORT", "5000"))
    debug = os.environ.get("PLATFORM_DEBUG", "false").lower() == "true"
    app.run(host=host, port=port, debug=debug)
