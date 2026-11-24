"""Personal agent: chat with one assistant that uses all your projects.

Usage:
    python -m personal_agent.main                           # chat in Terminal
    python -m personal_agent.main "gift ideas for my dad, $60, loves gardening"   # one question

Type 'help' to see what it can do, or an empty line to quit. Files: type or drag in a path,
e.g. "explain my spending in ~/Downloads/statement.csv".
"""
import argparse
import sys

from personal_agent.agent import Agent, describe_tools


def show(agent: Agent, text: str) -> None:
    try:
        result = agent.send(text, on_tool=lambda label: print(f"  ...using {label}", file=sys.stderr))
    except SystemExit as e:  # API problems (bad key, no internet) come back as a plain message
        print(f"\n{e.code}")
        return
    for label, output, ok in result["results"]:
        print(f"\n--- {label}{'' if ok else ' (failed)'} ---\n{output}")
    print(f"\n{result['reply']}")
    while agent.pending:
        answer = input(f"\n{agent.pending['question']} (yes/no) ").strip().lower()
        print(agent.answer_confirmation(answer in ("y", "yes")))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("message", nargs="*", help="Ask one thing and exit. Leave out to chat.")
    args = parser.parse_args()
    agent = Agent()
    if args.message:
        show(agent, " ".join(args.message))
        return
    print("Hi! What can I help with? ('help' for ideas, empty line to quit)", file=sys.stderr)
    while True:
        try:
            text = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not text:
            break
        if text.lower() == "help":
            print(f"I can use: {describe_tools()}.")
            continue
        show(agent, text)


if __name__ == "__main__":
    main()
