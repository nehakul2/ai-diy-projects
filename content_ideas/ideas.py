"""Research timely content ideas, keep an idea bank, and draft posts from saved ideas.

Idea bank: ~/.ai-diy-projects/ideas.json (set IDEAS_FILE to change it).
"""
import json
import os
from datetime import date
from pathlib import Path

from common.claude import WEB_SEARCH, ask
from content_ideas.prompt import DRAFT_SYSTEM, PLATFORMS, RESEARCH_SCHEMA, RESEARCH_SYSTEM


def ideas_file() -> Path:
    return Path(os.environ.get("IDEAS_FILE", Path.home() / ".ai-diy-projects" / "ideas.json")).expanduser()


def load() -> list[dict]:
    p = ideas_file()
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else []


def save(items: list[dict]) -> None:
    p = ideas_file()
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(items, indent=2), encoding="utf-8")
    tmp.replace(p)


SCORES = ("timeliness", "audience_fit", "originality")


def score(idea: dict) -> int:
    return sum(idea[k] for k in SCORES)


def research(niche: str, audience: str = "", platform: str = "LinkedIn", past_posts: str = "",
             count: int = 5, keep: bool = True) -> list[dict]:
    """Search the web and return `count` scored ideas, best first. Saves them to the idea bank if keep=True."""
    if not niche.strip():
        raise ValueError("Say what you create content about (your niche or topic).")
    if platform not in PLATFORMS:
        raise ValueError(f"Platform must be one of: {', '.join(PLATFORMS)}")
    if not 1 <= count <= 10:
        raise ValueError("Ask for between 1 and 10 ideas.")
    bank = load()
    parts = [f"Niche: {niche.strip()}", f"Platform: {platform}"]
    if audience.strip():
        parts.append(f"Audience: {audience.strip()}")
    if past_posts.strip():
        parts.append("Past posts (for voice and to avoid repeats):\n" + past_posts.strip()[:15000])
    if bank:
        parts.append("Already saved ideas (don't repeat):\n" + "\n".join(f"- {i['title']}" for i in bank[-40:]))
    system = RESEARCH_SYSTEM.format(today=f"{date.today():%d %B %Y}", count=count)
    tools = [dict(WEB_SEARCH, max_uses=6 + count)]
    found = json.loads(ask(system, "\n\n".join(parts), tools=tools, schema=RESEARCH_SCHEMA, effort="high"))["ideas"]
    for idea in found:  # keep each score in 1-5
        for k in SCORES:
            idea[k] = min(max(int(idea[k]), 1), 5)
    next_id = max((i["id"] for i in bank), default=0) + 1
    for n, idea in enumerate(sorted(found, key=score, reverse=True)):
        idea.update(id=next_id + n, score=score(idea), platform=platform, niche=niche.strip(),
                    found=date.today().isoformat(), status="new")
    if keep and found:
        save(bank + found)
    return sorted(found, key=lambda i: -i["score"])


def get(idea_id: int) -> dict:
    for i in load():
        if i["id"] == idea_id:
            return i
    raise ValueError(f"No idea with id {idea_id}. Run 'list' to see ids.")


def set_status(idea_id: int, status: str) -> dict:
    if status not in ("new", "drafted", "posted", "skipped"):
        raise ValueError("Status must be new, drafted, posted or skipped.")
    items = load()
    for i in items:
        if i["id"] == idea_id:
            i["status"] = status
            save(items)
            return i
    raise ValueError(f"No idea with id {idea_id}.")


def draft(idea_id: int, past_posts: str = "", platform: str = "") -> str:
    """Write a first draft for a saved idea. No web search; uses the idea, outline and source."""
    idea = get(idea_id)
    platform = platform or idea.get("platform", "LinkedIn")
    user = (f"Platform: {platform}\nIdea: {json.dumps({k: idea[k] for k in ('title', 'angle', 'why_now', 'source_url', 'format', 'outline')}, indent=1)}"
            + (f"\n\nMy past posts (match this voice):\n{past_posts.strip()[:15000]}" if past_posts.strip() else ""))
    text = ask(DRAFT_SYSTEM, user)
    if idea["status"] == "new":
        set_status(idea_id, "drafted")
    return text


def card(i: dict) -> str:
    link = f" ([source]({i['source_url']}))" if i.get("source_url", "").startswith("http") else ""
    lines = [f"### {i['id']}. {i['title']}",
             f"**Score {i['score']}/15** (timely {i['timeliness']}, fit {i['audience_fit']}, original "
             f"{i['originality']}) · {i['format']} for {i['platform']} · {i['status']}",
             f"**Angle:** {i['angle']}", f"**Why now:** {i['why_now']}{link}"]
    lines += ["**Outline:**"] + [f"- {b}" for b in i["outline"]]
    return "\n\n".join(lines[:4]) + "\n\n" + "\n".join(lines[4:])


def bank_table(items: list[dict], show_all: bool = False) -> str:
    rows = [i for i in items if show_all or i["status"] in ("new", "drafted")]
    if not rows:
        return "No ideas in the bank yet." if not items else "No open ideas. Add --all to see posted and skipped ones."
    lines = ["| Id | Idea | Score | Platform | Status | Found |", "|---|---|---|---|---|---|"]
    for i in sorted(rows, key=lambda i: (-i["score"], i["id"])):
        lines.append(f"| {i['id']} | {i['title']} | {i['score']} | {i['platform']} | {i['status']} | {i['found']} |")
    return "\n".join(lines)
