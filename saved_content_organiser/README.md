# Saved-content organiser

A home for the articles, videos and podcast notes you save "for later". For
each item, Claude reads the link (or your pasted text or notes) and adds:

- a title, the type (article, video, podcast and so on) and a rough time to read or watch
- **2 to 4 tags**, reusing your existing tags so the library stays tidy
- a **3-point summary**
- **why it matters** to you, building on your own note when you give one

Everything is saved on your computer in `~/.ai-diy-projects/library.json`.
Set `LIBRARY_FILE` to use a different file.

## Try it

From the repo root:

```bash
python -m saved_content_organiser.main add --url https://en.wikipedia.org/wiki/Pomodoro_Technique --note "trying this for focus"
python -m saved_content_organiser.main add --text saved_content_organiser/examples/podcast_notes.txt --note "ideas for weekly planning"
python -m saved_content_organiser.main list
python -m saved_content_organiser.main list --tag productivity --search "weekly"
python -m saved_content_organiser.main tags
python -m saved_content_organiser.main done 1
```

To make "why it matters" more personal, set your interests once:
`export MY_INTERESTS="product analytics, parenting, running"`.

Searching and filtering happen on your computer, with no API call. Items you
mark done are hidden unless you add `--all`. The test page
(`streamlit run app.py`) lets you browse by tag, type or search, and add new items.

Some pages can't be read, such as paywalled articles or video pages with
little text. In that case the summary is based on the title and your notes,
and says so.

## Ideas to improve it

- Feed the library into project 18 (ask-your-notes) to ask questions across everything you've saved.
- A weekly digest of your 3 most relevant unread items.
