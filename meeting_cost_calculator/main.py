"""Meeting cost calculator: see what your recurring meetings cost and where to cut.

Usage:
    python -m meeting_cost_calculator.main meeting_cost_calculator/examples/team_meetings.txt --rate 75
    python -m meeting_cost_calculator.main meetings.csv --rate 60 --no-advice     # maths only, no API call
    python -m meeting_cost_calculator.main calendar.ics --rate 90 --currency "£" --context "8-person product team"

Input can be a plain description of your meetings, a calendar export (.ics), or a CSV
with columns title, minutes, attendees, per_month.
"""
import argparse
import sys
from pathlib import Path

from meeting_cost_calculator.costs import add_costs, extract_meetings, get_advice, looks_like_csv, report


def calculate(text: str, rate: float, currency: str = "$", context: str = "", advice: bool = True) -> str:
    """Plain function used by the CLI and the test page. Returns a Markdown report."""
    if rate <= 0:
        raise ValueError("Hourly rate must be more than 0.")
    if not advice and not looks_like_csv(text):
        raise ValueError("Without advice, give a CSV (title, minutes, attendees, per_month) "
                         "so the meetings can be read without Claude.")
    meetings = extract_meetings(text)
    if advice:
        result = get_advice(meetings, rate, context)
        return report(result["meetings"], rate, currency, result["summary"])
    return report(add_costs(meetings, rate), rate, currency)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("file", nargs="?", help="Meetings file (text, .ics or .csv). Omit to type or paste them.")
    parser.add_argument("--rate", type=float, required=True,
                        help="Average cost of one person's hour (salary plus overheads), e.g. 75.")
    parser.add_argument("--currency", default="$")
    parser.add_argument("--context", default="", help="A line about your team, e.g. '6 engineers, remote'.")
    parser.add_argument("--no-advice", action="store_true", help="Only do the maths (CSV input, no API call).")
    args = parser.parse_args()

    if args.file:
        path = Path(args.file)
        if not path.is_file():
            sys.exit(f"File not found: {path}")
        text = path.read_text(encoding="utf-8", errors="replace")
    else:
        print("Describe your recurring meetings, then press Ctrl-D (Ctrl-Z then Enter on Windows):",
              file=sys.stderr)
        text = sys.stdin.read()
    try:
        if not args.no_advice:
            print("Reading your meetings and looking for savings...", file=sys.stderr)
        print(calculate(text, args.rate, args.currency, args.context, advice=not args.no_advice))
    except ValueError as e:
        sys.exit(str(e))


if __name__ == "__main__":
    main()
