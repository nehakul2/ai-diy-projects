"""Team FAQ bot: answers questions from your team's documents, always with sources.

Questions it can't answer are logged, so you can see which docs are missing.
Log: ~/.ai-diy-projects/faq-gaps.json (set FAQ_GAPS_FILE to change it).
"""
import json
import os
from collections import Counter
from datetime import datetime
from pathlib import Path

from common.answer import answer
from common.search import Index

EXAMPLE_DOCS = Path(__file__).parent / "examples" / "handbook"

SYSTEM = """You are a friendly internal helpdesk for a team. People ask about policies,
processes and how things work, and you answer from the team's own documents so they
don't have to dig through them. Be direct: lead with the answer (a number, a yes/no,
a deadline), then any conditions. Point people to the right person or channel when
the documents name one."""


def gaps_file() -> Path:
    return Path(os.environ.get("FAQ_GAPS_FILE", Path.home() / ".ai-diy-projects" / "faq-gaps.json")).expanduser()


def load_gaps() -> list[dict]:
    p = gaps_file()
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else []


def log_gap(question: str, docs: str) -> None:
    p = gaps_file()
    p.parent.mkdir(parents=True, exist_ok=True)
    gaps = load_gaps() + [{"question": question.strip(), "docs": docs,
                           "when": datetime.now().isoformat(timespec="minutes")}]
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(gaps[-500:], indent=2), encoding="utf-8")
    tmp.replace(p)


def ask_faq(index: Index, question: str, docs: str = "", history: list[tuple[str, str]] | None = None) -> dict:
    result = answer(index, question, SYSTEM, history=history)
    if not result["found"]:
        log_gap(question, docs)
    return result


def gaps_report(gaps: list[dict]) -> str:
    if not gaps:
        return "No unanswered questions logged yet."
    counts = Counter(g["question"].lower().rstrip("?") for g in gaps)
    lines = [f"**{len(gaps)} questions the documents couldn't answer** (most asked first). "
             "Adding docs for these will help the most.", ""]
    lines += [f"- {q}?" + (f" (asked {n} times)" if n > 1 else "") for q, n in counts.most_common(30)]
    return "\n".join(lines)
