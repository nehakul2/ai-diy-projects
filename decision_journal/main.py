"""Decision journal pattern finder: log decisions and assumptions, review them later, spot patterns.

Usage:
    python -m decision_journal.main log --decision "Accept the team lead role" --context "..." \\
        --options "stay IC; take lead role" --expected "more impact, less coding" --confidence 70
    python -m decision_journal.main list
    python -m decision_journal.main due                  # decisions ready to review
    python -m decision_journal.main review 1 --outcome worse --what "..." --assumptions "..." --lesson "..."
    python -m decision_journal.main patterns             # needs 3+ reviewed decisions
    python -m decision_journal.main samples              # try it with 5 sample decisions
"""
import argparse
import sys

from decision_journal.journal import (OUTCOMES, card, decisions_file, due, find_patterns, get, load,
                                      load_samples, log_decision, record_review)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("log", help="Log a decision (Claude adds assumptions and signals to watch).")
    p.add_argument("--decision", required=True)
    p.add_argument("--context", default="", help="What's going on and why now.")
    p.add_argument("--options", default="", help="Options you considered.")
    p.add_argument("--expected", default="", help="What you expect to happen.")
    p.add_argument("--confidence", type=int, default=70, help="0-100, how sure you are it's right (default 70).")
    p.add_argument("--review-on", default="", help="Date to review it, YYYY-MM-DD (default: suggested by Claude).")
    p.add_argument("--no-ai", action="store_true", help="Just save it, without asking Claude.")
    p = sub.add_parser("list", help="Show all decisions.")
    sub.add_parser("due", help="Show decisions whose review date has come.")
    p = sub.add_parser("show")
    p.add_argument("id", type=int)
    p = sub.add_parser("review", help="Record what actually happened.")
    p.add_argument("id", type=int)
    p.add_argument("--outcome", required=True, choices=OUTCOMES)
    p.add_argument("--what", required=True, help="What happened.")
    p.add_argument("--assumptions", default="", help="Which assumptions held or failed.")
    p.add_argument("--lesson", default="")
    sub.add_parser("patterns", help="Find patterns across reviewed decisions.")
    sub.add_parser("samples", help="Fill an empty journal with 5 sample decisions to try things out.")
    args = parser.parse_args()

    try:
        if args.cmd == "log":
            if not args.no_ai:
                print("Finding assumptions and signals to watch...", file=sys.stderr)
            d = log_decision(args.decision, args.context, args.options, args.expected, args.confidence,
                             args.review_on, sharpen=not args.no_ai)
            print(card(d))
            print(f"\nSaved to {decisions_file()}. Review it on {d['review_on']}.", file=sys.stderr)
        elif args.cmd == "list":
            items = load()
            print("\n\n---\n\n".join(card(d) for d in items) or "No decisions logged yet.")
        elif args.cmd == "due":
            items = due(load())
            print("\n".join(f"{d['id']}. {d['decision']} (review was due {d['review_on']})" for d in items)
                  or "Nothing due for review.")
        elif args.cmd == "show":
            print(card(get(args.id)))
        elif args.cmd == "review":
            d = record_review(args.id, args.outcome, args.what, args.assumptions, args.lesson)
            print(card(d))
        elif args.cmd == "patterns":
            print("Looking for patterns (this can take a minute)...", file=sys.stderr)
            print(find_patterns(load()))
        elif args.cmd == "samples":
            print(f"Added {load_samples()} sample decisions to {decisions_file()}.")
    except ValueError as e:
        sys.exit(str(e))


if __name__ == "__main__":
    main()
