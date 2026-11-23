"""Job-search tracker: saved roles, deadlines, next actions and a checklist per role.

Usage:
    python -m job_search_tracker.main add --posting job.txt [--url https://...] [--deadline 2026-12-15]
    python -m job_search_tracker.main list [--all]
    python -m job_search_tracker.main show 3
    python -m job_search_tracker.main update 3 --status applied --next "Follow up with recruiter" --next-date 2026-12-05
    python -m job_search_tracker.main done 3 2          # tick checklist step 2 of role 3
    python -m job_search_tracker.main match 3 --resume ~/Documents/resume.pdf
"""
import argparse
import sys
from pathlib import Path

from job_search_tracker import store
from job_search_tracker.tracker import add_role, details, table


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("add", help="Save a role from a job posting.")
    p.add_argument("--posting", help="Text file with the job posting. Leave out to paste it (stdin).")
    p.add_argument("--url", default="", help="Link to the posting.")
    p.add_argument("--deadline", default="", help="Application deadline, YYYY-MM-DD (if not in the posting).")

    p = sub.add_parser("list", help="Show your roles, most urgent first.")
    p.add_argument("--all", action="store_true", help="Include rejected, withdrawn and offers.")

    p = sub.add_parser("show", help="Show one role with its skills and checklist.")
    p.add_argument("id", type=int)

    p = sub.add_parser("update", help="Change status, deadline, next action or notes.")
    p.add_argument("id", type=int)
    p.add_argument("--status", choices=store.STATUSES)
    p.add_argument("--deadline")
    p.add_argument("--next", dest="next_action")
    p.add_argument("--next-date", dest="next_action_date")
    p.add_argument("--notes")

    p = sub.add_parser("done", help="Tick (or untick) a checklist step.")
    p.add_argument("id", type=int)
    p.add_argument("step", type=int, help="Step number as shown by 'show'.")

    p = sub.add_parser("match", help="Compare a saved role with your resume (uses project 6).")
    p.add_argument("id", type=int)
    p.add_argument("--resume", required=True)

    args = parser.parse_args()
    try:
        if args.cmd == "add":
            if args.posting:
                posting = Path(args.posting).expanduser().read_text(encoding="utf-8")
            else:
                if sys.stdin.isatty():
                    print("Paste the job posting, then press Ctrl-D:", file=sys.stderr)
                posting = sys.stdin.read()
            if not posting.strip():
                sys.exit("The job posting is empty.")
            print("Reading the posting...", file=sys.stderr)
            job = add_role(posting, args.url, args.deadline)
            print(details(job))
            print(f"\nSaved as id {job['id']} in {store.jobs_file()}", file=sys.stderr)
        elif args.cmd == "list":
            print(table(store.load(), args.all))
        elif args.cmd == "show":
            print(details(store.get(args.id)))
        elif args.cmd == "update":
            job = store.update(args.id, status=args.status, deadline=args.deadline, next_action=args.next_action,
                               next_action_date=args.next_action_date, notes=args.notes)
            print(f"Updated role {job['id']}: {job['role']} at {job['company']} ({job['status']}).")
        elif args.cmd == "done":
            job = store.toggle_step(args.id, args.step - 1)
            step = job["checklist"][args.step - 1]
            print(f"{'Ticked' if step['done'] else 'Unticked'}: {step['step']}")
        elif args.cmd == "match":
            from resume_matcher.main import match_resume, resume_block
            job = store.get(args.id)
            path = Path(args.resume).expanduser()
            if not path.is_file():
                sys.exit(f"Resume not found: {path}")
            print("Comparing your resume with this role...", file=sys.stderr)
            print(match_resume(resume_block(path.read_bytes(), path.name), job["posting"]))
    except ValueError as e:
        sys.exit(str(e))


if __name__ == "__main__":
    main()
