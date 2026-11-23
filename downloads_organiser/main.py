"""Downloads organiser: suggest clearer file names and a simple folder structure.

Usage:
    python -m downloads_organiser.main ~/Downloads              # preview the newest 20 files
    python -m downloads_organiser.main ~/Downloads --limit 50
    python -m downloads_organiser.main ~/Downloads --apply      # preview, then ask before moving
    python -m downloads_organiser.main --undo ~/Downloads/.organiser-undo-20261123-101500.json
"""
import argparse
import sys

from downloads_organiser.organiser import DEFAULT_LIMIT, apply_plan, make_plan, plan_to_markdown, undo


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("folder", nargs="?", help="Folder to tidy, e.g. ~/Downloads")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT,
                        help=f"How many of the newest files to look at (default {DEFAULT_LIMIT}).")
    parser.add_argument("--apply", action="store_true", help="After the preview, ask to move the files.")
    parser.add_argument("--undo", metavar="LOG", help="Undo a previous run using its undo log file.")
    args = parser.parse_args()

    if args.undo:
        print("\n".join(undo(args.undo)))
        return
    if not args.folder:
        parser.error("give a folder, e.g. ~/Downloads")

    print(f"Looking at the newest {args.limit} files (names, sizes and dates only)...", file=sys.stderr)
    try:
        plan = make_plan(args.folder, args.limit)
    except ValueError as e:
        sys.exit(str(e))
    print(plan_to_markdown(plan))

    if not args.apply:
        print("\nThis was a preview. Run again with --apply to make these changes.", file=sys.stderr)
        return
    if not plan["moves"]:
        print("\nNothing to move.", file=sys.stderr)
        return
    try:
        answer = input(f"\nMove {len(plan['moves'])} files as shown? Type yes to continue: ")
    except EOFError:
        answer = ""
    if answer.strip().lower() != "yes":
        print("No changes made.")
        return
    _, messages = apply_plan(plan)
    print("\n".join(messages))


if __name__ == "__main__":
    main()
