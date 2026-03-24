# CLAUDE.md — eip-platform

## Context Loading
Read these Notion pages before starting work (use Notion MCP):
- **Core Context:** `32c062d6840b81388422e7452c1c5437` — who the user is, interaction style, active goals
- **Handoff Notes:** `32c062d6840b81deb1b0f1037da6e57a` — where we left off per-topic

Load project-specific pages based on what's being worked on:
- Smart Mirror work → `32c062d6840b8105a80ad51d36bf6e92`
- EIP work → `324062d6840b818d8efce1c567a5861f`

## This Repo
Universal Flask application server with Blueprint auto-discovery. Zero app-specific code in the platform layer.

Entry point: `server.py` (NOT `platform.py` — stdlib name collision)
Apps live in `apps/<name>/` with `__init__.py` (Blueprint as `bp`) + optional `manifest.json`
Config: `.env` (gitignored, secrets live here)
Python: `.venv/` (Flask installed here, not system Python)
Runs on Pi (rasplient) as systemd service `eip-platform.service`

## Boundary Rule
Before adding code, ask: "Would this exist if no apps were registered?"
- Yes → platform layer (`server.py`)
- No → app Blueprint (`apps/<name>/`)

## Conventions
- Never name Python files after stdlib modules
- All secrets in `.env`, never hardcoded
- Apps are self-contained — own routes, own background tasks, own static serving
- Commit messages: short, imperative (`add weather endpoint`, `fix polling interval`)

## Working Style
- User skims — keep explanations short, give exact commands
- Ask before destructive changes
- If updating Notion after a session: write to Handoff Notes and relevant project doc
