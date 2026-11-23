# Job-search tracker

Track the roles you've saved, their deadlines and your next action for each.
When you add a role, Claude reads the posting and pulls out:

- company, role, location, salary and **deadline** (when the posting states one)
- **must-have and nice-to-have skills**, in the posting's own words
- an **application checklist** specific to that role
- a suggested **next action**

Everything is saved on your computer in `~/.ai-diy-projects/jobs.json`, not in
the repo. Set `JOBS_FILE` to use a different file.

## Try it

From the repo root:

```bash
python -m job_search_tracker.main add --posting job_search_tracker/examples/posting.txt --url https://example.com/job
python -m job_search_tracker.main list
python -m job_search_tracker.main show 1
python -m job_search_tracker.main done 1 2                       # tick step 2
python -m job_search_tracker.main update 1 --status applied --next "Follow up" --next-date 2026-12-08
python -m job_search_tracker.main match 1 --resume ~/Documents/resume.pdf   # uses project 6
```

`list` puts the most urgent roles first, and flags anything 🔴 overdue or 🟠
due this week. Closed roles (offer, rejected, withdrawn) are hidden unless you
add `--all`. The statuses are saved, applying, applied, interviewing, offer,
rejected and withdrawn.

To add a role without saving the posting to a file, copy it and run
`pbpaste | python -m job_search_tracker.main add`.

The test page (`streamlit run app.py`) has tabs to add roles, see the list,
tick checklist steps and update status.

## Ideas to improve it

- Save the resume match score with each role.
- Send a reminder email the day before a next-action date.
