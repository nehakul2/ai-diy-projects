"""Personal finance explainer: turn a bank export into a plain-English picture of your spending.

Usage:
    python -m finance_explainer.main finance_explainer/examples/sample_bank_export.csv
    python -m finance_explainer.main ~/Downloads/statement.csv --currency "£" --day-first
    python -m finance_explainer.main statement.csv --context "Family of 3, rent is split with a flatmate"
"""
import argparse
import sys
from pathlib import Path

from finance_explainer.analysis import categorise, explain, summarise, tables
from finance_explainer.bank import read_export


def explain_export(text: str, currency: str = "$", day_first: bool = False, context: str = "") -> str:
    """Plain function used by the CLI and the test page. Returns a Markdown report."""
    txns, notes = read_export(text, day_first)
    summary = summarise(txns, categorise(txns))
    parts = [explain(summary, currency, context), tables(summary, currency)]
    if notes:
        parts.append("**Notes on reading your file:**\n" + "\n".join(f"- {n}" for n in notes))
    parts.append("_This is a plain-English explanation of your spending, not financial advice._")
    return "\n\n".join(parts)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("file", help="CSV export of transactions from your bank or card.")
    parser.add_argument("--currency", default="$")
    parser.add_argument("--day-first", action="store_true", help="Dates are day/month (e.g. UK, India, Europe).")
    parser.add_argument("--context", default="", help="Anything that helps, e.g. 'rent is paid from another account'.")
    args = parser.parse_args()
    path = Path(args.file).expanduser()
    if not path.is_file():
        sys.exit(f"File not found: {path}")
    try:
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        print("Reading transactions and explaining your spending (this can take a minute)...", file=sys.stderr)
        print(explain_export(text, args.currency, args.day_first, args.context))
    except ValueError as e:
        sys.exit(str(e))


if __name__ == "__main__":
    main()
