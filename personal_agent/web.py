"""The personal helper as a standalone web app: a JSON API plus a phone-friendly page.

The page (personal_agent/static/) is just one client of the API below, so a phone app can
use the same API later.

Run on your Mac (everything works, using your own files):
    python -m personal_agent.web                      # then open http://localhost:8000

Run as the shared app for friends (see personal_agent/DEPLOY.md):
    AGENT_HOSTED=1 DATABASE_URL=... INVITE_CODE=... ANTHROPIC_API_KEY=... python -m personal_agent.web

API (JSON; send the token from /api/login as "Authorization: Bearer <token>"):
    POST /api/login   {"invite", "name", "pin"}  -> {"token", "name", "left", "limit"}
    GET  /api/me                                  -> {"name", "left", "limit", "examples", "features"}
    POST /api/chat    {"message"} or a form with "message" and an optional "file"
                                                  -> {"reply", "results": [{"label", "output", "ok"}], "left"}
    POST /api/new                                 -> starts a fresh conversation
    POST /api/confirm {"yes": true|false}         -> on your own computer only: answer a file-move question
"""
import hashlib
import hmac
import os
import re
import sys
import threading
import uuid
from pathlib import Path

import anyio
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import FileResponse, JSONResponse
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

from common import storage
from personal_agent.agent import Agent
from personal_agent.tools import HOSTED, UPLOADS, available_tools

STATIC = Path(__file__).parent / "static"
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_MESSAGE_CHARS = 20000
LOCAL_USER = "me"


def question_limit() -> int:
    return int(os.environ.get("FRIEND_QUESTION_LIMIT", "10"))


def unlimited(user: str) -> bool:
    names = {n.strip().lower() for n in os.environ.get("UNLIMITED_USERS", "").split(",") if n.strip()}
    return not HOSTED or user in names


# ---------- tokens: "<user>.<signature>", signed with a server secret ----------
def _secret() -> bytes:
    explicit = os.environ.get("APP_SECRET", "")
    if explicit:
        return explicit.encode()
    # Stable across restarts without another setting: derived from the private settings.
    basis = os.environ.get("DATABASE_URL", "") + os.environ.get("INVITE_CODE", "") + os.environ.get("ANTHROPIC_API_KEY", "")
    return hashlib.sha256(("personal-agent:" + basis).encode()).digest()


def make_token(user: str) -> str:
    sig = hmac.new(_secret(), user.encode(), hashlib.sha256).hexdigest()[:32]
    return f"{user}.{sig}"


def user_from(request: Request) -> str | None:
    if not HOSTED:
        return LOCAL_USER
    auth = request.headers.get("authorization", "")
    token = auth.removeprefix("Bearer ").strip()
    user, _, sig = token.rpartition(".")
    if user and hmac.compare_digest(make_token(user), token):
        return user
    return None


# ---------- per-person state ----------
_agents: dict[str, Agent] = {}
_busy: dict[str, threading.Lock] = {}


def agent_for(user: str) -> Agent:
    if user not in _agents:
        _agents[user] = Agent(name="" if HOSTED else os.environ.get("AGENT_NAME", ""))
        _busy[user] = threading.Lock()
    return _agents[user]


def _usage_file() -> Path:
    return Path.home() / ".ai-diy-projects" / "web-usage.json"


def used(user: str) -> int:
    if unlimited(user) or not storage.per_user():
        return _memory_usage.get(user, 0)
    with storage.as_user(user):
        rows = storage.read_json("usage", _usage_file())
    return rows[0].get("questions", 0) if rows else 0


_memory_usage: dict[str, int] = {}  # used when there's no database (counts reset on restart)


def add_use(user: str, n: int) -> None:
    if unlimited(user):
        return
    if not storage.per_user():
        _memory_usage[user] = _memory_usage.get(user, 0) + n
        return
    with storage.as_user(user):
        rows = storage.read_json("usage", _usage_file()) or [{}]
        rows[0]["questions"] = rows[0].get("questions", 0) + n
        storage.write_json("usage", _usage_file(), rows)


def left(user: str) -> int | None:
    return None if unlimited(user) else max(0, question_limit() - used(user))


def error(message: str, status: int = 400) -> JSONResponse:
    return JSONResponse({"error": message}, status_code=status)


# ---------- routes ----------
async def login(request: Request) -> JSONResponse:
    if not HOSTED:
        return JSONResponse({"token": "local", "name": LOCAL_USER, "left": None, "limit": None})
    body = await request.json()
    invite = str(body.get("invite", "")).strip()
    if not hmac.compare_digest(invite.encode(), os.environ.get("INVITE_CODE", "").encode()):
        return error("That invite code isn't right. Check the link you were sent.", 403)
    try:
        user, created = await anyio.to_thread.run_sync(storage.sign_in, str(body.get("name", "")),
                                                       str(body.get("pin", "")))
    except ValueError as e:
        return error(str(e), 403)
    return JSONResponse({"token": make_token(user), "name": user, "created": created,
                         "left": left(user), "limit": None if unlimited(user) else question_limit()})


EXAMPLES = [
    "Gift ideas for my dad, around $60, he loves gardening and jazz",
    "Check my trip: London to Tokyo via Doha, 3-17 March, Indian passport",
    "Turn these notes into a to-do list: call bank about card, Sam wants slides by Fri, book dentist",
    "What can you do?",
]


async def me(request: Request) -> JSONResponse:
    user = user_from(request)
    if not user:
        return error("Please sign in.", 401)
    names = {t["name"] for t in available_tools()}
    return JSONResponse({"name": user, "left": left(user), "limit": None if unlimited(user) else question_limit(),
                         "examples": EXAMPLES, "hosted": HOSTED,
                         "features": {"saves_data": "list_jobs" in names, "tidy_folders": "confirm_tidy" in names},
                         "owner": os.environ.get("AGENT_NAME", "")})


def _save_upload(user: str, filename: str, data: bytes) -> str:
    # A random folder per upload, so nobody can guess another person's file path.
    folder = UPLOADS / uuid.uuid4().hex
    folder.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^\w.\- ]", "_", Path(filename or "file").name)[:100] or "file"
    path = folder / safe
    path.write_bytes(data)
    return str(path)


def _run_chat(user: str, text: str) -> dict:
    agent = agent_for(user)
    lock = _busy[user]
    if not lock.acquire(blocking=False):
        raise ValueError("I'm still working on your last message. Give me a moment.")
    try:
        ctx = storage.as_user(user) if storage.per_user() else _nothing()
        with ctx:
            return agent.send(text)
    finally:
        lock.release()


class _nothing:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


async def chat(request: Request) -> JSONResponse:
    user = user_from(request)
    if not user:
        return error("Please sign in.", 401)
    if (remaining := left(user)) is not None and remaining <= 0:
        return error(f"You've used all {question_limit()} questions in this demo. Thanks for trying it!", 429)
    if request.headers.get("content-type", "").startswith("multipart/form-data"):
        form = await request.form(max_part_size=MAX_UPLOAD_BYTES)
        text = str(form.get("message", ""))
        upload = form.get("file")
        if upload is not None and getattr(upload, "filename", ""):
            data = await upload.read()
            if len(data) > MAX_UPLOAD_BYTES:
                return error("That file is too big (10 MB max).")
            path = await anyio.to_thread.run_sync(_save_upload, user, upload.filename, data)
            text += f"\n\n[Attached file: {path}]"
    else:
        text = str((await request.json()).get("message", ""))
    text = text.strip()[:MAX_MESSAGE_CHARS]
    if not text:
        return error("Type a message first.")
    add_use(user, 1)  # counted up front so several tabs can't go over the limit
    try:
        result = await anyio.to_thread.run_sync(_run_chat, user, text)
    except SystemExit as e:  # API problems come back as a plain message
        add_use(user, -1)
        return error(str(e.code or "Something went wrong."), 502)
    except ValueError as e:
        add_use(user, -1)
        return error(str(e), 409)
    agent = agent_for(user)
    return JSONResponse({
        "reply": result["reply"],
        "results": [{"label": label, "output": output, "ok": ok} for label, output, ok in result["results"]],
        "left": left(user),
        "pending": agent.pending["question"] if agent.pending else None,
    })


async def new_chat(request: Request) -> JSONResponse:
    user = user_from(request)
    if not user:
        return error("Please sign in.", 401)
    _agents.pop(user, None)
    return JSONResponse({"ok": True})


async def confirm(request: Request) -> JSONResponse:
    user = user_from(request)
    if not user:
        return error("Please sign in.", 401)
    agent = agent_for(user)
    if not agent.pending:
        return error("Nothing is waiting for confirmation.")
    yes = bool((await request.json()).get("yes"))
    outcome = await anyio.to_thread.run_sync(agent.answer_confirmation, yes)
    return JSONResponse({"outcome": outcome})


async def index(request: Request) -> FileResponse:
    return FileResponse(STATIC / "index.html", headers={"Cache-Control": "no-cache"})


async def service_worker(request: Request) -> FileResponse:
    return FileResponse(STATIC / "sw.js", media_type="application/javascript", headers={"Cache-Control": "no-cache"})


async def health(request: Request) -> JSONResponse:
    return JSONResponse({"ok": True})


def create_app() -> Starlette:
    if HOSTED:
        missing = [k for k in ("INVITE_CODE", "ANTHROPIC_API_KEY") if not os.environ.get(k, "").strip()]
        if missing:
            sys.exit(f"Set {' and '.join(missing)} for the shared app (see personal_agent/DEPLOY.md).")
        if not storage.database_url():
            print("No DATABASE_URL: friends can chat, but saving (trackers, library...) is off and "
                  "question counts reset when the server restarts.", file=sys.stderr)
    return Starlette(routes=[
        Route("/", index),
        Route("/sw.js", service_worker),
        Route("/health", health),
        Route("/api/login", login, methods=["POST"]),
        Route("/api/me", me),
        Route("/api/chat", chat, methods=["POST"]),
        Route("/api/new", new_chat, methods=["POST"]),
        Route("/api/confirm", confirm, methods=["POST"]),
        Mount("/static", StaticFiles(directory=STATIC), name="static"),
    ])


def main() -> None:
    import uvicorn
    port = int(os.environ.get("PORT", "8000"))
    host = "0.0.0.0" if HOSTED else "127.0.0.1"  # on your Mac, only your own computer can open it
    if not HOSTED:
        print(f"Open http://localhost:{port} in your browser. Ctrl-C to stop.", file=sys.stderr)
    uvicorn.run(create_app(), host=host, port=port, proxy_headers=True, forwarded_allow_ips="*")


if __name__ == "__main__":
    main()
