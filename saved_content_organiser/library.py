"""Your saved-content library, kept in one JSON file on your computer.

Default: ~/.ai-diy-projects/library.json. Set LIBRARY_FILE to use another file.
"""
import json
import os
import re
from collections import Counter
from datetime import date
from pathlib import Path

from common.claude import WEB_FETCH, ask
from saved_content_organiser.prompt import SCHEMA, SYSTEM
from common import storage

MAX_TEXT_CHARS = 20000
KINDS = ["article", "video", "podcast", "paper", "thread", "tool", "other"]


def library_file() -> Path:
    return Path(os.environ.get("LIBRARY_FILE", Path.home() / ".ai-diy-projects" / "library.json")).expanduser()


def load() -> list[dict]:
    return storage.read_json("library", library_file())


def save(items: list[dict]) -> None:
    storage.write_json("library", library_file(), items)


def tag_counts(items: list[dict]) -> Counter:
    return Counter(t for i in items for t in i.get("tags", []))


def _clean_tag(tag: str) -> str:
    return re.sub(r"[^a-z0-9-]+", "-", tag.lower()).strip("-")


def add_item(url: str = "", note: str = "", text: str = "", interests: str = "") -> dict:
    """Ask Claude to tag and summarise one item, then save it. Returns the saved item."""
    url, note, text = url.strip(), note.strip(), text.strip()
    if not (url or text or note):
        raise ValueError("Give a link, some pasted text, or a note.")
    if url and not re.match(r"https?://", url):
        raise ValueError("Links must start with http:// or https://")
    items = load()
    if url and any(i.get("url") == url for i in items):
        raise ValueError("That link is already in your library.")
    existing = ", ".join(t for t, _ in tag_counts(items).most_common(40)) or "(none yet)"
    parts = [f"Existing tags: {existing}"]
    if interests.strip():
        parts.append(f"My interests: {interests.strip()}")
    if url:
        parts.append(f"Link: {url}")
    if note:
        parts.append(f"Why I saved it / my notes: {note}")
    if text:
        parts.append(f"<pasted>\n{text[:MAX_TEXT_CHARS]}\n</pasted>")
    info = json.loads(ask(SYSTEM, "\n\n".join(parts), schema=SCHEMA, tools=[WEB_FETCH] if url else None))
    item = {
        "id": max((i["id"] for i in items), default=0) + 1,
        "title": info["title"], "url": url, "kind": info["kind"], "minutes": max(0, info["minutes"]),
        "tags": sorted({_clean_tag(t) for t in info["tags"] if _clean_tag(t)}),
        "summary": info["summary"], "why_it_matters": info["why_it_matters"], "my_note": note,
        "read_ok": info["read_ok"], "added": date.today().isoformat(), "done": False,
    }
    items.append(item)
    save(items)
    return item


def find(items: list[dict], tag: str = "", query: str = "", kind: str = "", include_done: bool = False) -> list[dict]:
    """Filter locally (no API call): by tag, kind and words in title/summary/notes."""
    words = query.lower().split()
    out = []
    for i in items:
        if i.get("done") and not include_done:
            continue
        if tag and _clean_tag(tag) not in i.get("tags", []):
            continue
        if kind and i.get("kind") != kind:
            continue
        hay = " ".join([i["title"], i["summary"], i["why_it_matters"], i.get("my_note", ""), " ".join(i["tags"])]).lower()
        if all(w in hay for w in words):
            out.append(i)
    return sorted(out, key=lambda i: i["id"], reverse=True)


def mark(item_id: int, done: bool = True, note: str | None = None, tags: list[str] | None = None) -> dict:
    items = load()
    for i in items:
        if i["id"] == item_id:
            i["done"] = done
            if note is not None:
                i["my_note"] = note
            if tags is not None:
                i["tags"] = sorted({_clean_tag(t) for t in tags if _clean_tag(t)})
            save(items)
            return i
    raise ValueError(f"No item with id {item_id}. Run 'list' to see ids.")


def card(i: dict) -> str:
    head = f"### {i['id']}. {i['title']}" + (" ✅" if i.get("done") else "")
    meta = f"{i['kind']}" + (f" · ~{i['minutes']} min" if i.get("minutes") else "") + " · " + " ".join(f"`{t}`" for t in i["tags"])
    lines = [head, meta]
    if i.get("url"):
        lines.append(i["url"])
    lines += ["", i["summary"], "", f"**Why it matters:** {i['why_it_matters']}"]
    if not i.get("read_ok", True):
        lines.append("_(Couldn't read the full content, so this is based on the title and your notes.)_")
    return "\n".join(lines)


def overview(items: list[dict]) -> str:
    if not items:
        return "Your library is empty."
    return "\n\n".join(card(i) for i in items)
