# AI DIY projects

18 small AI projects from Sakshi Chauhan's two "9 DIY AI projects" LinkedIn posts,
built from easiest to hardest. Each project lives in its own folder. Shared code
lives in `common/`.

| # | Project | Status |
|---|---------|--------|
| 1 | [Notes into actions](notes_to_actions/) | Done |
| 2 | [Gift idea finder](gift_idea_finder/) | Done |
| 3 | Inbox clean-up helper | Next |
| 4 | Travel planner that checks the boring bits | |
| 5 | Downloads organiser | |
| 6 | Resume vs job description matcher | |
| 7 | Weekly life-admin planner | |
| 8 | Job-search tracker | |
| 9 | Saved-content organiser | |
| 10 | Decision journal pattern finder | |
| 11 | Meeting cost calculator | |
| 12 | Reading list with a spoken summary | |
| 13 | Personal finance explainer | |
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

By default the projects use Claude Opus 5.5. To try another model, set
`CLAUDE_MODEL`, e.g. `export CLAUDE_MODEL=claude-haiku-5-5` for a cheaper one.
