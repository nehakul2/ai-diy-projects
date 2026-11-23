# Meeting cost calculator

See what your recurring meetings really cost, and where to cut.

Describe your meetings in plain words, upload a calendar export (`.ics`), or
give a CSV. You get:

- the cost of each meeting per month and per year (length × people × how often × hourly rate)
- the total, in money and person-hours
- Claude's verdict on each one: **keep**, **shorten**, **fewer people**,
  **make async** or **cancel**, with a reason and a practical tip
- how much the suggested changes would save

The maths is done in plain Python, so the numbers are exact. Claude reads your
meeting list and gives the advice. It's told that decisions, 1:1s and
brainstorms usually need to stay live, while read-outs usually don't.

## Try it

From the repo root:

```bash
python -m meeting_cost_calculator.main meeting_cost_calculator/examples/team_meetings.txt --rate 75
python -m meeting_cost_calculator.main meeting_cost_calculator/examples/meetings.csv --rate 75 --no-advice
python -m meeting_cost_calculator.main ~/Downloads/calendar.ics --rate 90 --currency "£" --context "8-person product team"
```

`--rate` is the average cost of one person's hour. A rough rule of thumb is
yearly salary ÷ 2,000, plus about 30% for overheads (a $100k salary is roughly $65/hour).

`--no-advice` only does the maths and makes no API call. It needs CSV input
with columns `title,minutes,attendees,per_month` (and optionally `purpose`).
How often per month: weekdays = 21, weekly = 4.3, every two weeks = 2.15, monthly = 1.

When Claude reads free text or a calendar, it lists anything it had to guess
(such as the number of attendees) under "Guesses to check".

The test page (`streamlit run app.py`) has the same options, plus example buttons.

## Ideas to improve it

- Use different rates per role (engineer, manager, director).
- Re-run monthly from your calendar and track the trend.
