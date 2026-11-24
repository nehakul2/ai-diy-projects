"""Find the most relevant passages in a folder of documents, using only the standard library.

Used by the team FAQ bot (project 17) and ask-your-notes (project 18).
Documents are split into passages (by headings, then by size) and ranked with BM25,
a classic keyword-search formula. No embeddings or extra services needed.
"""
import html
import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

TEXT_TYPES = {".md", ".markdown", ".txt", ".text", ".rst", ".csv", ".html", ".htm"}
MAX_WORDS = 350
STOP = set("""a an and are as at be but by can do does for from has have how i if in into is it its me my of on or
our so that the their them then there these they this to was we what when where which who why will with you your
should would could may might must not no yes am been being did doing had having he her his she than too very""".split())


@dataclass
class Passage:
    id: int
    source: str   # file path relative to the folder
    heading: str
    text: str


def words(text: str) -> list[str]:
    return [w for w in re.findall(r"[a-z0-9]+(?:'[a-z]+)?", text.lower()) if w not in STOP and len(w) > 1]


def _stem(w: str) -> str:
    for suffix in ("ing", "ies", "ed", "es", "s"):
        if len(w) > len(suffix) + 3 and w.endswith(suffix):
            return w[: -len(suffix)] + ("y" if suffix == "ies" else "")
    return w


def terms(text: str) -> list[str]:
    return [_stem(w) for w in words(text)]


def read_file(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError:
            raise ValueError(f"Skipped {path.name}: reading PDFs needs `pip install pypdf`.") from None
        return "\n\n".join(page.extract_text() or "" for page in PdfReader(str(path)).pages)
    text = path.read_text(encoding="utf-8", errors="replace")
    if suffix in (".html", ".htm"):
        text = re.sub(r"(?is)<(script|style).*?</\1>", " ", text)
        text = re.sub(r"(?i)<h[1-6][^>]*>", "\n# ", text)
        text = html.unescape(re.sub(r"<[^>]+>", " ", text))
    return text


def split(text: str, max_words: int = MAX_WORDS) -> list[tuple[str, str]]:
    """Split into (heading, passage) pairs: at Markdown headings, then into ~max_words pieces by paragraph."""
    sections: list[tuple[str, list[str]]] = [("", [])]
    for line in text.splitlines():
        m = re.match(r"^\s{0,3}#{1,6}\s+(.*)", line)
        if m:
            sections.append((m.group(1).strip(), []))
        else:
            sections[-1][1].append(line)
    out = []
    for heading, lines in sections:
        paras = [p.strip() for p in re.split(r"\n\s*\n", "\n".join(lines)) if p.strip()]
        chunk: list[str] = []
        for p in paras:
            if chunk and len(" ".join(chunk + [p]).split()) > max_words:
                out.append((heading, "\n\n".join(chunk)))
                chunk = []
            chunk.append(p)
        if chunk:
            out.append((heading, "\n\n".join(chunk)))
    return out


class Index:
    """BM25 index over passages from a folder (recursively) or from given (source, text) pairs."""

    def __init__(self, passages: list[Passage], skipped: list[str] | None = None):
        self.passages = passages
        self.skipped = skipped or []
        self._tf = [Counter(terms(p.heading + " " + p.heading + " " + p.text + " " + Path(p.source).stem))
                    for p in passages]
        self._len = [sum(tf.values()) for tf in self._tf]
        self._avg = sum(self._len) / len(self._len) if passages else 0
        df = Counter(t for tf in self._tf for t in tf)
        n = len(passages)
        self._idf = {t: math.log(1 + (n - d + 0.5) / (d + 0.5)) for t, d in df.items()}

    @classmethod
    def from_texts(cls, items: list[tuple[str, str]], skipped: list[str] | None = None) -> "Index":
        passages = []
        for source, text in items:
            for heading, chunk in split(text):
                passages.append(Passage(len(passages) + 1, source, heading, chunk))
        return cls(passages, skipped)

    @classmethod
    def from_folder(cls, folder: str | Path, max_files: int = 2000) -> "Index":
        root = Path(folder).expanduser()
        if not root.is_dir():
            raise ValueError(f"Not a folder: {root}")
        files = sorted(p for p in root.rglob("*") if p.is_file() and not any(part.startswith(".") for part in
                       p.relative_to(root).parts) and p.suffix.lower() in TEXT_TYPES | {".pdf"})
        if not files:
            raise ValueError(f"No documents (.md, .txt, .html, .pdf) found in {root}.")
        if len(files) > max_files:
            raise ValueError(f"{len(files)} files is more than {max_files}. Point it at a smaller folder.")
        items, skipped = [], []
        for f in files:
            try:
                items.append((str(f.relative_to(root)), read_file(f)))
            except (ValueError, OSError) as e:
                skipped.append(str(e))
            except Exception as e:  # e.g. a damaged PDF
                skipped.append(f"Skipped {f.name}: {e}")
        return cls.from_texts(items, skipped)

    def search(self, query: str, k: int = 6) -> list[Passage]:
        q = terms(query)
        if not q or not self.passages:
            return []
        k1, b = 1.5, 0.75
        scores = []
        for i, tf in enumerate(self._tf):
            s = 0.0
            for t in q:
                f = tf.get(t)
                if f:
                    s += self._idf[t] * f * (k1 + 1) / (f + k1 * (1 - b + b * self._len[i] / self._avg))
            if s > 0:
                scores.append((s, i))
        return [self.passages[i] for _, i in sorted(scores, reverse=True)[:k]]

    def files(self) -> list[str]:
        return sorted({p.source for p in self.passages})
