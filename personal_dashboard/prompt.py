BRIEFING_SYSTEM = """You prepare the web part of someone's personal morning dashboard.
Today is {today}. Use web search to find current information. Be brief: this is
read at a glance.

- weather: today's forecast for their location: a one-line summary, the high and
  low (with units as used locally), and a short tip if useful ("take an umbrella").
- topics: for each topic, up to 3 items from the last few days. Each has a
  headline (your own words, under 15 words), one line on why it matters to someone
  following the topic, and the source URL. Skip old or low-quality items. If
  nothing new, return an empty list for that topic.
- answers: answer each question in 1-2 sentences, with a source URL.
- focus: one friendly sentence suggesting what to focus on today, based on their
  local items (calendar, follow-ups, reviews due) and the weather.
Never invent facts or URLs; only use what your searches found."""

BRIEFING_SCHEMA = {
    "type": "object",
    "properties": {
        "weather": {
            "type": "object",
            "properties": {"summary": {"type": "string"}, "high": {"type": "string"},
                           "low": {"type": "string"}, "tip": {"type": "string"}},
            "required": ["summary", "high", "low", "tip"],
            "additionalProperties": False,
        },
        "topics": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string"},
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {"headline": {"type": "string"}, "why": {"type": "string"},
                                           "url": {"type": "string"}},
                            "required": ["headline", "why", "url"],
                            "additionalProperties": False,
                        },
                    },
                },
                "required": ["topic", "items"],
                "additionalProperties": False,
            },
        },
        "answers": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"question": {"type": "string"}, "answer": {"type": "string"},
                               "url": {"type": "string"}},
                "required": ["question", "answer", "url"],
                "additionalProperties": False,
            },
        },
        "focus": {"type": "string"},
    },
    "required": ["weather", "topics", "answers", "focus"],
    "additionalProperties": False,
}
