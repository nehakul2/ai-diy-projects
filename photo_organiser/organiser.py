"""Plan, preview, apply and undo sorting photos into one folder per event.

Safety rules (the same as the downloads organiser, whose move and undo code this reuses):
- Only files directly inside the folder are touched. Nothing is deleted or overwritten.
- Files keep their names; they only move into new event folders inside the same folder.
- Every applied plan writes an undo log.
- Sent to Claude: dates, photo counts, a few file names, GPS rounded to about 1 km, and
  (unless you turn it off) 3 small thumbnails per event. Never the full photos.
"""
import json
from collections import defaultdict
from pathlib import Path

from common.claude import ask
from downloads_organiser.organiser import BAD_CHARS, _taken, apply_plan, undo  # noqa: F401 (re-exported)
from photo_organiser.photos import Event, group_events, samples, scan, thumbnail_b64
from photo_organiser.prompt import NAME_SCHEMA, NAME_SYSTEM

BATCH = 15


def _describe(e: Event) -> str:
    loc = e.location()
    names = [p.path.name for p in e.photos]
    shown = names if len(names) <= 4 else names[:2] + ["..."] + names[-2:]
    return (f"Event {e.number}: {e.start:%a %d %b %Y %H:%M} to {e.end:%a %d %b %Y %H:%M}, {len(e.photos)} files"
            + (f", GPS about {loc[0]}, {loc[1]}" if loc else ", no GPS") + f". Files: {', '.join(shown)}")


def name_events(events: list[Event], thumbnails: bool = True) -> None:
    """Ask Claude to name each event (fills in event.name, place, confident)."""
    for i in range(0, len(events), BATCH):
        batch = events[i:i + BATCH]
        blocks: list[dict] = [{"type": "text", "text": f"{len(batch)} events to name."}]
        for e in batch:
            blocks.append({"type": "text", "text": _describe(e)})
            if thumbnails:
                for path in samples(e):
                    data = thumbnail_b64(path)
                    if data:
                        blocks.append({"type": "image",
                                       "source": {"type": "base64", "media_type": "image/jpeg", "data": data}})
        result = json.loads(ask(NAME_SYSTEM, blocks, schema=NAME_SCHEMA, effort="low"))
        by_number = {r["number"]: r for r in result["events"]}
        for e in batch:
            r = by_number.get(e.number)
            if r:
                e.name, e.place, e.confident = r["name"], r["place"], r["confident"]


def _clean(name: str) -> str:
    name = BAD_CHARS.sub("", name).strip(" .")
    return name[:60] or "Photos"


def make_plan(folder: str, gap_hours: float = 6, min_photos: int = 3, use_ai: bool = True,
              thumbnails: bool = True) -> dict:
    """Scan, group and (optionally) name events. Returns a plan for apply_plan(). Moves nothing."""
    root = Path(folder).expanduser().resolve()
    photos = scan(root)
    events = group_events(photos, gap_hours)
    big = [e for e in events if len(e.photos) >= min_photos]
    small = [e for e in events if len(e.photos) < min_photos]
    if use_ai and big:
        name_events(big, thumbnails)
    plan_events, used = [], set()
    for e in big:
        title = f"{e.dates()} {_clean(e.name)}" if e.name else e.dates()
        base, n = title, 2
        while title.lower() in used or ((root / title).exists() and not (root / title).is_dir()):
            title = f"{base} ({n})"
            n += 1
        used.add(title.lower())
        plan_events.append({"folder": title, "photos": [p.path.name for p in e.photos], "place": e.place,
                            "guess": bool(e.name) and not e.confident})
    leftovers: dict[str, list[str]] = defaultdict(list)
    for e in small:
        leftovers[f"{e.start:%Y-%m} Other photos"] += [p.path.name for p in e.photos]
    for title, names in sorted(leftovers.items()):
        plan_events.append({"folder": title, "photos": names, "place": "", "guess": False})
    moves, warnings = [], []
    for pe in plan_events:
        for name in pe["photos"]:
            if _taken(root / pe["folder"] / name):
                warnings.append(f"Skipping '{name}': '{pe['folder']}/{name}' already exists.")
                continue
            moves.append({"current": name, "folder": pe["folder"], "new_name": name})
    sources = defaultdict(int)
    for p in photos:
        sources[p.source] += 1
    notes = [f"{len(photos)} files, {len(events)} groups ({len(big)} events of {min_photos}+ photos)."]
    if sources.get("file date"):
        notes.append(f"{sources['file date']} files had no camera date or date in the name, so their file date was "
                     "used. That can be wrong for copied files.")
    return {"folder": str(root), "events": plan_events, "moves": moves, "warnings": warnings, "notes": notes,
            "folders": [pe["folder"] for pe in plan_events]}


def plan_to_markdown(plan: dict) -> str:
    lines = [f"## Plan for {plan['folder']}", ""] + [f"- {n}" for n in plan["notes"]] + [""]
    for pe in plan["events"]:
        place = f" · {pe['place']}" if pe["place"] else ""
        guess = " · _name is a guess_" if pe["guess"] else ""
        shown = pe["photos"] if len(pe["photos"]) <= 5 else pe["photos"][:3] + [f"... and {len(pe['photos']) - 3} more"]
        lines += [f"### 📁 {pe['folder']}", f"{len(pe['photos'])} file{'s' if len(pe['photos']) != 1 else ''}{place}{guess}", "", ", ".join(shown), ""]
    if plan["warnings"]:
        lines += ["**Skipped:**"] + [f"- {w}" for w in plan["warnings"]]
    return "\n".join(lines)


def preview(folder: str, **kwargs) -> str:
    return plan_to_markdown(make_plan(folder, **kwargs))
