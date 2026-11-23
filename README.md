# AI DIY projects

18 small AI projects from Sakshi Chauhan's two "9 DIY AI projects" LinkedIn posts,
built from easiest to hardest. Each project lives in its own folder. Shared code
lives in `common/`.

| # | Project | Status |
|---|---------|--------|
| 1 | [Notes into actions](notes_to_actions/) | Done |
| 2 | [Gift idea finder](gift_idea_finder/) | Done |
| 3 | [Inbox clean-up helper](inbox_cleanup/) | Done |
| 4 | [Travel planner that checks the boring bits](travel_planner/) | Done |
| 5 | [Downloads organiser](downloads_organiser/) | Done |
| 6 | [Resume vs job description matcher](resume_matcher/) | Done |
| 7 | [Weekly life-admin planner](life_admin_planner/) | Done |
| 8 | [Job-search tracker](job_search_tracker/) | Done |
| 9 | [Saved-content organiser](saved_content_organiser/) | Done |
| 10 | [Decision journal pattern finder](decision_journal/) | Done |
| 11 | [Meeting cost calculator](meeting_cost_calculator/) | Done |
| 12 | [Reading list with a spoken summary](reading_list/) | Done |
| 13 | Personal finance explainer | Next |
| 14 | Photo organiser by event | |
| 15 | Self-updating personal dashboard | |
| 16 | Content-idea research assistant | |
| 17 | Team FAQ bot with sources | |
| 18 | Ask-your-notes assistant | |

## Setup (once)

You need Python 3.10 or newer.

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Get an API key from https://console.anthropic.com and set it:

```bash
export ANTHROPIC_API_KEY=sk-ant-...   # Windows: set ANTHROPIC_API_KEY=sk-ant-...
```

Then follow the README in each project folder. Run commands from the repo root.

## Test every project in your browser

Instead of typing commands, you can try each project in a simple web page.
From the repo root, with your virtual environment active:

```bash
streamlit run app.py
```

Your browser opens at http://localhost:8501. Pick a project in the left sidebar,
fill in the form and press the button. The first time, Streamlit may ask for an
email in the Terminal: just press Enter to skip. Press Ctrl-C in the Terminal to stop it.

The page uses the `ANTHROPIC_API_KEY` you exported. If you didn't set one, paste a key
into the sidebar box. A pasted key stays in that browser tab's memory and is never saved.

**Adding a project to the test page:** create `<project>/ui.py` with `TITLE`, `ORDER`
and a `render()` function that calls the project's own functions (see
`notes_to_actions/ui.py`). The page picks it up automatically.

By default the projects use Claude Opus 5.5. To try another model, set
`CLAUDE_MODEL`, e.g. `export CLAUDE_MODEL=claude-haiku-5-5` for a cheaper one.
