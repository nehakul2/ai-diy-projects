"""Load emails from a pasted text file or a folder of .eml files."""
import email
from email import policy
from pathlib import Path

SEPARATOR = "---"
MAX_BODY_CHARS = 2000  # long newsletters don't need more to be sorted


def from_text(text: str) -> list[str]:
    """Emails pasted into one file, separated by a line containing only ---."""
    chunks, current = [], []
    for line in text.splitlines():
        if line.strip() == SEPARATOR:
            chunks.append("\n".join(current))
            current = []
        else:
            current.append(line)
    chunks.append("\n".join(current))
    return [c.strip()[:MAX_BODY_CHARS] for c in chunks if c.strip()]


def from_eml(path: Path) -> str:
    """One saved email file (most mail apps can drag-and-drop or 'Save as' .eml)."""
    return from_eml_bytes(path.read_bytes())


def from_eml_bytes(data: bytes) -> str:
    """Same as from_eml, for raw bytes (for example an uploaded file)."""
    msg = email.message_from_bytes(data, policy=policy.default)
    body = msg.get_body(preferencelist=("plain", "html"))
    text = body.get_content() if body else ""
    headers = [f"{h}: {msg[h]}" for h in ("From", "Subject", "Date", "List-Unsubscribe") if msg[h]]
    return ("\n".join(headers) + "\n\n" + text.strip())[:MAX_BODY_CHARS]


def load(source: str) -> list[str]:
    path = Path(source)
    if path.is_dir():
        return [from_eml(p) for p in sorted(path.glob("*.eml"))]
    if path.suffix.lower() == ".eml":
        return [from_eml(path)]
    return from_text(path.read_text(encoding="utf-8"))
