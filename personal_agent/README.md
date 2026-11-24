# Personal agent

One assistant you talk to in plain words. It works out which of your 18 projects fits
what you asked, runs it, and tells you the result. It reuses each project's own code,
so it behaves exactly like the project would on its own.

## Try it

From the repo root, with your virtual environment active:

```bash
streamlit run app.py
```

"Personal agent (chat)" is the first page in the sidebar. Or chat in Terminal:

```bash
python -m personal_agent.main
python -m personal_agent.main "gift ideas for my dad, around \$60, he loves gardening"
```

Things to ask:

- "Turn these notes into actions: ..." (paste them)
- "Gift ideas for my sister, under £40, into climbing and tea"
- "Check my trip: London to Tokyo via Doha, 3-17 March, Indian passport"
- "Tidy my Downloads folder" → shows a plan → "go ahead" → press **Confirm**
- "Sort my photos in ~/Pictures/Unsorted into events"
- "How well does my resume ~/Documents/resume.pdf match job 2 in my tracker?"
- "What's on my job tracker?" / "Mark job 2 as applied, follow up next Friday"
- "Save this link: https://..." / "What have I saved about focus?"
- "Log a decision: I'm taking the Berlin offer..." / "Which decisions are due for review?"
- "Explain my spending in ~/Downloads/statement.csv, pounds, UK dates"
- "Plan my week. Tasks: dentist, tax return, call mum. Calendar: ~/Downloads/calendar.ics"
- "What did I write about habits in ~/Documents/Obsidian?"

**Files:** in the chat page, attach a file with "📎 Attach a file". In Terminal, type the
path (tip: drag the file into the Terminal window to paste its path).

## The standalone app (and sharing it with friends)

`python -m personal_agent.web` opens the agent as its own app at http://localhost:8000
(on your Mac, everything works, using your own files). To put it online for friends, with a
name + PIN sign-in, 10 questions each on your key and their own saved data, follow
[DEPLOY.md](DEPLOY.md). Friends can add it to their phone's home screen.

The older Streamlit chat page is still there: `streamlit run agent_app.py`.

## Safety

- Moving files always takes two steps: a preview first, then a **Confirm** button
  (or yes/no in Terminal). The agent itself can only *ask*; it cannot move anything.
- Undoing a tidy-up asks for confirmation the same way.
- Everything else either only reads, or saves to your own data files in
  `~/.ai-diy-projects/` (job tracker, library, decisions, idea bank), just like the projects.
- Each message costs a little more than running a project directly, because Claude
  first decides which project to use.

## Settings

- `AGENT_NAME=Neha` makes the assistant address you by name.
- `CLAUDE_MODEL` works here too (default Claude Opus 5.5).

## How it works

- `tools.py`: each project is described as a "tool" (name, what it does, what it needs)
  and wired to that project's existing function.
- `agent.py`: sends your message and the tool list to Claude; when Claude picks a tool,
  runs it on your computer and sends the result back, until Claude replies.
- `ui.py` / `main.py`: the chat page and the Terminal chat.

To add a new project to the agent, add one `@tool(...)` function in `tools.py`.
