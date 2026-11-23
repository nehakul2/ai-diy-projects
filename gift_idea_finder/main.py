"""Gift idea finder: describe a person and a budget, get five gift ideas with links.

Usage:
    python -m gift_idea_finder.main --who "my sister, 30, just moved to Denver" \\
        --budget "50 USD" --likes "hiking, coffee, crime podcasts"
    python -m gift_idea_finder.main            # asks you each question
"""
import argparse
import sys
from pathlib import Path

from common.claude import WEB_SEARCH, ask
from gift_idea_finder.prompt import SYSTEM


def prompt_for(label: str) -> str:
    try:
        return input(f"{label}: ").strip()
    except EOFError:
        return ""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--who", help="Who the gift is for, e.g. 'my dad, 65, retired teacher'.")
    parser.add_argument("--budget", help="Budget with currency, e.g. '40 GBP' or 'under $100'.")
    parser.add_argument("--likes", help="A few things they like, comma separated.")
    parser.add_argument("--occasion", default="", help="Optional, e.g. 'birthday' or 'thank you'.")
    parser.add_argument("--country", default="", help="Optional: where to shop, e.g. 'UK'.")
    parser.add_argument("-o", "--output", help="Save the result to this Markdown file.")
    args = parser.parse_args()

    who = args.who or prompt_for("Who is the gift for")
    budget = args.budget or prompt_for("Budget (with currency)")
    likes = args.likes or prompt_for("Things they like")
    if not (who and budget and likes):
        sys.exit("Need who the gift is for, a budget, and a few things they like.")

    details = [f"Person: {who}", f"Budget: {budget}", f"They like: {likes}"]
    if args.occasion:
        details.append(f"Occasion: {args.occasion}")
    if args.country:
        details.append(f"Shop in: {args.country}")

    print("Searching for ideas (this can take a minute)...", file=sys.stderr)
    result = ask(SYSTEM, "\n".join(details), tools=[WEB_SEARCH])
    print(result)
    if args.output:
        Path(args.output).write_text(result + "\n", encoding="utf-8")
        print(f"\nSaved to {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
