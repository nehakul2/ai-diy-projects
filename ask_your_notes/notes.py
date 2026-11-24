"""Ask questions across your own notes, saved articles and decisions, with sources.

Sources:
- a notes folder (Obsidian, Markdown, plain text, exported Notion/Google Docs, PDFs with pypdf)
- optionally your saved-content library (project 9) and decision journal (project 10)
"""
from pathlib import Path

from common.answer import answer
from common.search import Index

EXAMPLE_NOTES = Path(__file__).parent / "examples" / "notes"
EXTRAS = ["library", "decisions"]
EXTRA_NAMES = {"library": "saved-content library", "decisions": "decision journal"}

SYSTEM = """You help someone remember and connect what's in their own notes. Answer like a
thoughtful assistant who has read everything they wrote: specific, with dates and numbers
from the notes when present. If notes from different times disagree (a plan changed),
give the latest and mention the earlier one. Connect related notes when it helps
("you also wrote..."). Speak to them as "you"."""


def _library_texts() -> list[tuple[str, str]]:
    from saved_content_organiser.library import card, load
    return [(f"saved library/{i['id']}. {i['title'][:60]}", f"Saved {i.get('added', '')}\n" + card(i).replace("### ", "# ", 1))
            for i in load()]


def _decision_texts() -> list[tuple[str, str]]:
    from decision_journal.journal import card, load
    return [(f"decision journal/{d['id']}. {d['decision'][:60]}", card(d).replace("### ", "# ", 1)) for d in load()]


def build_index(folder: str = "", extras: list[str] | None = None) -> Index:
    """Index the notes folder plus any extras ("library", "decisions")."""
    extras = extras or []
    texts: list[tuple[str, str]] = []
    skipped: list[str] = []
    if folder:
        notes = Index.from_folder(folder)
        skipped += notes.skipped
        texts += [(p.source, (f"# {p.heading}\n" if p.heading else "") + p.text) for p in notes.passages]
    for extra in extras:
        if extra not in EXTRAS:
            raise ValueError(f"Extra sources can be: {', '.join(EXTRAS)}")
        try:
            got = _library_texts() if extra == "library" else _decision_texts()
        except Exception as e:  # a broken data file shouldn't stop the rest
            skipped.append(f"Couldn't read your {EXTRA_NAMES[extra]}: {e}")
            continue
        if not got:
            skipped.append(f"Your {EXTRA_NAMES[extra]} is empty.")
        texts += got
    if not texts:
        raise ValueError("Nothing to search. Choose a notes folder or include your library or decisions.")
    return Index.from_texts(texts, skipped)


def ask_notes(index: Index, question: str, history: list[tuple[str, str]] | None = None) -> dict:
    return answer(index, question, SYSTEM, k=8, history=history)
