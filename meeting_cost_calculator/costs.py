"""Work out what recurring meetings cost, and what Claude's suggested changes would save.

All the maths happens here in plain Python. Claude only reads your meeting list and gives advice.
"""
import csv
import io
import json

from common.claude import ask
from meeting_cost_calculator.prompt import ADVICE_SCHEMA, ADVICE_SYSTEM, EXTRACT_SCHEMA, EXTRACT_SYSTEM

CSV_COLUMNS = ["title", "minutes", "attendees", "per_month"]


def _check(m: dict) -> dict:
    title = str(m.get("title", "")).strip() or "Untitled meeting"
    try:
        minutes, attendees, per_month = int(m["minutes"]), int(m["attendees"]), float(m["per_month"])
    except (KeyError, TypeError, ValueError):
        raise ValueError(f"'{title}': minutes, attendees and per_month must be numbers.") from None
    if minutes <= 0 or attendees <= 0 or per_month <= 0:
        raise ValueError(f"'{title}': minutes, attendees and per_month must be more than 0.")
    return {"title": title, "minutes": minutes, "attendees": attendees, "per_month": per_month,
            "purpose": m.get("purpose", ""), "notes": m.get("notes", "")}


def from_csv(text: str) -> list[dict]:
    """Read a CSV with columns title, minutes, attendees, per_month (purpose optional). No AI needed."""
    rows = list(csv.DictReader(io.StringIO(text.strip())))
    if not rows or not set(CSV_COLUMNS) <= set(rows[0]):
        raise ValueError(f"CSV needs a header row with: {', '.join(CSV_COLUMNS)} (purpose is optional).")
    return [_check(r) for r in rows]


def looks_like_csv(text: str) -> bool:
    first = text.strip().splitlines()[0].lower() if text.strip() else ""
    return all(c in first for c in CSV_COLUMNS)


def extract_meetings(text: str) -> list[dict]:
    """Use Claude to turn free text or a calendar export into a meeting list."""
    if not text.strip():
        raise ValueError("Describe your meetings, or give a CSV or calendar export.")
    if looks_like_csv(text):
        return from_csv(text)
    data = json.loads(ask(EXTRACT_SYSTEM, text[:60000], schema=EXTRACT_SCHEMA, effort="low"))
    if not data["meetings"]:
        raise ValueError("Couldn't find any meetings in that text.")
    return [_check(m) for m in data["meetings"]]


def monthly_cost(minutes: float, attendees: int, per_month: float, rate: float) -> float:
    return minutes / 60 * attendees * per_month * rate


def add_costs(meetings: list[dict], rate: float) -> list[dict]:
    if rate <= 0:
        raise ValueError("Hourly rate must be more than 0.")
    out = []
    for m in meetings:
        m = dict(m)
        m["hours_per_month"] = m["minutes"] / 60 * m["attendees"] * m["per_month"]
        m["cost_per_month"] = monthly_cost(m["minutes"], m["attendees"], m["per_month"], rate)
        m["cost_per_year"] = m["cost_per_month"] * 12
        out.append(m)
    return sorted(out, key=lambda m: -m["cost_per_month"])


def get_advice(meetings: list[dict], rate: float, context: str = "") -> dict:
    """Ask Claude for a verdict on each meeting, then work out the savings in code."""
    costed = add_costs(meetings, rate)
    slim = [{k: m[k] for k in ("title", "minutes", "attendees", "per_month", "purpose")}
            | {"cost_per_month": round(m["cost_per_month"])} for m in costed]
    user = (f"Team context: {context}\n\n" if context.strip() else "") + json.dumps(slim, indent=1)
    data = json.loads(ask(ADVICE_SYSTEM, user, schema=ADVICE_SCHEMA))
    by_title = {a["title"]: a for a in data["advice"]}
    for m in costed:
        a = by_title.get(m["title"]) or {"verdict": "keep", "suggested_minutes": m["minutes"],
                                         "suggested_attendees": m["attendees"], "reason": "", "tip": ""}
        new_minutes = max(0, min(a["suggested_minutes"], m["minutes"]))
        new_people = max(0, min(a["suggested_attendees"], m["attendees"]))
        if a["verdict"] in ("make async", "cancel"):
            new_minutes = new_people = 0
        new_cost = monthly_cost(new_minutes, new_people, m["per_month"], rate)
        m.update(verdict=a["verdict"], suggested_minutes=new_minutes, suggested_attendees=new_people,
                 reason=a["reason"], tip=a["tip"], saving_per_month=m["cost_per_month"] - new_cost,
                 hours_saved_per_month=m["hours_per_month"] - new_minutes / 60 * new_people * m["per_month"])
    return {"summary": data["summary"], "meetings": costed}


def money(x: float, currency: str = "$") -> str:
    return f"{currency}{x:,.0f}"


def report(meetings: list[dict], rate: float, currency: str = "$", summary: str = "") -> str:
    """Markdown report. Works with or without advice."""
    total_m = sum(m["cost_per_month"] for m in meetings)
    hours = sum(m["hours_per_month"] for m in meetings)
    advised = "verdict" in meetings[0] if meetings else False
    lines = [f"## Meeting costs at {money(rate, currency)}/hour per person", "",
             f"**{money(total_m, currency)} a month ({money(total_m * 12, currency)} a year)**, "
             f"{hours:,.0f} person-hours a month across {len(meetings)} meetings.", ""]
    if advised:
        saving = sum(m["saving_per_month"] for m in meetings)
        hours_saved = sum(m["hours_saved_per_month"] for m in meetings)
        lines += [f"**Suggested changes would save about {money(saving, currency)} a month "
                  f"({money(saving * 12, currency)} a year) and {hours_saved:,.0f} person-hours.**", ""]
        if summary:
            lines += [summary, ""]
    header = "| Meeting | Length | People | Per month | Cost / month |"
    sep = "|---|---|---|---|---|"
    if advised:
        header += " Suggestion | Saves / month |"
        sep += "---|---|"
    lines += [header, sep]
    for m in meetings:
        row = (f"| {m['title']} | {m['minutes']} min | {m['attendees']} | {m['per_month']:g} | "
               f"{money(m['cost_per_month'], currency)} |")
        if advised:
            change = {"shorten": f"shorten to {m['suggested_minutes']} min",
                      "fewer people": f"{m['suggested_attendees']} people"}.get(m["verdict"], m["verdict"])
            row += f" {change} | {money(m['saving_per_month'], currency)} |"
        lines.append(row)
    if advised:
        lines += ["", "### Why"]
        for m in meetings:
            if m.get("reason"):
                lines.append(f"- **{m['title']}** ({m['verdict']}): {m['reason']} *Tip:* {m['tip']}")
    guesses = [m for m in meetings if m.get("notes")]
    if guesses:
        lines += ["", "### Guesses to check"] + [f"- **{m['title']}**: {m['notes']}" for m in guesses]
    return "\n".join(lines)
