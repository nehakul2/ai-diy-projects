# Notes into actions

Paste meeting notes, a voice-note transcript or an article, and get back:

- a short **summary**
- a **task list** (with owners and dates when the notes mention them)
- a **follow-up message** you can send

## Try it

From the repo root:

```bash
python -m notes_to_actions.main notes_to_actions/examples/team_sync.txt
```

Save the result to a file:

```bash
python -m notes_to_actions.main my_notes.txt -o actions.md
```

Or paste notes straight in (finish with Ctrl-D):

```bash
python -m notes_to_actions.main
```

## Ideas to improve it

- Read a `.docx` or `.pdf` instead of plain text.
- Add a `--tone` option for the follow-up message (formal or casual).
- Send the tasks to your to-do app.
