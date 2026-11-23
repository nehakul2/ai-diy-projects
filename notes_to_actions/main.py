"""Notes into actions: turn messy notes into a summary, task list and follow-up message.

Usage:
    python -m notes_to_actions.main notes.txt
    python -m notes_to_actions.main notes.txt -o actions.md
    pbpaste | python -m notes_to_actions.main
"""
import argparse
import sys
from pathlib import Path

from common.claude import ask
from notes_to_actions.prompt import SYSTEM


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("file", nargs="?", help="Notes file. Leave out to read from stdin.")
    parser.add_argument("-o", "--output", help="Save the result to this Markdown file.")
    args = parser.parse_args()

    if args.file:
        notes = Path(args.file).read_text(encoding="utf-8")
    else:
        if sys.stdin.isatty():
            print("Paste your notes, then press Ctrl-D (Ctrl-Z then Enter on Windows):", file=sys.stderr)
        notes = sys.stdin.read()

    if not notes.strip():
        sys.exit("No notes given.")

    result = ask(SYSTEM, f"<notes>\n{notes}\n</notes>")
    print(result)
    if args.output:
        Path(args.output).write_text(result + "\n", encoding="utf-8")
        print(f"\nSaved to {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
