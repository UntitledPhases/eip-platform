"""Pure data-model parsers — Notion API response → Python dicts. No side effects."""


# ── Property extractors ──────────────────────────────────────────────────────

def _text(prop) -> str:
    if not prop:
        return ""
    entries = prop.get("title") or prop.get("rich_text") or []
    return "".join(t.get("plain_text", "") for t in entries)

def _select(prop) -> str | None:
    if not prop:
        return None
    sel = prop.get("select")
    return sel.get("name") if sel else None

def _status(prop) -> str | None:
    if not prop:
        return None
    sel = prop.get("status")
    return sel.get("name") if sel else None

def _date(prop) -> dict | None:
    if not prop:
        return None
    d = prop.get("date")
    if not d:
        return None
    return {"start": d.get("start"), "end": d.get("end")}

def _multiselect(prop) -> list:
    if not prop:
        return []
    return [o.get("name") for o in prop.get("multi_select", [])]


# ── Record parsers ───────────────────────────────────────────────────────────

def parse_goal(page: dict) -> dict:
    p = page.get("properties", {})
    return {
        "id": page["id"],
        "goal": _text(p.get("Goal")),
        "status": _status(p.get("Status")),
        "priority": _select(p.get("Priority")),
        "horizon": _select(p.get("Horizon")),
        "category": _select(p.get("Category")),
        "target": _date(p.get("Target")),
        "notes": _text(p.get("Notes")),
    }


def parse_event(page: dict) -> dict:
    p = page.get("properties", {})
    return {
        "id": page["id"],
        "event": _text(p.get("Event")),
        "status": _status(p.get("Status")),
        "priority": _select(p.get("Priority")),
        "type": _select(p.get("Type")),
        "when": _date(p.get("When")),
        "location": _text(p.get("Location")),
        "notes": _text(p.get("Notes")),
        "days": _multiselect(p.get("Days")),
        "start_time": _text(p.get("Start Time")),
        "end_time": _text(p.get("End Time")),
    }


def parse_mirror_notes(blocks: list) -> list:
    """Extract bullet items under the 'Active Nudges' heading."""
    notes = []
    in_section = False
    for block in blocks:
        btype = block.get("type")
        if btype in ("heading_1", "heading_2", "heading_3"):
            rt = block.get(btype, {}).get("rich_text", [])
            heading = "".join(t.get("plain_text", "") for t in rt).strip()
            in_section = (heading == "Active Nudges")
            continue
        if in_section and btype in ("bulleted_list_item", "numbered_list_item", "to_do"):
            rt = block.get(btype, {}).get("rich_text", [])
            text = "".join(t.get("plain_text", "") for t in rt).strip()
            if text:
                notes.append(text)
    return notes
