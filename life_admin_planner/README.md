# Weekly life-admin planner

Give it a snapshot of your calendar and your task list. It:

- shows how busy each day looks
- **flags clashes** and pinch points, each with a suggested fix
- picks **3 realistic priorities**, each with a free slot to do it in
- says what can wait, plus a few quick wins for small gaps

If you give it an `.ics` calendar export, the code finds overlapping events
itself and passes them to Claude as facts. That way real clashes aren't missed.

## Try it

From the repo root, with the example week. It has a dentist and review clash
on Tuesday, car insurance expiring Thursday, a Friday evening flight, and
Mum's birthday on Saturday:

```bash
python -m life_admin_planner.main \
  --calendar life_admin_planner/examples/calendar.ics \
  --tasks life_admin_planner/examples/tasks.txt \
  --week-start 2026-11-30
```

With your own week, put tasks in a text file (one per line), then either:

- **Export your calendar:** in Google Calendar go to Settings > Import & export > Export, or in Apple Calendar use File > Export. Then pass the `.ics` file.
- **Type your week** in a text file, e.g. `Tue 15:00-16:00 dentist`, and pass that file instead.

`--week-start` defaults to next Monday (or today, if it's Monday). It's on the
test page too (`streamlit run app.py`).

Limitation: repeating events in an `.ics` file only show on their first date.

## Ideas to improve it

- Read Google Calendar directly instead of an export.
- Remember what you deferred last week and bring it back.
