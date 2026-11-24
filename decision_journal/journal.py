"""Decision journal: log decisions with their assumptions, review outcomes later, find patterns.

Data lives in ~/.ai-diy-projects/decisions.json (set DECISIONS_FILE to change it).
"""
import json
import os
from datetime import date, timedelta
from pathlib import Path

from common.claude import ask
from decision_journal.prompt import PATTERNS_SYSTEM, SHARPEN_SCHEMA, SHARPEN_SYSTEM
from common import storage

OUTCOMES = ["better", "as expected", "worse", "too early to tell"]
MIN_REVIEWED_FOR_PATTERNS = 3


def decisions_file() -> Path:
    return Path(os.environ.get("DECISIONS_FILE", Path.home() / ".ai-diy-projects" / "decisions.json")).expanduser()


def load() -> list[dict]:
    return storage.read_json("decisions", decisions_file())


def save(items: list[dict]) -> None:
    storage.write_json("decisions", decisions_file(), items)


def _check_date(value: str) -> str:
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError:
        raise ValueError(f"'{value}' isn't a date. Use YYYY-MM-DD, e.g. 2027-02-01.") from None


def log_decision(decision: str, context: str = "", options: str = "", expected: str = "",
                 confidence: int = 70, review_on: str = "", sharpen: bool = True) -> dict:
    """Save a decision. With sharpen=True, Claude pulls out hidden assumptions and review signals."""
    if not decision.strip():
        raise ValueError("Describe the decision.")
    if not 0 <= confidence <= 100:
        raise ValueError("Confidence must be between 0 and 100.")
    review_on = _check_date(review_on) if review_on else ""
    entry = {"decision": decision.strip(), "context": context.strip(), "options": options.strip(),
             "expected": expected.strip(), "confidence": confidence, "assumptions": [], "watch_for": [],
             "change_mind_if": "", "review_on": review_on}
    if sharpen:
        text = "\n".join(f"{k}: {v}" for k, v in entry.items() if v and k not in ("assumptions", "watch_for"))
        info = json.loads(ask(SHARPEN_SYSTEM, text, schema=SHARPEN_SCHEMA))
        entry["assumptions"] = info["assumptions"]
        entry["watch_for"] = info["watch_for"]
        entry["change_mind_if"] = info["change_mind_if"]
        if not review_on:
            days = min(max(info["suggested_review_days"], 7), 365)
            entry["review_on"] = (date.today() + timedelta(days=days)).isoformat()
    if not entry["review_on"]:
        entry["review_on"] = (date.today() + timedelta(days=90)).isoformat()
    items = load()
    entry.update(id=max((d["id"] for d in items), default=0) + 1, logged=date.today().isoformat(), review=None)
    items.append(entry)
    save(items)
    return entry


def get(decision_id: int) -> dict:
    for d in load():
        if d["id"] == decision_id:
            return d
    raise ValueError(f"No decision with id {decision_id}. Run 'list' to see ids.")


def record_review(decision_id: int, outcome: str, what_happened: str, assumptions_held: str = "",
                  lesson: str = "") -> dict:
    if outcome not in OUTCOMES:
        raise ValueError(f"Outcome must be one of: {', '.join(OUTCOMES)}")
    if not what_happened.strip():
        raise ValueError("Say briefly what happened.")
    items = load()
    for d in items:
        if d["id"] == decision_id:
            d["review"] = {"date": date.today().isoformat(), "outcome": outcome, "what_happened": what_happened.strip(),
                           "assumptions_held": assumptions_held.strip(), "lesson": lesson.strip()}
            save(items)
            return d
    raise ValueError(f"No decision with id {decision_id}.")


def due(items: list[dict], today: date | None = None) -> list[dict]:
    today = today or date.today()
    return [d for d in items if not d.get("review") and date.fromisoformat(d["review_on"]) <= today]


def find_patterns(items: list[dict]) -> str:
    """Ask Claude to look across reviewed decisions for patterns in how you decide."""
    reviewed = [d for d in items if d.get("review") and d["review"]["outcome"] != "too early to tell"]
    if len(reviewed) < MIN_REVIEWED_FOR_PATTERNS:
        raise ValueError(f"Review at least {MIN_REVIEWED_FOR_PATTERNS} decisions first "
                         f"(you have {len(reviewed)}). Patterns need a few data points.")
    slim = [{k: d[k] for k in ("id", "logged", "decision", "context", "options", "expected", "confidence",
                               "assumptions", "review")} for d in reviewed]
    pending = sum(1 for d in items if not d.get("review"))
    return ask(PATTERNS_SYSTEM, f"{len(slim)} reviewed decisions ({pending} not yet reviewed):\n"
               + json.dumps(slim, indent=1), effort="high")


SAMPLE = Path(__file__).parent / "examples" / "sample_decisions.json"


def load_samples() -> int:
    """Fill an empty journal with sample decisions so you can try 'patterns' straight away."""
    if load():
        raise ValueError(f"Your journal already has decisions, so the samples weren't added ({decisions_file()}).")
    items = json.loads(SAMPLE.read_text(encoding="utf-8"))
    save(items)
    return len(items)


def card(d: dict) -> str:
    lines = [f"### {d['id']}. {d['decision']}",
             f"Logged {d['logged']} · confidence {d['confidence']}% · review on {d['review_on']}"]
    for label, key in (("Context", "context"), ("Options considered", "options"), ("Expected", "expected")):
        if d.get(key):
            lines.append(f"**{label}:** {d[key]}")
    if d.get("assumptions"):
        lines += ["**Assumptions:**"] + [f"- {a}" for a in d["assumptions"]]
    if d.get("watch_for"):
        lines += ["**Signals to watch:**"] + [f"- {w}" for w in d["watch_for"]]
    if d.get("change_mind_if"):
        lines.append(f"**Would change my mind:** {d['change_mind_if']}")
    r = d.get("review")
    if r:
        lines += [f"**Reviewed {r['date']}: {r['outcome']}.** {r['what_happened']}"]
        if r.get("assumptions_held"):
            lines.append(f"**Assumptions:** {r['assumptions_held']}")
        if r.get("lesson"):
            lines.append(f"**Lesson:** {r['lesson']}")
    return "\n\n".join(lines)
