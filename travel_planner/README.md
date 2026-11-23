# Travel planner that checks the boring bits

Most trip planners just build an itinerary. This one checks the things that
actually go wrong: **visas and entry rules, passport validity, luggage limits,
check-in deadlines and tight transfers**. It searches official sites and links
its sources, then gives you a dated checklist and a simple day-by-day plan.

## Try it

From the repo root, using the example bookings (London to Tokyo via Doha,
then Kyoto and Seoul):

```bash
python -m travel_planner.main --file travel_planner/examples/bookings.txt --passport "Indian"
```

Or describe a trip in one line:

```bash
python -m travel_planner.main --trip "NYC to Lisbon 2-9 May, then Porto by train" \
  --passport "US" --airline "TAP, economy light"
```

Running it with no options makes it ask you each question. Add `-o trip.md` to
save the result.

Your passport nationality matters, because entry rules depend on it. Each run
uses web search and a higher effort setting, so it takes a minute or two and
costs a little more than the other projects.

**Always confirm visa and entry rules on the official government site before
you travel.** This tool helps you spot issues, but it isn't legal advice.

## Ideas to improve it

- Read booking confirmation PDFs directly.
- Add your calendar so it flags clashes with work.
- Re-run automatically a week before departure to catch rule changes.
