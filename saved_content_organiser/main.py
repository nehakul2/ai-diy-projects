"""Saved-content organiser: tag, summarise and remember why you saved things.

Usage:
    python -m saved_content_organiser.main add --url https://example.com/article --note "for the Q1 strategy doc"
    python -m saved_content_organiser.main add --text notes.txt --note "podcast notes from my commute"
    python -m saved_content_organiser.main list [--tag ai] [--kind video] [--search "pricing"] [--all]
    python -m saved_content_organiser.main tags
    python -m saved_content_organiser.main done 4
"""
import argparse
import os
import sys
from pathlib import Path

from saved_content_organiser.library import add_item, card, find, library_file, load, mark, overview, tag_counts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("add", help="Save a link, pasted text or notes.")
    p.add_argument("--url", default="")
    p.add_argument("--text", help="File with pasted text or your notes (e.g. podcast notes).")
    p.add_argument("--note", default="", help="Why you saved it.")
    p.add_argument("--interests", default=os.environ.get("MY_INTERESTS", ""),
                   help="What you care about, so 'why it matters' is personal (or set MY_INTERESTS).")
    p = sub.add_parser("list", help="Show items, newest first.")
    p.add_argument("--tag", default="")
    p.add_argument("--kind", default="")
    p.add_argument("--search", default="", help="Words to look for in titles, summaries and notes.")
    p.add_argument("--all", action="store_true", help="Include items marked done.")
    sub.add_parser("tags", help="Show your tags and how often each is used.")
    p = sub.add_parser("done", help="Mark an item as read/watched.")
    p.add_argument("id", type=int)
    p.add_argument("--undo", action="store_true")
    args = parser.parse_args()

    try:
        if args.cmd == "add":
            text = Path(args.text).expanduser().read_text(encoding="utf-8") if args.text else ""
            if not (args.url or text.strip() or args.note):
                sys.exit("Give --url, --text or --note.")
            print("Reading and summarising...", file=sys.stderr)
            item = add_item(args.url, args.note, text, args.interests)
            print(card(item))
            print(f"\nSaved to {library_file()}", file=sys.stderr)
        elif args.cmd == "list":
            print(overview(find(load(), args.tag, args.search, args.kind, args.all)))
        elif args.cmd == "tags":
            counts = tag_counts(load())
            print("\n".join(f"{t}: {n}" for t, n in counts.most_common()) or "No tags yet.")
        elif args.cmd == "done":
            item = mark(args.id, done=not args.undo)
            print(f"{'Marked done' if item['done'] else 'Marked not done'}: {item['title']}")
    except ValueError as e:
        sys.exit(str(e))


if __name__ == "__main__":
    main()
