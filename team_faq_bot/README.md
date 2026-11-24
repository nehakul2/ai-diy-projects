# Team FAQ bot with sources

Your team's handbook, policies and how-tos, answerable in plain words:

> **How many holiday days can I carry over?**
> Up to 5 unused days, and they must be used by 31 March [1].
>
> **Sources**
> [1] **time-off.md › Holiday allowance**: _Everyone gets 25 days of paid holiday a year…_

- Every answer cites the **exact passages** it came from, so people can check.
- If the documents don't cover something, it **says so instead of guessing**.
- Unanswered questions are **logged**, so you can see which docs to write next.
- Follow-up questions work ("and for part-timers?").

## Try it

From the repo root, using the example handbook in `team_faq_bot/examples/handbook/`:

```bash
python -m team_faq_bot.main "How many holiday days can I carry over?"
python -m team_faq_bot.main "Who approves an expense of $120?"
python -m team_faq_bot.main --docs ~/Documents/team-handbook      # chat with your own docs
python -m team_faq_bot.main --gaps                                 # what the docs couldn't answer
```

It reads `.md`, `.txt` and `.html` files in the folder and its subfolders, and
PDFs too if you `pip install pypdf`. Export Google Docs or Notion pages as
Markdown or HTML into one folder.

## How it works

The documents are split into passages at headings and searched on your
computer with BM25 (a classic keyword-ranking formula, in `common/search.py`).
Only the 6 best passages are sent to Claude with the question, and Claude is
told to answer only from them and cite each one. The same search is used by
project 18 (ask-your-notes).

The unanswered-question log is `~/.ai-diy-projects/faq-gaps.json` (set `FAQ_GAPS_FILE` to change it).

The test page (`streamlit run app.py`) has a chat tab and an "Unanswered questions" tab.

## Ideas to improve it

- Connect it to Slack so the team can ask it in a channel.
- Use embeddings for better matching when people use different words from the docs.
