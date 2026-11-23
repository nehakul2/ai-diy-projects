# Decision journal pattern finder

Write down important decisions at the time you make them, check back later on
how they turned out, and let Claude spot patterns in how you decide.

1. **Log** a decision: what you decided, the context, the options you
   considered, what you expect, and how confident you are (0 to 100%).
   Claude adds the **hidden assumptions** it rests on, **early signals** to
   watch, **what would change your mind**, and a sensible **review date**.
2. **Review** it when the date comes: better, as expected, worse or too
   early to tell, what happened, and which assumptions held.
3. **Find patterns** once 3 or more decisions are reviewed. Claude looks at
   your calibration (are 80%-confident calls right 80% of the time?),
   assumptions that keep failing, and habits like only considering one
   option, then suggests 3 things to try next time.

Everything is saved on your computer in `~/.ai-diy-projects/decisions.json`.
Set `DECISIONS_FILE` to use a different file.

## Try it

From the repo root:

```bash
python -m decision_journal.main log --decision "Take the team lead role" \
  --context "Manager left, I was asked to step in" --options "take the role; stay as engineer" \
  --expected "More impact, a bit less coding" --confidence 75
python -m decision_journal.main list
python -m decision_journal.main due
python -m decision_journal.main review 1 --outcome worse --what "Hardly any coding time" \
  --assumptions "Team support held; focus time didn't" --lesson "Agree protected focus time first"
python -m decision_journal.main patterns
```

To try the pattern finder straight away, load 5 sample decisions into an
empty journal (4 already reviewed). Using a separate file keeps them out of
your real journal:

```bash
export DECISIONS_FILE=/tmp/sample-decisions.json
python -m decision_journal.main samples
python -m decision_journal.main patterns
```

`log --no-ai` saves a decision without calling Claude (review date defaults to
90 days). Listing, `due` and `review` never call Claude. The test page
(`streamlit run app.py`) has tabs for logging, the journal, reviews and patterns.

## Ideas to improve it

- A weekly reminder (with project 7's life-admin planner) for decisions that are due for review.
- Compare patterns by area: work, money, health.
