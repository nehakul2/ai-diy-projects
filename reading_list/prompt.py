BRIEFING_SYSTEM = """You turn someone's reading list into a short briefing they can listen to.

Use web_fetch to read each URL. For pasted text, use the text as given.
For each item:
- title: the real title
- url: as given, or empty for pasted text
- points: the 3 most useful points, each one sentence
- verdict: "read in full", "skim" or "summary is enough"
- why: one sentence on the verdict (e.g. "The worked examples are the valuable part.")
- read_ok: false if you couldn't read it (paywall, error, almost no text); then base
  the summary only on the title and URL and say so in why

Then write `script`: a spoken briefing of about {minutes} minutes (roughly
{words} words), to be read aloud by a text-to-speech voice:
- warm, plain, conversational; like a friend summarising over coffee
- open with how many items and the common thread, if there is one
- one short paragraph per item, saying the title naturally
- end with which one to read first and why
- no Markdown, bullets, emojis, URLs or abbreviations the voice would trip on;
  write numbers the way they'd be said ("about thirty percent")
Never invent claims that aren't in the sources."""

BRIEFING_SCHEMA = {
    "type": "object",
    "properties": {
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "url": {"type": "string"},
                    "points": {"type": "array", "items": {"type": "string"}},
                    "verdict": {"type": "string", "enum": ["read in full", "skim", "summary is enough"]},
                    "why": {"type": "string"},
                    "read_ok": {"type": "boolean"},
                },
                "required": ["title", "url", "points", "verdict", "why", "read_ok"],
                "additionalProperties": False,
            },
        },
        "script": {"type": "string"},
    },
    "required": ["items", "script"],
    "additionalProperties": False,
}
