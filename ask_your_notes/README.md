# Ask-your-notes assistant

A search engine for your own brain. Point it at your notes and ask:

> **What budget did I get for user interviews?**
> $1,500, approved at the onboarding kick-off on 30 October. You'd originally
> planned to ask for $2,000 [2][1].

- Works with an **Obsidian vault**, a folder of Markdown or text files, exported
  Notion or Google Docs pages, and PDFs (with `pip install pypdf`). Subfolders included.
- Can also search your **saved-content library** (project 9) and **decision journal** (project 10).
- Every answer **cites the notes** it came from. When plans changed over time, it
  gives the latest and mentions the earlier one. If your notes don't cover it, it says so.
- Follow-up questions work in chat mode.

## Try it

From the repo root, using the example notes in `ask_your_notes/examples/notes/`:

```bash
python -m ask_your_notes.main "What did I learn about habits?"
python -m ask_your_notes.main "When is my Lisbon trip?"
python -m ask_your_notes.main --notes ~/Documents/Obsidian                     # chat with your vault
python -m ask_your_notes.main --notes ~/Notes --include library,decisions      # search everything
```

## Privacy

Your notes are searched on your computer (the same BM25 search as project 17,
in `common/search.py`). Only the 8 most relevant passages for each question are
sent to Claude, never the whole folder. Hidden folders such as `.obsidian` are skipped.

The test page (`streamlit run app.py`) is a chat where you pick the notes folder
and the extra sources.

## Ideas to improve it

- A weekly "notes you forgot" digest that resurfaces related old notes.
- Use embeddings so questions match notes that use different words.
