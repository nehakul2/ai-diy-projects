"""Inbox clean-up helper: sort a batch of emails into reply, keep, archive or unsubscribe.

Usage:
    python -m inbox_cleanup.main emails.txt          # pasted emails separated by ---
    python -m inbox_cleanup.main saved_emails/       # a folder of .eml files
    python -m inbox_cleanup.main emails.txt -o plan.md
"""
import argparse
import sys
from pathlib import Path

from common.claude import ask
from inbox_cleanup.emails import load
from inbox_cleanup.prompt import SYSTEM

MAX_EMAILS = 50


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("source", help="A .txt file of pasted emails, an .eml file, or a folder of .eml files.")
    parser.add_argument("-o", "--output", help="Save the result to this Markdown file.")
    args = parser.parse_args()

    if not Path(args.source).exists():
        sys.exit(f"Not found: {args.source}")
    emails = load(args.source)
    if not emails:
        sys.exit("No emails found. Separate pasted emails with a line containing only ---")
    if len(emails) > MAX_EMAILS:
        print(f"Found {len(emails)} emails; sorting the first {MAX_EMAILS}. Start small!", file=sys.stderr)
        emails = emails[:MAX_EMAILS]

    batch = "\n\n".join(f'<email number="{i}">\n{e}\n</email>' for i, e in enumerate(emails, 1))
    print(f"Sorting {len(emails)} emails...", file=sys.stderr)
    result = ask(SYSTEM, batch)
    print(result)
    if args.output:
        Path(args.output).write_text(result + "\n", encoding="utf-8")
        print(f"\nSaved to {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
