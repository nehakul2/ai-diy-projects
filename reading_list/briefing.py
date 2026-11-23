"""Summarise a reading list and write a script to listen to."""
import json
import re

from common.claude import WEB_FETCH, ask
from reading_list.prompt import BRIEFING_SCHEMA, BRIEFING_SYSTEM

MAX_ITEMS = 10
WORDS_PER_MINUTE = 150
URL_RE = re.compile(r"https?://[^\s<>\"')\]]+")


def parse_list(text: str) -> tuple[list[str], str]:
    """Split input into URLs and any remaining pasted text (for articles that can't be fetched)."""
    urls = list(dict.fromkeys(u.rstrip(".,;") for u in URL_RE.findall(text)))
    rest = URL_RE.sub("", text)
    rest = "\n".join(line for line in rest.splitlines() if re.search(r"\w", line)).strip()
    return urls, rest


def from_library(limit: int = 5) -> str:
    """Unread articles from the saved-content organiser (project 9), newest first."""
    from saved_content_organiser.library import find, load
    items = [i for i in find(load()) if i.get("url") and i.get("kind") in ("article", "other", "")]
    if not items:
        raise ValueError("No unread articles with links in your saved-content library.")
    return "\n".join(i["url"] for i in items[::-1][:limit])


def make_briefing(text: str, minutes: int = 3) -> dict:
    """Return {"items": [...], "script": "..."} for the URLs and/or pasted text in `text`."""
    urls, rest = parse_list(text)
    if not urls and not rest:
        raise ValueError("Add some links (one per line) or paste the text of an article.")
    if len(urls) > MAX_ITEMS:
        raise ValueError(f"That's {len(urls)} links. Keep it to {MAX_ITEMS} or fewer per briefing.")
    if not 1 <= minutes <= 15:
        raise ValueError("Choose a briefing length between 1 and 15 minutes.")
    parts = []
    if urls:
        parts.append("Links:\n" + "\n".join(urls))
    if rest:
        parts.append("Pasted text (treat as one or more articles):\n" + rest[:40000])
    system = BRIEFING_SYSTEM.format(minutes=minutes, words=minutes * WORDS_PER_MINUTE)
    tools = [dict(WEB_FETCH, max_uses=len(urls) + 2)] if urls else None
    result = json.loads(ask(system, "\n\n".join(parts), tools=tools, schema=BRIEFING_SCHEMA))
    if not result["items"]:
        raise ValueError("Couldn't summarise anything from that list.")
    return result


def to_markdown(briefing: dict) -> str:
    lines = ["## Your reading list"]
    for n, i in enumerate(briefing["items"], 1):
        title = f"[{i['title']}]({i['url']})" if i["url"] else i["title"]
        lines += ["", f"### {n}. {title}", f"**{i['verdict'].capitalize()}.** {i['why']}"]
        lines += [f"- {p}" for p in i["points"]]
        if not i["read_ok"]:
            lines.append("_Couldn't read the page, so this is based on the title only._")
    words = len(briefing["script"].split())
    lines += ["", f"## Spoken briefing (about {max(1, round(words / WORDS_PER_MINUTE))} min)", "", briefing["script"]]
    return "\n".join(lines)
