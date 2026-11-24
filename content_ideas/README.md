# Content-idea research assistant

Never stare at a blank page again. Tell it your niche, audience and platform,
and Claude **searches what people are discussing right now** (news, new
tools, forum questions, debates) and suggests ideas. Each one has:

- a **hook** (title) and a **fresh angle**
- **why it's timely**, with a source link
- the best **format** for your platform and a short **outline**
- a **score** out of 15: timeliness, audience fit and originality

Ideas go into an **idea bank** (`~/.ai-diy-projects/ideas.json`, or set
`IDEAS_FILE`), so later searches don't repeat them. Pick one and Claude writes a
**first draft** for your platform, matching your voice if you give it a few past posts.

## Try it

From the repo root:

```bash
python -m content_ideas.main research --niche "AI tools and habits for product managers" \
  --audience "PMs at startups" --platform LinkedIn --past content_ideas/examples/past_posts.txt
python -m content_ideas.main list
python -m content_ideas.main draft 1 --past content_ideas/examples/past_posts.txt
python -m content_ideas.main status 1 posted
```

Platforms: LinkedIn, Blog, Newsletter, YouTube, Instagram, X / Threads, Podcast.
`--count` sets how many ideas (1 to 10). Research takes a couple of minutes
because it runs several web searches. Drafting doesn't search the web; it
works from the idea and its source, and puts anything you should check or
personalise in [square brackets].

The test page (`streamlit run app.py`) has a "Find ideas" tab and an "Idea bank"
tab where you can draft, mark as posted or skip ideas.

## Ideas to improve it

- Feed it your saved articles from project 9 as extra inspiration.
- Track which posted ideas did best and favour similar angles.
