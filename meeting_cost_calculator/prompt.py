EXTRACT_SYSTEM = """Turn someone's description of their recurring meetings (free text, a list,
or a calendar export) into a structured list. For each meeting give:
- title
- minutes: scheduled length
- attendees: number of people, including the organiser (count ATTENDEE lines in
  calendar exports; if unknown, make a sensible guess and say so in notes)
- per_month: how often it happens per month (daily on weekdays = 21, weekly = 4.3,
  every two weeks = 2.15, monthly = 1, one-off = 1)
- purpose: what it's for, in a few words, from what they wrote
- notes: anything you had to guess, otherwise empty

Only include meetings. Don't invent meetings that aren't described."""

EXTRACT_SCHEMA = {
    "type": "object",
    "properties": {
        "meetings": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "minutes": {"type": "integer"},
                    "attendees": {"type": "integer"},
                    "per_month": {"type": "number"},
                    "purpose": {"type": "string"},
                    "notes": {"type": "string"},
                },
                "required": ["title", "minutes", "attendees", "per_month", "purpose", "notes"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["meetings"],
    "additionalProperties": False,
}

ADVICE_SYSTEM = """You help a team spend less time in meetings without losing what matters.
For each meeting (with its cost already worked out), decide one verdict:
- keep: worth it as it is
- shorten: same people, less time
- fewer people: some attendees could read notes instead
- make async: could be a written update, doc comments or a recorded video
- cancel: no clear purpose, or duplicates another meeting

Give suggested_minutes and suggested_attendees for the new version (0 and 0 for
make async or cancel; the same numbers for keep). Be realistic: decision-making,
1:1s, brainstorming and conflict resolution usually need to stay live. Status
updates and read-outs usually don't.
reason: one sentence tied to the meeting's purpose.
tip: one specific, practical change (e.g. "Post updates in the channel by 10am;
meet only on blockers").
Also give a short overall summary (2-3 sentences) of the biggest opportunities."""

ADVICE_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "advice": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "verdict": {"type": "string", "enum": ["keep", "shorten", "fewer people", "make async", "cancel"]},
                    "suggested_minutes": {"type": "integer"},
                    "suggested_attendees": {"type": "integer"},
                    "reason": {"type": "string"},
                    "tip": {"type": "string"},
                },
                "required": ["title", "verdict", "suggested_minutes", "suggested_attendees", "reason", "tip"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["summary", "advice"],
    "additionalProperties": False,
}
