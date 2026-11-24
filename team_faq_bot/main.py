"""Team FAQ bot with sources: ask questions about your team's docs and get cited answers.

Usage:
    python -m team_faq_bot.main "How many holiday days can I carry over?"            # example handbook
    python -m team_faq_bot.main --docs ~/Documents/team-handbook "Who approves expenses over $75?"
    python -m team_faq_bot.main --docs ~/Documents/team-handbook        # chat: keep asking questions
    python -m team_faq_bot.main --gaps                                  # questions the docs couldn't answer

Reads .md, .txt and .html files (and .pdf with `pip install pypdf`) in the folder and its subfolders.
"""
import argparse
import sys

from common.answer import to_markdown
from common.search import Index
from team_faq_bot.bot import EXAMPLE_DOCS, ask_faq, gaps_report, load_gaps


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("question", nargs="?", help="Your question. Leave out to chat.")
    parser.add_argument("--docs", default=str(EXAMPLE_DOCS), help="Folder of team documents (default: example).")
    parser.add_argument("--gaps", action="store_true", help="Show questions the documents couldn't answer.")
    args = parser.parse_args()

    if args.gaps:
        print(gaps_report(load_gaps()))
        return
    try:
        index = Index.from_folder(args.docs)
    except ValueError as e:
        sys.exit(str(e))
    print(f"Loaded {len(index.files())} documents ({len(index.passages)} passages).", file=sys.stderr)
    for s in index.skipped:
        print(s, file=sys.stderr)
    try:
        if args.question:
            print(to_markdown(ask_faq(index, args.question, args.docs)))
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
            result = ask_faq(index, q, args.docs, history)
            print("\n" + to_markdown(result))
            history.append((q, result["answer"]))
    except ValueError as e:
        sys.exit(str(e))
    except KeyboardInterrupt:
        print()


if __name__ == "__main__":
    main()
