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

Runs on Pi (rasplient, 100.66.29.15) as systemd service `eip-platform.service`.

## Platform Layer
```
server.py          ← entry point (NOT platform.py — stdlib collision)
apps/<name>/
  __init__.py      ← Blueprint as `bp` + init_app(app)
  manifest.json    ← { name, url_prefix, description, version }
```
`server.py` auto-discovers every `apps/*/` directory, calls `init_app(app)`, registers `bp` at the manifest's `url_prefix`. Adding a new app = drop a folder, no platform changes needed.

Config: `.env` (gitignored). Runtime: `.venv/` (not system Python).

## Boundary Rule
Before adding code, ask: *"Would this exist if no apps were registered?"*
- Yes → platform layer (`server.py`)
- No → app Blueprint (`apps/<name>/`)

## Mirror App (`apps/mirror/`)

The most complex Blueprint — split into focused modules:

| File | What / Why |
|------|-----------|
| `__init__.py` | Blueprint routes (`/api/data`, static serving) + `init_app` that starts the poller |
| `poller.py` | Background thread, polls Notion every 60s, writes to `cache` singleton |
| `notion.py` | Raw Notion API calls (`_request`, `_query_db`, `_get_blocks`) — no parsing |
| `parsers.py` | Converts raw Notion responses to clean dicts (goals, events, mirror notes, mirror notes nudge extraction) |

**Data flow:** `poller.py` → calls `notion.py` → passes results to `parsers.py` → stores in `cache` → `__init__.py` serves `cache.get()` at `/mirror/api/data`.

**Why split:** parsers and Notion API calls change for different reasons. Separating them keeps each file testable and readable independently.

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
