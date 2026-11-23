"""Weekly life-admin planner: flag calendar clashes and pick three realistic priorities.

Usage:
    python -m life_admin_planner.main --calendar calendar.ics --tasks tasks.txt
    python -m life_admin_planner.main --calendar week.txt --tasks tasks.txt     # pasted calendar text
    python -m life_admin_planner.main --calendar calendar.ics --tasks tasks.txt --week-start 2026-11-30
"""
import argparse
import sys
from datetime import date, timedelta
from pathlib import Path

from common.claude import ask
from life_admin_planner.calendar_ics import clashes, in_week, parse_ics
from life_admin_planner.prompt import SYSTEM


def next_monday(today: date | None = None) -> date:
    today = today or date.today()
    return today if today.weekday() == 0 else today + timedelta(days=7 - today.weekday())


def calendar_snapshot(calendar_text: str, week_start: date) -> tuple[str, list[str]]:
    """Turn .ics text into a readable list plus code-detected clashes; pass plain text through."""
    if "BEGIN:VCALENDAR" not in calendar_text:
        return calendar_text.strip(), []
    events = in_week(parse_ics(calendar_text), week_start)
    lines = [e.describe() for e in events] or ["(no events this week)"]
    found = [f"{a.describe()}  overlaps  {b.describe()}" for a, b in clashes(events)]
    if any(e.repeats for e in events):
        lines.append("(Note: repeating events are only shown on their first date.)")
    return "\n".join(lines), found


def plan_week(calendar_text: str, tasks: str, week_start: date | None = None, notes: str = "") -> str:
    """Plan the week and return Markdown. Used by the CLI and the test page."""
    if not tasks.strip():
        raise ValueError("Add at least a few tasks.")
    week_start = week_start or next_monday()
    snapshot, found = calendar_snapshot(calendar_text, week_start)
    parts = [f"Week starting {week_start:%A %d %B %Y}.", f"<calendar>\n{snapshot or '(no calendar given)'}\n</calendar>"]
    if found:
        parts.append("<detected_clashes>\n" + "\n".join(found) + "\n</detected_clashes>")
    parts.append(f"<tasks>\n{tasks.strip()}\n</tasks>")
    if notes.strip():
        parts.append(f"Notes: {notes.strip()}")
    return ask(SYSTEM, "\n\n".join(parts))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--calendar", help="An .ics export, or a text file listing your week.")
    parser.add_argument("--tasks", required=True, help="Text file with your tasks, one per line.")
    parser.add_argument("--week-start", help="First day of the week (YYYY-MM-DD). Default: next Monday, or today if Monday.")
    parser.add_argument("--notes", default="", help="Anything else, e.g. 'gym Tue/Thu evenings'.")
    parser.add_argument("-o", "--output", help="Save the result to this Markdown file.")
    args = parser.parse_args()

    try:
        week_start = date.fromisoformat(args.week_start) if args.week_start else None
    except ValueError:
        sys.exit("--week-start must look like 2026-11-30")
    calendar_text = Path(args.calendar).expanduser().read_text(encoding="utf-8") if args.calendar else ""
    tasks = Path(args.tasks).expanduser().read_text(encoding="utf-8")
    if not tasks.strip():
        sys.exit("The tasks file is empty.")

    print("Planning your week...", file=sys.stderr)
    try:
        result = plan_week(calendar_text, tasks, week_start, args.notes)
    except ValueError as e:
        sys.exit(str(e))
    print(result)
    if args.output:
        Path(args.output).write_text(result + "\n", encoding="utf-8")
        print(f"\nSaved to {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
