# Self-updating personal dashboard

One page with what you need today:

- **Weather** for your location, with a tip if it's useful
- **News on your topics**: up to 3 fresh items each, with why they matter
- **Answers to your standing questions**, such as "Any BART disruption this week?"
- From your other projects, with no API call:
  - your **calendar** for today and tomorrow (from an `.ics` export, like project 7)
  - **job-search follow-ups** that are due or overdue (project 8)
  - **decisions due for review** (project 10)
  - your **reading list** (project 9)
- A one-line **focus for the day**

The web part is found by Claude with web search. The page is saved as
`~/.ai-diy-projects/dashboard.html`, with light and dark mode, and it reloads
itself in an open browser tab.

## Try it

From the repo root:

```bash
python -m personal_dashboard.main --init          # copy the example settings, then edit them
python -m personal_dashboard.main --open          # build it and open the page
python -m personal_dashboard.main --local-only    # just your own data, no API call
```

Settings live in `~/.ai-diy-projects/dashboard.json` (the example in
`personal_dashboard/examples/` is used until you create yours):

```json
{
  "name": "Neha",
  "location": "San Francisco, CA",
  "topics": ["AI tools for product managers"],
  "questions": ["Is there any BART disruption this week?"],
  "calendar": "~/Downloads/calendar.ics",
  "include": ["calendar", "jobs", "decisions", "reading"]
}
```

## Keeping it up to date

**While your computer is on:** leave this running in a Terminal window. It
rebuilds every hour, and the open page refreshes itself:

```bash
python -m personal_dashboard.main --watch 60 --open
```

**Every morning automatically (Mac or Linux):** add a cron job with
`crontab -e`, for example at 7:30 every weekday (use your own paths and key):

```
30 7 * * 1-5 cd ~/ai-diy-projects && ANTHROPIC_API_KEY=sk-ant-... /usr/bin/python3 -m personal_dashboard.main >> ~/.ai-diy-projects/dashboard.log 2>&1
```

Each web update makes several searches, so `--watch` needs at least 15 minutes
between updates. `--local-only` updates are free, and keep the last web part.

The test page (`streamlit run app.py`) lets you edit the settings and update the dashboard.

## Ideas to improve it

- Add a card for the meeting cost of this week's calendar (project 11).
- Email yourself the page each morning.
