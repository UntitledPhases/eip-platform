# CLAUDE.md — eip-platform

## What This Is
Universal Flask application server with Blueprint auto-discovery. The platform
layer owns Flask boot, env loading, shared error handlers, and app registration.
Every feature lives in a self-contained app Blueprint under `apps/`.

Runs on a Raspberry Pi as the `eip-platform.service` systemd service.

## Structure
```
server.py          ← entry point (NOT platform.py — stdlib collision)
apps/<name>/
  __init__.py      ← Blueprint as `bp` + optional init_app(app)
  manifest.json    ← { name, url_prefix, description, version }
```

`server.py` auto-discovers every `apps/*/` directory, calls `init_app(app)`,
and registers `bp` at the manifest's `url_prefix`. Both repo root and `apps/`
are on `sys.path` at boot. Adding a new app = drop a folder, no platform
changes needed.

Config: `.env` (gitignored). Runtime: `.venv/` (not system Python).

## Boundary Rules
Before adding code, ask: "Would this exist if no apps were registered?"

- Yes → `server.py` (platform)
- No, but reusable across apps → shared helper module
- No, app-specific → `apps/<name>/` (Blueprint)

## Mirror App (`apps/mirror/`)

Smart Mirror serves the Svelte kiosk build and a local JSON data API.

| File | What / Why |
|------|------------|
| `__init__.py` | Blueprint routes for static `dist/` and `/api/data` |
| `store.py` | Loads and normalizes local JSON from `MIRROR_DATA_FILE` |
| `mirror.example.json` | Example shape for the Pi-local data file |
| `mirror.empty.json` | Safe blank live-data starter |

Data flow:

`~/mirror-data/mirror.json` → `apps/mirror/store.py` →
`GET /mirror/api/data` → Smart-Mirror frontend store.

There is no Notion, Canvas, iCal, or background poller in the current mirror
path. Updating mirror content means pushing a new JSON file to the Pi. The app
loads the file per request, so data changes do not require restarting the Flask
service.

## EIP App (`apps/eip/`)

Wake-on-LAN + hub status. Single Blueprint, no background tasks.

## Env Vars (`.env`)
```
MIRROR_DIST        # path to Smart-Mirror/dist
MIRROR_DATA_FILE   # path to local mirror JSON, default ~/mirror-data/mirror.json
PLATFORM_HOST / PLATFORM_PORT / PLATFORM_DEBUG
EIP_HUB_IP / EIP_HUB_PORT / EIP_NC_TIMEOUT
```

## Test
```bash
python -m unittest discover -s tests -v
```

## Deploy Notes

- Backend code deploy: copy this repo to the Pi, preserving `.env` and `.venv`,
  then restart `eip-platform.service`.
- Mirror data deploy: copy a validated JSON file to
  `~/mirror-data/mirror.json`; no service restart needed.
- Frontend deploy: build `Smart-Mirror`, copy `dist/` to
  `~/Smart-Mirror/dist`, then refresh/restart the kiosk only if the
  browser does not pick up the new asset hash.

## Conventions

- Never name Python files after stdlib modules.
- All secrets in `.env`, never hardcoded.
- Apps are self-contained: own routes, own data sources, own static serving.
- Commit: short, imperative.
