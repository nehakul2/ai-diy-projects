# Reading list with a spoken summary

Got a pile of tabs you'll "read later"? Paste the links and Claude reads each
one and gives you:

- the **3 key points** of each article
- a verdict: **read in full**, **skim**, or **summary is enough**, with a reason
- a **spoken briefing** (about 3 minutes by default) that you can listen to
  while you walk, cook or commute, ending with which article to read first

Pages that can't be read (paywalls, errors) are flagged, and their summary is
based on the title only. You can also paste an article's text instead of a link.

## Try it

From the repo root:

```bash
python -m reading_list.main reading_list/examples/links.txt
python -m reading_list.main reading_list/examples/links.txt --speak
python -m reading_list.main reading_list/examples/links.txt --save ~/Desktop/briefing.m4a --minutes 5
python -m reading_list.main --from-library     # unread articles saved with project 9
```

The voice is your computer's own, so there's nothing extra to install or pay for:
`say` on a Mac (save as `.m4a`), the built-in Windows voice (save as `.wav`),
or `espeak-ng` on Linux. Up to 10 links per briefing.

On the test page (`streamlit run app.py`), **Play** reads the briefing aloud
using your browser's voice, and you can also make an audio file to download.

## Ideas to improve it

- Pick a nicer voice: on a Mac, run `say -v '?'` to list voices.
- Send yourself the audio every morning with your saved articles from the day before.
