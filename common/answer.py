"""Answer a question from retrieved passages, with numbered citations. Shared by projects 17 and 18."""
import json

from common.claude import ask
from common.search import Index, Passage

ANSWER_SCHEMA = {
    "type": "object",
    "properties": {
        "answer": {"type": "string"},
        "used": {"type": "array", "items": {"type": "integer"}},
        "found": {"type": "boolean"},
        "follow_up": {"type": "string"},
    },
    "required": ["answer", "used", "found", "follow_up"],
    "additionalProperties": False,
}

RULES = """Answer ONLY from the numbered passages below. Cite them inline like [2] or [1][3]
after the sentences they support, and list every passage you used in `used`.
If the passages don't contain the answer, set found=false and say plainly that the
documents don't cover it (mention anything partly relevant), instead of guessing.
If passages disagree, say so and cite both. Keep it short and practical.
follow_up: one natural next question the person might ask, or empty."""


def build_prompt(question: str, passages: list[Passage], history: list[tuple[str, str]] | None = None) -> str:
    parts = []
    if history:
        parts.append("Earlier in this conversation:\n" + "\n".join(f"Q: {q}\nA: {a}" for q, a in history[-3:]))
    parts.append("Passages:\n\n" + "\n\n".join(
        f"[{n}] {p.source}" + (f" > {p.heading}" if p.heading else "") + f"\n{p.text}"
        for n, p in enumerate(passages, 1)))
    parts.append(f"Question: {question}")
    return "\n\n---\n\n".join(parts)


def answer(index: Index, question: str, system: str, k: int = 6,
           history: list[tuple[str, str]] | None = None) -> dict:
    """Returns {"answer", "found", "follow_up", "sources": [{"n", "source", "heading", "text"}]}."""
    if not question.strip():
        raise ValueError("Type a question.")
    # Include the last question in the search so follow-ups like "and for contractors?" still find context.
    query = question + (" " + history[-1][0] if history else "")
    passages = index.search(query, k)
    if not passages:
        return {"answer": "I couldn't find anything about that in the documents.", "found": False,
                "follow_up": "", "sources": []}
    data = json.loads(ask(system + "\n\n" + RULES, build_prompt(question, passages, history),
                          schema=ANSWER_SCHEMA, effort="low"))
    used = [n for n in dict.fromkeys(data["used"]) if 1 <= n <= len(passages)]
    sources = [{"n": n, "source": passages[n - 1].source, "heading": passages[n - 1].heading,
                "text": passages[n - 1].text} for n in used]
    return {"answer": data["answer"], "found": data["found"], "follow_up": data["follow_up"], "sources": sources}


def to_markdown(result: dict, snippet_words: int = 40) -> str:
    lines = [result["answer"]]
    if result["sources"]:
        lines += ["", "**Sources**"]
        for s in result["sources"]:
            where = s["source"] + (f" › {s['heading']}" if s["heading"] else "")
            words = s["text"].split()
            snippet = " ".join(words[:snippet_words]) + (" …" if len(words) > snippet_words else "")
            lines.append(f"- [{s['n']}] **{where}**: _{snippet}_")
    if result.get("follow_up"):
        lines += ["", f"_You could also ask: {result['follow_up']}_"]
    return "\n".join(lines)
