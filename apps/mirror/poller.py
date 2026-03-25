"""
Mirror-specific poller — wires engine primitives to mirror's data shape.

Imports NotionClient and PollingCache from the engine layer, then supplies
the mirror-specific fetch function (which databases to query, which parsers
to run). Nothing in here is reusable across apps.
"""

from engine.notion import NotionClient
from engine.poller import PollingCache
from .parsers import parse_goal, parse_event, parse_mirror_notes

_DEFAULTS = {"goals": [], "calendar": [], "mirror_notes": []}
cache = PollingCache(_DEFAULTS)


def start(notion_token: str, goals_db: str, calendar_db: str,
          notes_page: str, interval: int = 60) -> None:
    """Configure and start the mirror poll loop."""
    client = NotionClient(notion_token)

    def _fetch() -> dict:
        goals    = [parse_goal(p)  for p in client.query_database(goals_db)]
        calendar = [parse_event(p) for p in client.query_database(calendar_db)]
        try:
            notes = parse_mirror_notes(client.get_blocks(notes_page))
        except Exception:
            notes = []
        return {"goals": goals, "calendar": calendar, "mirror_notes": notes}

    cache.start(_fetch, interval)
