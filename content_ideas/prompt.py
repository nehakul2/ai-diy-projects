PLATFORMS = ["LinkedIn", "Blog", "Newsletter", "YouTube", "Instagram", "X / Threads", "Podcast"]

RESEARCH_SYSTEM = """You are a content strategist helping a creator find timely post ideas.
Today is {today}.

1. Use web search to see what their audience is discussing right now: news from the
   last few weeks, new tools or reports, common questions, debates and frustrations
   (forums, Reddit, Q&A sites, newsletters). Search several angles.
2. Propose {count} distinct ideas for their platform. Each idea needs:
   - title: a scroll-stopping hook in their style (not clickbait)
   - angle: what's fresh or contrarian about their take, in one sentence
   - why_now: what's happening that makes it timely, in one sentence
   - source_url: a real URL from your searches backing up why_now
   - format: the best format for the platform (e.g. carousel, how-to, story, list, opinion)
   - outline: 3 to 5 short bullet points
   - scores 1-5: timeliness, audience_fit, originality (be honest; not everything is a 5)
3. Avoid ideas they've already covered (their past posts and saved ideas are listed).
   Lean on their own experience where it fits.
Never invent sources, numbers or quotes."""

RESEARCH_SCHEMA = {
    "type": "object",
    "properties": {
        "ideas": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "angle": {"type": "string"},
                    "why_now": {"type": "string"},
                    "source_url": {"type": "string"},
                    "format": {"type": "string"},
                    "outline": {"type": "array", "items": {"type": "string"}},
                    "timeliness": {"type": "integer"},
                    "audience_fit": {"type": "integer"},
                    "originality": {"type": "integer"},
                },
                "required": ["title", "angle", "why_now", "source_url", "format", "outline", "timeliness",
                             "audience_fit", "originality"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["ideas"],
    "additionalProperties": False,
}

DRAFT_SYSTEM = """Write a first draft of a post for the creator, ready for them to edit.
Platform conventions:
- LinkedIn: strong first line, short paragraphs, 150-300 words, end with a question; no hashtag spam (max 3).
- Blog: title, intro, subheadings, 600-900 words, conclusion.
- Newsletter: friendly subject line and preview text, then 300-500 words.
- YouTube: title, a 15-second hook, then a script outline with timestamps.
- Instagram: carousel slide-by-slide text (6-8 slides) plus a caption.
- X / Threads: a thread of 5-8 posts, each under 280 characters.
- Podcast: episode title, intro script and talking points.
Match their voice from their past posts if given. Use only facts from the idea and its
source; mark anything they should check or personalise with [square brackets]."""
