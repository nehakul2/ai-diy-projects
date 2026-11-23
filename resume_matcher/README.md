# Resume vs job description matcher

Upload your resume and paste a job description. You get:

- your **3 strongest matches**, each backed by a direct quote from your resume
- the **gaps**, marked must-have or nice-to-have, with how to close each one
- **keywords** to add (only if they're true for you)
- up to 5 specific **resume tweaks** for this role

It never invents experience. Where a number would help, it leaves a
[placeholder] for you to fill in.

## Try it

From the repo root, with the example files:

```bash
python -m resume_matcher.main --resume resume_matcher/examples/resume.txt --job resume_matcher/examples/job.txt
```

With your own resume, saved as **PDF or plain text** (export from Word or
Pages first):

```bash
python -m resume_matcher.main --resume ~/Documents/resume.pdf --job job.txt -o match.md
```

You can also copy a job description and pipe it in with `pbpaste | python -m resume_matcher.main --resume ~/Documents/resume.pdf`.
It's on the test page too (`streamlit run app.py`).

## Ideas to improve it

- Feed it into project 8 (job-search tracker) so each saved role gets a match score.
- Draft a tailored cover letter from the strongest matches.
