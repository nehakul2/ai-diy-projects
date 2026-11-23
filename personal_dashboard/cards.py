"""Collect the dashboard's contents: local cards from your other projects, plus a web briefing from Claude."""
import json
import os
from datetime import date, datetime, timedelta
from pathlib import Path

from common.claude import WEB_SEARCH, ask
from personal_dashboard.prompt import BRIEFING_SCHEMA, BRIEFING_SYSTEM

LOCAL_CARDS = ["calendar", "jobs", "decisions", "reading"]
DEFAULT_CONFIG = Path(__file__).parent / "examples" / "dashboard.json"


def data_dir() -> Path:
    return Path(os.environ.get("DASHBOARD_DIR", Path.home() / ".ai-diy-projects")).expanduser()


def load_config(path: str | Path | None = None) -> dict:
    """Read the dashboard settings. Relative calendar paths are relative to the current folder."""
    p = Path(path).expanduser() if path else data_dir() / "dashboard.json"
    if not p.is_file():
        if path:
            raise ValueError(f"Settings file not found: {p}")
        p = DEFAULT_CONFIG
    try:
        cfg = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(f"{p} isn't valid JSON: {e}") from None
    cfg.setdefault("name", "")
    cfg.setdefault("location", "")
    cfg.setdefault("topics", [])
    cfg.setdefault("questions", [])
    cfg.setdefault("calendar", "")
    cfg.setdefault("include", LOCAL_CARDS)
    if len(cfg["topics"]) > 6 or len(cfg["questions"]) > 5:
        raise ValueError("Keep it to 6 topics and 5 questions at most, so the dashboard stays quick.")
    return cfg


def save_config(cfg: dict) -> Path:
    p = data_dir() / "dashboard.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    return p


def calendar_card(path: str, today: date) -> list[str]:
    from life_admin_planner.calendar_ics import parse_ics
    p = Path(path).expanduser()
    if not p.is_file():
        return [f"Calendar file not found: {p}"]
    start = datetime.combine(today, datetime.min.time())
    events = [e for e in parse_ics(p.read_text(encoding="utf-8", errors="replace"))
              if e.start < start + timedelta(days=2) and e.end > start]
    lines = []
    for e in sorted(events, key=lambda e: e.start):
        day = "Today" if e.start.date() <= today else "Tomorrow"
        when = "all day" if e.all_day else f"{e.start:%H:%M}"
        lines.append(f"{day} {when}: {e.title}")
    return lines or ["Nothing in your calendar today or tomorrow."]


def jobs_card(today: date) -> list[str]:
    from job_search_tracker.store import load, urgency
    lines = []
    for j in load():
        u = urgency(j, today)
        if u:
            what = j.get("next_action") or "next step"
            lines.append(f"{'Overdue' if u == 'overdue' else 'Soon'}: {j.get('company', '')} {j.get('role', '')} "
                         f"({what})".strip())
    return lines or ["No job-search follow-ups due this week."]


def decisions_card(today: date) -> list[str]:
    from decision_journal.journal import due, load
    items = due(load(), today)
    return [f"Review: {d['decision']} (due {d['review_on']})" for d in items] or ["No decisions due for review."]


def reading_card() -> list[str]:
    from saved_content_organiser.library import find, load
    unread = find(load())
    if not unread:
        return ["Your saved-content library is all caught up."]
    mins = sum(i.get("minutes", 0) for i in unread)
    newest = unread[-1]
    return [f"{len(unread)} saved items to get to (about {mins} min).", f"Newest: {newest['title']}"]


def local_cards(cfg: dict, today: date | None = None) -> dict[str, list[str]]:
    """Cards built from your own data, with no API call."""
    today = today or date.today()
    makers = {"calendar": lambda: calendar_card(cfg["calendar"], today) if cfg.get("calendar") else None,
              "jobs": lambda: jobs_card(today), "decisions": lambda: decisions_card(today),
              "reading": reading_card}
    cards = {}
    for name in cfg["include"]:
        if name not in makers:
            continue
        try:
            lines = makers[name]()
        except Exception as e:  # a broken data file shouldn't break the whole dashboard
            lines = [f"Couldn't read this: {e}"]
        if lines:
            cards[name] = lines
    return cards


def web_briefing(cfg: dict, local: dict[str, list[str]], today: date | None = None) -> dict:
    """Weather, topic news and answers, found by Claude with web search."""
    today = today or date.today()
    if not (cfg["location"] or cfg["topics"] or cfg["questions"]):
        raise ValueError("Add a location, topics or questions to the settings for the web part of the dashboard.")
    user = json.dumps({"location": cfg["location"], "topics": cfg["topics"], "questions": cfg["questions"],
                       "local_items": local}, indent=1)
    tools = [dict(WEB_SEARCH, max_uses=4 + 2 * len(cfg["topics"]) + len(cfg["questions"]))]
    return json.loads(ask(BRIEFING_SYSTEM.format(today=f"{today:%A %d %B %Y}"), user, tools=tools,
                          schema=BRIEFING_SCHEMA))
