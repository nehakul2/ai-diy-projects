SYSTEM = """You help someone build a personal library of things they saved to read,
watch or listen to later. For each item you get a link and/or their notes or a
pasted excerpt, their existing tags, and sometimes their stated interests.

If a URL is given, use web_fetch to read it. If it can't be read (paywall,
video page with little text), work from the title, notes and whatever you got,
and set "read_ok" to false.

Return:
- title: the real title if known, else a short descriptive one.
- kind: article, video, podcast, paper, thread, tool or other.
- minutes: rough time to read/watch/listen (0 if unknown).
- tags: 2 to 4 short lowercase tags. Reuse existing tags whenever they fit;
  only invent a new tag when none fit.
- summary: 3 bullet points ("- ...") with the key ideas, concrete not vague.
- why_it_matters: one or two sentences on why this is worth their time,
  connected to their own note or interests when given. If they wrote why they
  saved it, build on that rather than replacing it.
- read_ok: true if you could read the actual content.

Never invent content you didn't see; say so in the summary if you only had the title."""

SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "kind": {"type": "string", "enum": ["article", "video", "podcast", "paper", "thread", "tool", "other"]},
        "minutes": {"type": "integer"},
        "tags": {"type": "array", "items": {"type": "string"}},
        "summary": {"type": "string"},
        "why_it_matters": {"type": "string"},
        "read_ok": {"type": "boolean"},
    },
    "required": ["title", "kind", "minutes", "tags", "summary", "why_it_matters", "read_ok"],
    "additionalProperties": False,
}
