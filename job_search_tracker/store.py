"""Saved roles, kept in one JSON file on your computer (not in the repo).

Default location: ~/.ai-diy-projects/jobs.json. Set JOBS_FILE to use another file.
"""
import os
from datetime import date
from pathlib import Path
from common import storage

STATUSES = ["saved", "applying", "applied", "interviewing", "offer", "rejected", "withdrawn"]
ACTIVE = {"saved", "applying", "applied", "interviewing"}


def check_date(value: str) -> None:
    try:
        date.fromisoformat(value)
    except ValueError:
        raise ValueError(f"'{value}' isn't a date. Use YYYY-MM-DD, e.g. 2026-12-05.") from None


def jobs_file() -> Path:
    return Path(os.environ.get("JOBS_FILE", Path.home() / ".ai-diy-projects" / "jobs.json")).expanduser()


def load() -> list[dict]:
    return storage.read_json("jobs", jobs_file())


def save(jobs: list[dict]) -> None:
    storage.write_json("jobs", jobs_file(), jobs)


def add(job: dict) -> dict:
    jobs = load()
    job["id"] = max((j["id"] for j in jobs), default=0) + 1
    job.setdefault("status", "saved")
    job.setdefault("added", date.today().isoformat())
    jobs.append(job)
    save(jobs)
    return job


def get(job_id: int) -> dict:
    for j in load():
        if j["id"] == job_id:
            return j
    raise ValueError(f"No saved role with id {job_id}. Run 'list' to see ids.")


def update(job_id: int, **changes) -> dict:
    if "status" in changes and changes["status"] not in STATUSES:
        raise ValueError(f"Status must be one of: {', '.join(STATUSES)}")
    for key in ("deadline", "next_action_date"):
        if changes.get(key):
            check_date(changes[key])
    jobs = load()
    for j in jobs:
        if j["id"] == job_id:
            j.update({k: v for k, v in changes.items() if v is not None})
            save(jobs)
            return j
    raise ValueError(f"No saved role with id {job_id}. Run 'list' to see ids.")


def toggle_step(job_id: int, step_index: int) -> dict:
    jobs = load()
    for j in jobs:
        if j["id"] == job_id:
            steps = j.get("checklist", [])
            if not 0 <= step_index < len(steps):
                raise ValueError(f"Role {job_id} has {len(steps)} checklist steps.")
            steps[step_index]["done"] = not steps[step_index]["done"]
            save(jobs)
            return j
    raise ValueError(f"No saved role with id {job_id}.")


def urgency(job: dict, today: date | None = None) -> str:
    """'overdue', 'soon' (within 7 days), or '' for the earliest of deadline / next action date."""
    if job.get("status") not in ACTIVE:
        return ""
    today = today or date.today()
    dates = [date.fromisoformat(d) for d in (job.get("deadline"), job.get("next_action_date")) if d]
    if not dates:
        return ""
    days = (min(dates) - today).days
    return "overdue" if days < 0 else "soon" if days <= 7 else ""
