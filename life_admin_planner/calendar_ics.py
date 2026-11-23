"""Read a calendar export (.ics) and find clashes, using only the standard library.

Handles the common cases (timed and all-day events, UTC or local times).
Repeating events (RRULE) are only shown on their first date, which is noted in the output.
"""
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone


@dataclass
class Event:
    title: str
    start: datetime
    end: datetime
    all_day: bool = False
    repeats: bool = False

    def describe(self) -> str:
        if self.all_day:
            when = self.start.strftime("%a %d %b") + " (all day)"
        else:
            when = f"{self.start:%a %d %b %H:%M}-{self.end:%H:%M}"
        return f"{when}: {self.title}" + (" [repeats]" if self.repeats else "")


def _unfold(text: str) -> list[str]:
    lines: list[str] = []
    for raw in text.replace("\r\n", "\n").split("\n"):
        if raw[:1] in (" ", "\t") and lines:
            lines[-1] += raw[1:]
        else:
            lines.append(raw)
    return lines


def _parse_dt(value: str, params: str) -> tuple[datetime, bool]:
    if "VALUE=DATE" in params or len(value) == 8:
        d = datetime.strptime(value[:8], "%Y%m%d")
        return d, True
    dt = datetime.strptime(value[:15], "%Y%m%dT%H%M%S")
    if value.endswith("Z"):
        dt = dt.replace(tzinfo=timezone.utc).astimezone().replace(tzinfo=None)  # show in local time
    return dt, False


def parse_ics(text: str) -> list[Event]:
    events, cur = [], None
    for line in _unfold(text):
        if line == "BEGIN:VEVENT":
            cur = {}
        elif line == "END:VEVENT" and cur is not None:
            if "start" in cur:
                start, all_day = cur["start"]
                end = cur.get("end", (start + (timedelta(days=1) if all_day else timedelta(hours=1)), all_day))[0]
                events.append(Event(cur.get("title", "(no title)"), start, end, all_day, cur.get("repeats", False)))
            cur = None
        elif cur is not None and ":" in line:
            name_params, value = line.split(":", 1)
            name, _, params = name_params.partition(";")
            if name == "SUMMARY":
                cur["title"] = value.replace("\\,", ",").replace("\\n", " ").strip()
            elif name == "DTSTART":
                cur["start"] = _parse_dt(value, params)
            elif name == "DTEND":
                cur["end"] = _parse_dt(value, params)
            elif name == "RRULE":
                cur["repeats"] = True
    return sorted(events, key=lambda e: e.start)


def in_week(events: list[Event], week_start: date) -> list[Event]:
    start = datetime.combine(week_start, datetime.min.time())
    end = start + timedelta(days=7)
    return [e for e in events if e.start < end and e.end > start]


def clashes(events: list[Event]) -> list[tuple[Event, Event]]:
    """Pairs of timed events that overlap."""
    timed = [e for e in events if not e.all_day]
    found = []
    for i, a in enumerate(timed):
        for b in timed[i + 1:]:
            if b.start >= a.end:
                break
            found.append((a, b))
    return found
