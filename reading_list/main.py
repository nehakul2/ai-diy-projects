"""Reading list with a spoken summary: paste links, get key points and a briefing to listen to.

Usage:
    python -m reading_list.main reading_list/examples/links.txt               # summary + script
    python -m reading_list.main reading_list/examples/links.txt --speak       # also read it aloud
    python -m reading_list.main links.txt --save briefing.m4a --minutes 5     # save audio (.wav on Windows/Linux)
    python -m reading_list.main --from-library                                # unread articles from project 9
"""
import argparse
import sys
from pathlib import Path

from reading_list.briefing import from_library, make_briefing, to_markdown


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("file", nargs="?", help="File with links (one per line) and/or article text.")
    parser.add_argument("--from-library", action="store_true",
                        help="Use unread articles from the saved-content organiser (project 9).")
    parser.add_argument("--minutes", type=int, default=3, help="Length of the spoken briefing (default 3).")
    parser.add_argument("--speak", action="store_true", help="Read the briefing aloud.")
    parser.add_argument("--save", help="Save the briefing as audio, e.g. briefing.m4a (Mac) or briefing.wav.")
    args = parser.parse_args()

    try:
        if args.from_library:
            text = from_library()
        elif args.file:
            path = Path(args.file)
            if not path.is_file():
                sys.exit(f"File not found: {path}")
            text = path.read_text(encoding="utf-8", errors="replace")
        else:
            print("Paste links (one per line) or article text, then press Ctrl-D (Ctrl-Z then Enter on Windows):",
                  file=sys.stderr)
            text = sys.stdin.read()
        if args.speak or args.save:
            from reading_list.speech import audio_suffix
            audio_suffix()  # check a voice exists before spending an API call
        print("Reading your list (this can take a minute or two)...", file=sys.stderr)
        briefing = make_briefing(text, args.minutes)
        print(to_markdown(briefing))
        if args.save:
            from reading_list.speech import speak
            speak(briefing["script"], Path(args.save).expanduser())
            print(f"\nSaved audio to {args.save}", file=sys.stderr)
        if args.speak:
            from reading_list.speech import speak
            print("\nReading it aloud (Ctrl-C to stop)...", file=sys.stderr)
            speak(briefing["script"])
    except ValueError as e:
        sys.exit(str(e))
    except KeyboardInterrupt:
        sys.exit("\nStopped.")


if __name__ == "__main__":
    main()
