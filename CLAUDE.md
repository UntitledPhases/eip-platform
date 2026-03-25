# CLAUDE.md — eip-platform

## Context Loading
Read these Notion pages before starting work (use Notion MCP):
- **Core Context:** `32c062d6840b81388422e7452c1c5437` — who the user is, interaction style, active goals
- **Handoff Notes:** `32c062d6840b81deb1b0f1037da6e57a` — where we left off per-topic

Load project-specific pages based on what's being worked on:
- Smart Mirror work → `32c062d6840b8105a80ad51d36bf6e92`
- EIP work → `324062d6840b818d8efce1c567a5861f`

## What This Is
Universal Flask application server with Blueprint auto-discovery. The platform layer has zero app-specific code — every feature lives in a self-contained app Blueprint under `apps/`.

The `engine/` layer holds reusable primitives (Notion client, polling cache, etc.) that any app can import. Apps wire engine modules together with app-specific config — they don't reimplement the plumbing.

Runs on Pi (rasplient, 100.66.29.15) as systemd service `eip-platform.service`.

## Structure
```
engine/            ← reusable primitives, no app-specific logic
  notion.py        ← NotionClient (HTTP client for Notion API)
  poller.py        ← PollingCache (generic background polling cache)
server.py          ← entry point (NOT platform.py — stdlib collision)
apps/<name>/
  __init__.py      ← Blueprint as `bp` + init_app(app)
  manifest.json    ← { name, url_prefix, description, version }
```
`server.py` auto-discovers every `apps/*/` directory, calls `init_app(app)`, registers `bp` at the manifest's `url_prefix`. Both `engine/` and `apps/` are on `sys.path` at boot. Adding a new app = drop a folder, no platform changes needed.

Config: `.env` (gitignored). Runtime: `.venv/` (not system Python).

## Boundary Rules
Before adding code, ask: *"Would this exist if no apps were registered?"*
- Yes → `server.py` (platform)
- No, but reusable across apps → `engine/` (primitive)
- No, app-specific → `apps/<name>/` (Blueprint)

## Engine Primitives (`engine/`)

| Module | What / Why |
|--------|-----------|
| `notion.py` | `NotionClient` — thin Notion REST wrapper. Any app talking to Notion imports this. |
| `poller.py` | `PollingCache` — generic background polling cache. Caller supplies a `fetch_fn`, cache handles threading, error capture, timestamps. |

**How to use PollingCache in a new app:**
```python
from engine.poller import PollingCache
from engine.notion import NotionClient

cache = PollingCache({"items": []})

def start(token, db_id, interval=60):
    client = NotionClient(token)
    cache.start(lambda: {"items": client.query_database(db_id)}, interval)
```

## Mirror App (`apps/mirror/`)

| File | What / Why |
|------|-----------|
| `__init__.py` | Blueprint routes + `init_app` that starts the poller |
| `poller.py` | Wires `engine.NotionClient` + `engine.PollingCache` to mirror's 3 data sources |
| `parsers.py` | Converts raw Notion pages/blocks → mirror dicts. Mirror-specific, stays in app. |

**Data flow:** `__init__.py` → `poller.start()` → `engine.PollingCache` calls `_fetch()` every 60s → `_fetch()` uses `engine.NotionClient` + `parsers` → result in `cache` → `/mirror/api/data` serves `cache.get()`.

## EIP App (`apps/eip/`)
Wake-on-LAN + hub status. Simpler — single `__init__.py`, no background tasks.

## Env Vars (`.env`)
```
NOTION_TOKEN
MIRROR_GOALS_DB         # Notion database ID
MIRROR_CALENDAR_DB      # Notion database ID
MIRROR_NOTES_PAGE       # Notion page ID (Mirror Notes)
MIRROR_DIST             # path to Smart-Mirror/dist
MIRROR_POLL_INTERVAL    # seconds (default 60)
PLATFORM_HOST / PLATFORM_PORT / PLATFORM_DEBUG
EIP_HUB_IP / EIP_HUB_PORT / EIP_NC_TIMEOUT
```

## Conventions
- Never name Python files after stdlib modules
- All secrets in `.env`, never hardcoded
- Apps are fully self-contained — own routes, own background threads, own static serving
- Notion API version pinned to `2022-06-28`
- Commit: short, imperative

## Working Style
- User skims — short answers, exact commands
- Ask before destructive changes
- After sessions: update Handoff Notes + relevant project doc in Notion
