"""Where the projects keep their data (job tracker, library, decisions, idea bank).

On your own computer: JSON files in ~/.ai-diy-projects/, exactly as before.

In the shared version (AGENT_HOSTED=1) with DATABASE_URL set: one database row per
person and per project, so every friend has their own data. The signed-in person is
set with `as_user(...)` around each chat message.

DATABASE_URL is a Postgres connection link (for example from Supabase), or
sqlite:///path/to/file.db for testing.
"""
import contextvars
import hashlib
import hmac
import json
import os
import re
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

_user = contextvars.ContextVar("storage_user", default=None)


def database_url() -> str:
    return os.environ.get("DATABASE_URL", "").strip()


def hosted() -> bool:
    return os.environ.get("AGENT_HOSTED", "").strip().lower() in ("1", "true", "yes")


def per_user() -> bool:
    """True when data should go to the database for the signed-in person."""
    return hosted() and bool(database_url())


@contextmanager
def as_user(user_id: str):
    token = _user.set(user_id)
    try:
        yield
    finally:
        _user.reset(token)


def _current_user() -> str:
    user = _user.get()
    if not user:
        raise ValueError("Please sign in first.")
    return user


# ---------- database plumbing (Postgres, or SQLite for tests) ----------
SCHEMA = [
    "CREATE TABLE IF NOT EXISTS agent_users (user_id TEXT PRIMARY KEY, passcode_hash TEXT NOT NULL, "
    "created TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS agent_data (user_id TEXT NOT NULL, name TEXT NOT NULL, data TEXT NOT NULL, "
    "updated TEXT NOT NULL, PRIMARY KEY (user_id, name))",
]
_ready = False


@contextmanager
def _connect():
    """A short-lived connection per call (simple and safe with several visitors at once)."""
    url = database_url()
    if url.startswith("sqlite:///"):
        conn = sqlite3.connect(url.removeprefix("sqlite:///"))
        try:
            yield conn, "?"
            conn.commit()
        finally:
            conn.close()
        return
    import psycopg  # only needed for the shared version
    # prepare_threshold=None: Supabase's connection pooler doesn't support prepared statements.
    with psycopg.connect(url, autocommit=True, connect_timeout=10, prepare_threshold=None) as conn:
        yield conn, "%s"


def _run(sql: str, params: tuple = (), fetch: bool = False):
    global _ready
    with _connect() as (conn, mark):
        if not _ready:
            for statement in SCHEMA:
                conn.execute(statement)
            _ready = True
        cur = conn.execute(sql.replace("?", mark), params)
        return cur.fetchone() if fetch else None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ---------- the two functions the projects use ----------
def read_json(name: str, path: Path) -> list:
    if per_user():
        row = _run("SELECT data FROM agent_data WHERE user_id = ? AND name = ?", (_current_user(), name), fetch=True)
        return json.loads(row[0]) if row else []
    if hosted():
        raise ValueError("Saving data isn't switched on in this shared version.")
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else []


def write_json(name: str, path: Path, data: list) -> None:
    if per_user():
        _run("INSERT INTO agent_data (user_id, name, data, updated) VALUES (?, ?, ?, ?) "
             "ON CONFLICT (user_id, name) DO UPDATE SET data = excluded.data, updated = excluded.updated",
             (_current_user(), name, json.dumps(data), _now()))
        return
    if hosted():
        raise ValueError("Saving data isn't switched on in this shared version.")
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    tmp.replace(path)  # write-then-rename, so a crash can't leave a half-written file


# ---------- sign-in for the shared version ----------
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9 ._-]{1,29}$")


def _hash(passcode: str, salt: bytes) -> str:
    digest = hashlib.scrypt(passcode.encode(), salt=salt, n=2**14, r=8, p=1)
    return salt.hex() + ":" + digest.hex()


def sign_in(name: str, passcode: str) -> tuple[str, bool]:
    """Sign in, or create the account if the name is new. Returns (user_id, created)."""
    user_id = " ".join(name.strip().lower().split())
    if not NAME_RE.match(user_id):
        raise ValueError("Use 2-30 letters or numbers for your name (spaces, dots and dashes are fine).")
    if len(passcode) < 4:
        raise ValueError("Use a passcode of at least 4 characters.")
    row = _run("SELECT passcode_hash FROM agent_users WHERE user_id = ?", (user_id,), fetch=True)
    if row is None:
        _run("INSERT INTO agent_users (user_id, passcode_hash, created) VALUES (?, ?, ?)",
             (user_id, _hash(passcode, secrets.token_bytes(16)), _now()))
        return user_id, True
    salt_hex, _ = row[0].split(":", 1)
    if not hmac.compare_digest(_hash(passcode, bytes.fromhex(salt_hex)), row[0]):
        raise ValueError("That name is taken and the passcode doesn't match. If it's you, try again "
                         "(or ask for a reset).")
    return user_id, False
