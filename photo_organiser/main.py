"""Photo organiser by event: sort a folder of photos into folders like "2026-07-14 Beach day in Santa Cruz".

Usage:
    python -m photo_organiser.main ~/Pictures/Unsorted                  # preview only, moves nothing
    python -m photo_organiser.main ~/Pictures/Unsorted --apply          # preview, then ask before moving
    python -m photo_organiser.main ~/Pictures/Unsorted --no-thumbnails  # don't send any images to Claude
    python -m photo_organiser.main ~/Pictures/Unsorted --no-ai          # date-only folder names, no API call
    python -m photo_organiser.main --undo ~/Pictures/Unsorted/.organiser-undo-20261123-101500.json
"""
import argparse
import sys

from photo_organiser.organiser import apply_plan, make_plan, plan_to_markdown, undo


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("folder", nargs="?", help="Folder with photos (only files directly inside it).")
    parser.add_argument("--gap", type=float, default=6,
                        help="Hours between photos that start a new event (default 6).")
    parser.add_argument("--min-photos", type=int, default=3,
                        help="Smaller groups go into a monthly 'Other photos' folder (default 3).")
    parser.add_argument("--no-thumbnails", action="store_true", help="Name events from dates and GPS only.")
    parser.add_argument("--no-ai", action="store_true", help="Use dates only as folder names.")
    parser.add_argument("--apply", action="store_true", help="After the preview, ask to move the files.")
    parser.add_argument("--undo", metavar="LOG", help="Undo a previous run using its undo log file.")
    args = parser.parse_args()

    if args.undo:
        print("\n".join(undo(args.undo)))
        return
    if not args.folder:
        parser.error("give a folder, or --undo LOG")
    try:
        if not args.no_ai:
            print("Reading photo dates and naming events (this can take a minute)...", file=sys.stderr)
        plan = make_plan(args.folder, args.gap, args.min_photos, use_ai=not args.no_ai,
                         thumbnails=not args.no_thumbnails)
    except ValueError as e:
        sys.exit(str(e))
    print(plan_to_markdown(plan))
    if not plan["moves"]:
        print("\nNothing to move.", file=sys.stderr)
        return
    if not args.apply:
        print("\nThis was a preview. Run again with --apply to make these changes.", file=sys.stderr)
        return
    answer = input(f"\nMove {len(plan['moves'])} files into {len(plan['events'])} folders? Type yes to continue: ")
    if answer.strip().lower() != "yes":
        print("Nothing moved.")
        return
    _, messages = apply_plan(plan)
    print("\n".join(messages))


if __name__ == "__main__":
    main()
