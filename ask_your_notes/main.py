"""Ask-your-notes assistant: ask questions across your notes and get answers with sources.

Usage:
    python -m ask_your_notes.main "What did I learn about habits?"                 # example notes
    python -m ask_your_notes.main --notes ~/Documents/Obsidian "When is my Lisbon trip?"
    python -m ask_your_notes.main --notes ~/Notes --include library,decisions      # chat across everything
    python -m ask_your_notes.main --include library "What have I saved about focus?"

Reads .md, .txt and .html files (and .pdf with `pip install pypdf`) in the folder and its subfolders.
--include adds your saved-content library (project 9) and/or decision journal (project 10).
"""
import argparse
import sys

from ask_your_notes.notes import EXAMPLE_NOTES, EXTRAS, ask_notes, build_index
from common.answer import to_markdown


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("question", nargs="?", help="Your question. Leave out to chat.")
    parser.add_argument("--notes", help="Notes folder (default: the example notes, unless --include is used).")
    parser.add_argument("--include", default="", help=f"Extra sources, comma separated: {','.join(EXTRAS)}.")
    args = parser.parse_args()

    include = [x.strip() for x in args.include.split(",") if x.strip()]
    folder = args.notes or ("" if include else str(EXAMPLE_NOTES))
    try:
        index = build_index(folder, include)
    except ValueError as e:
        sys.exit(str(e))
    print(f"Searching {len(index.files())} notes and items ({len(index.passages)} passages).", file=sys.stderr)
    for s in index.skipped:
        print(s, file=sys.stderr)
    try:
        if args.question:
            print(to_markdown(ask_notes(index, args.question)))
            return
        history: list[tuple[str, str]] = []
        print("Ask a question (empty line or Ctrl-D to quit).", file=sys.stderr)
        while True:
            try:
                q = input("\n> ").strip()
            except EOFError:
                break
            if not q:
                break
            result = ask_notes(index, q, history)
            print("\n" + to_markdown(result))
            history.append((q, result["answer"]))
    except ValueError as e:
        sys.exit(str(e))
    except KeyboardInterrupt:
        print()


if __name__ == "__main__":
    main()
