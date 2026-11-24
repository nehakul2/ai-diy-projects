"""Content-idea research assistant: find timely, scored post ideas for your niche, then draft them.

Usage:
    python -m content_ideas.main research --niche "AI for product managers" --audience "PMs at startups" \\
        --platform LinkedIn --past content_ideas/examples/past_posts.txt
    python -m content_ideas.main list                 # your idea bank, best first
    python -m content_ideas.main show 3
    python -m content_ideas.main draft 3 --past content_ideas/examples/past_posts.txt
    python -m content_ideas.main status 3 posted      # new, drafted, posted or skipped
"""
import argparse
import sys
from pathlib import Path

from content_ideas.ideas import bank_table, card, draft, get, ideas_file, load, research, set_status
from content_ideas.prompt import PLATFORMS


def _read(path: str | None) -> str:
    if not path:
        return ""
    p = Path(path).expanduser()
    if not p.is_file():
        sys.exit(f"File not found: {p}")
    return p.read_text(encoding="utf-8", errors="replace")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("research", help="Search what's being discussed and suggest scored ideas.")
    p.add_argument("--niche", required=True, help="What you create content about.")
    p.add_argument("--audience", default="", help="Who you're writing for.")
    p.add_argument("--platform", default="LinkedIn", choices=PLATFORMS)
    p.add_argument("--past", help="Text file with a few of your past posts (for voice and to avoid repeats).")
    p.add_argument("--count", type=int, default=5, help="How many ideas (1-10, default 5).")
    p.add_argument("--no-save", action="store_true", help="Don't add the ideas to your idea bank.")
    p = sub.add_parser("list", help="Show your idea bank.")
    p.add_argument("--all", action="store_true", help="Include posted and skipped ideas.")
    p = sub.add_parser("show")
    p.add_argument("id", type=int)
    p = sub.add_parser("draft", help="Write a first draft of a saved idea.")
    p.add_argument("id", type=int)
    p.add_argument("--past", help="Text file with your past posts, to match your voice.")
    p.add_argument("--platform", choices=PLATFORMS, help="Draft for a different platform than the idea's.")
    p = sub.add_parser("status")
    p.add_argument("id", type=int)
    p.add_argument("status", choices=["new", "drafted", "posted", "skipped"])
    args = parser.parse_args()

    try:
        if args.cmd == "research":
            past = _read(args.past)
            print("Researching what your audience is talking about (this can take a couple of minutes)...",
                  file=sys.stderr)
            found = research(args.niche, args.audience, args.platform, past, args.count, keep=not args.no_save)
            print("\n\n".join(card(i) for i in found))
            if not args.no_save:
                print(f"\nSaved to your idea bank ({ideas_file()}). Draft one with: draft <id>", file=sys.stderr)
        elif args.cmd == "list":
            print(bank_table(load(), args.all))
        elif args.cmd == "show":
            print(card(get(args.id)))
        elif args.cmd == "draft":
            past = _read(args.past)
            print("Writing a first draft...", file=sys.stderr)
            print(draft(args.id, past, args.platform or ""))
        elif args.cmd == "status":
            i = set_status(args.id, args.status)
            print(f"Idea {i['id']} is now {i['status']}.")
    except ValueError as e:
        sys.exit(str(e))


if __name__ == "__main__":
    main()
