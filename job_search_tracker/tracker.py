"""Tracker actions shared by the CLI and the test page."""
import json
import re
from datetime import date

from common.claude import ask
from job_search_tracker import store
from job_search_tracker.prompt import SCHEMA, SYSTEM

MAX_POSTING_CHARS = 30000


def add_role(posting: str, url: str = "", deadline: str = "") -> dict:
    """Read a job posting with Claude and save it. Returns the saved role."""
    if not posting.strip():
        raise ValueError("The job posting is empty.")
    if deadline:
        store.check_date(deadline)
    info = json.loads(ask(SYSTEM, f"<job_posting>\n{posting[:MAX_POSTING_CHARS]}\n</job_posting>", schema=SCHEMA))
    found_deadline = info["deadline"] if re.fullmatch(r"\d{4}-\d{2}-\d{2}", info["deadline"] or "") else ""
    job = {
        "company": info["company"], "role": info["role"], "location": info["location"],
        "salary": info["salary"], "url": url, "summary": info["summary"],
        "deadline": deadline or found_deadline,
        "must_have_skills": info["must_have_skills"], "nice_to_have_skills": info["nice_to_have_skills"],
        "checklist": [{"step": s, "done": False} for s in info["checklist"]],
        "next_action": info["next_action"], "next_action_date": "",
        "notes": "", "posting": posting[:MAX_POSTING_CHARS],
    }
    return store.add(job)


def table(jobs: list[dict], show_all: bool = False, today: date | None = None) -> str:
    """Markdown table, most urgent first. Hides closed roles unless show_all."""
    rows = [j for j in jobs if show_all or j.get("status") in store.ACTIVE]
    if not rows:
        return "No roles to show yet. Add one with: python -m job_search_tracker.main add --posting job.txt"

    def sort_key(j):
        dates = [d for d in (j.get("deadline"), j.get("next_action_date")) if d]
        return (min(dates) if dates else "9999-12-31", j["id"])

    flag = {"overdue": "🔴 overdue", "soon": "🟠 this week", "": ""}
    lines = ["| id | Company | Role | Status | Deadline | Next action | |", "|---|---|---|---|---|---|---|"]
    for j in sorted(rows, key=sort_key):
        steps = j.get("checklist", [])
        done = sum(s["done"] for s in steps)
        nxt = j.get("next_action", "") + (f" (by {j['next_action_date']})" if j.get("next_action_date") else "")
        lines.append(f"| {j['id']} | {j['company']} | {j['role']} | {j['status']} | {j.get('deadline') or '-'} | "
                     f"{nxt} ({done}/{len(steps)} steps) | {flag[store.urgency(j, today)]} |")
    return "\n".join(lines)


def details(job: dict) -> str:
    lines = [f"## {job['role']} at {job['company']} (id {job['id']})", "",
             f"**Status:** {job['status']} · **Deadline:** {job.get('deadline') or 'none stated'} · "
             f"**Location:** {job.get('location') or '-'}" + (f" · **Salary:** {job['salary']}" if job.get("salary") else ""),
             ""]
    if job.get("url"):
        lines += [f"**Link:** {job['url']}", ""]
    lines += [job.get("summary", ""), "", "**Must-have skills:** " + ", ".join(job.get("must_have_skills", [])),
              "", "**Nice to have:** " + (", ".join(job.get("nice_to_have_skills", [])) or "-"), "", "### Checklist"]
    lines += [f"{i}. [{'x' if s['done'] else ' '}] {s['step']}" for i, s in enumerate(job.get("checklist", []), 1)]
    lines += ["", f"**Next action:** {job.get('next_action', '')}"
              + (f" (by {job['next_action_date']})" if job.get("next_action_date") else "")]
    if job.get("notes"):
        lines += ["", f"**Notes:** {job['notes']}"]
    return "\n".join(lines)
