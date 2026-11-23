"""Scan a folder, ask Claude for a tidy-up plan, check it, apply it, and undo it.

Safety rules:
- Only files directly inside the folder are touched (no subfolders, no hidden files).
- Only file names, sizes and dates are sent to Claude, never file contents.
- Nothing is deleted. Files are only moved/renamed inside the same folder.
- Nothing is ever overwritten; clashes are skipped.
- Every applied plan writes an undo log you can replay.
"""
import json
import re
import time
from datetime import datetime
from pathlib import Path

from common.claude import ask
from downloads_organiser.prompt import SCHEMA, SYSTEM

DEFAULT_LIMIT = 20
UNDO_PREFIX = ".organiser-undo-"
BAD_CHARS = re.compile(r'[/\\:*?"<>|\x00-\x1f]')


def scan(folder: Path, limit: int = DEFAULT_LIMIT) -> list[dict]:
    """The newest `limit` regular files directly inside `folder`."""
    files = [p for p in folder.iterdir() if p.is_file() and not p.is_symlink() and not p.name.startswith(".")]
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    out = []
    for p in files[:limit]:
        st = p.stat()
        out.append({
            "name": p.name,
            "size_kb": round(st.st_size / 1024, 1),
            "modified": datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d"),
        })
    return out


def _safe_name(name: str) -> bool:
    return bool(name) and name not in (".", "..") and not name.startswith(".") and not BAD_CHARS.search(name)


def _taken(target: Path) -> bool:
    """True if the target name exists, ignoring case (macOS treats A.jpg and a.jpg as the same file)."""
    if not target.parent.is_dir():
        return False
    low = target.name.lower()
    return any(p.name.lower() == low for p in target.parent.iterdir())


def check_plan(plan: dict, folder: Path, scanned: list[dict]) -> tuple[list[dict], list[str]]:
    """Keep only safe moves. Returns (moves, warnings)."""
    known = {f["name"] for f in scanned}
    moves, warnings, targets = [], [], set()
    for item in plan.get("files", []):
        cur, new, sub = item["current"], item["new_name"].strip(), item["folder"].strip()
        if cur not in known:
            warnings.append(f"Skipped '{cur}': not one of the scanned files.")
            continue
        if Path(new).suffix.lower() != Path(cur).suffix.lower():
            new = Path(new).stem + Path(cur).suffix  # never change the file type
        if not (_safe_name(new) and _safe_name(sub)):
            warnings.append(f"Skipped '{cur}': unsafe name or folder suggested.")
            continue
        target = folder / sub / new
        key = str(target).lower()
        if key in targets or (sub and _taken(target)):
            warnings.append(f"Skipped '{cur}': '{sub}/{new}' already exists or clashes with another file.")
            continue
        targets.add(key)
        moves.append({"current": cur, "folder": sub, "new_name": new, "reason": item.get("reason", "")})
    return moves, warnings


def make_plan(folder: str, limit: int = DEFAULT_LIMIT) -> dict:
    """Scan and ask Claude. Returns {"folder", "folders", "moves", "warnings", "notes"}. Moves nothing."""
    root = Path(folder).expanduser()
    if not root.is_dir():
        raise ValueError(f"Not a folder: {root}")
    scanned = scan(root, limit)
    if not scanned:
        raise ValueError("No files found directly inside that folder.")
    listing = "\n".join(f"- {f['name']} ({f['size_kb']} KB, modified {f['modified']})" for f in scanned)
    reply = ask(SYSTEM, f"Files in the folder:\n{listing}", schema=SCHEMA)
    plan = json.loads(reply)
    moves, warnings = check_plan(plan, root, scanned)
    return {"folder": str(root), "folders": plan["folders"], "moves": moves,
            "warnings": warnings, "notes": plan.get("notes", "")}


def plan_to_markdown(plan: dict) -> str:
    lines = [f"## Proposed folders in `{plan['folder']}`", ""]
    lines += [f"- **{f['name']}**: {f['purpose']}" for f in plan["folders"]]
    lines += ["", "## Proposed changes", "", "| Current name | New location | Why |", "|---|---|---|"]
    for m in plan["moves"]:
        lines.append(f"| {m['current']} | {m['folder']}/{m['new_name']} | {m['reason']} |")
    if plan["warnings"]:
        lines += ["", "## Skipped", ""] + [f"- {w}" for w in plan["warnings"]]
    if plan["notes"]:
        lines += ["", "## Notes", "", plan["notes"]]
    lines += ["", f"_{len(plan['moves'])} files would move. Nothing has changed yet._"]
    return "\n".join(lines)


def preview(folder: str, limit: int = DEFAULT_LIMIT) -> str:
    """Dry run as Markdown (used by the test page)."""
    return plan_to_markdown(make_plan(folder, limit))


def apply_plan(plan: dict) -> tuple[Path, list[str]]:
    """Move the files. Returns (undo_log_path, messages). Never overwrites, never deletes."""
    root = Path(plan["folder"])
    done, messages = [], []
    for m in plan["moves"]:
        src = root / m["current"]
        dst = root / m["folder"] / m["new_name"]
        if not src.is_file():
            messages.append(f"Skipped '{m['current']}': it's no longer there.")
            continue
        if _taken(dst):
            messages.append(f"Skipped '{m['current']}': '{m['folder']}/{m['new_name']}' now exists.")
            continue
        dst.parent.mkdir(exist_ok=True)
        src.rename(dst)
        done.append({"from": m["current"], "to": f"{m['folder']}/{m['new_name']}"})
    log = root / f"{UNDO_PREFIX}{time.strftime('%Y%m%d-%H%M%S')}.json"
    log.write_text(json.dumps({"folder": str(root), "moves": done}, indent=2), encoding="utf-8")
    messages.insert(0, f"Moved {len(done)} files. Undo log: {log}")
    return log, messages


def undo(log_path: str) -> list[str]:
    """Put files back where they were, using an undo log. Removes folders left empty."""
    log = Path(log_path).expanduser()
    data = json.loads(log.read_text(encoding="utf-8"))
    root = Path(data["folder"])
    messages, restored = [], 0
    for m in reversed(data["moves"]):
        src, dst = root / m["to"], root / m["from"]
        if not src.is_file() or dst.exists():
            messages.append(f"Couldn't restore '{m['from']}' (moved again or name taken).")
            continue
        src.rename(dst)
        restored += 1
        try:
            src.parent.rmdir()  # only succeeds if the folder is now empty
        except OSError:
            pass
    log.rename(log.with_suffix(".undone"))
    messages.insert(0, f"Restored {restored} files.")
    return messages
