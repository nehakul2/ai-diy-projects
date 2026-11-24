"""Your personal agent as a connector (MCP server) that people add inside their own Claude app.

Claude in the app does the thinking and the web searching, so this server needs no
Claude API key and costs nothing per message. It gives Claude three kinds of tools:

- Saved data: a job tracker, reading library, decision journal and content-idea bank.
  In the shared version every friend has their own, kept in a database.
- Exact maths in code: meeting costs and calendar clashes.
- Playbooks: the instructions each of your projects uses (notes into actions, gift ideas,
  travel checks...), so Claude in the app works the same way your projects do.

Run on your own Mac for Claude Desktop (uses your normal files in ~/.ai-diy-projects/):
    python -m personal_agent.mcp_server

Run as a shared server (see personal_agent/CONNECTOR.md):
    AGENT_HOSTED=1 DATABASE_URL=... INVITE_CODE=... python -m personal_agent.mcp_server --http
Each friend then adds  https://<your-server>/mcp/<INVITE_CODE>/<their-name>/<their-PIN>
"""
import argparse
import functools
import hashlib
import hmac
import json
import os
import re
import sys
from contextlib import nullcontext
from datetime import date

import anyio
from mcp.server.mcpserver import Context, MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from common import storage

INSTRUCTIONS = """A personal assistant built from 18 small AI projects.
- Saved data: job tracker (jobs_*), reading library (library_*), decision journal (decision_*), content-idea
  bank (ideas_*). Fill in the fields yourself from what the user gives you (e.g. read the job posting and pass
  company, role, skills, a checklist). Data is private to this user.
- Exact maths: meeting_costs, calendar_clashes. Use them instead of doing the sums yourself.
- run_project runs a project on the server (with its own web search) for a full report, limited to a few
  runs per person; say how many are left. Otherwise call project_playbook and follow it yourself for: notes into actions, gift ideas, inbox
  clean-up, travel checks, resume vs job matching, weekly planning, reading briefings, spending explanations,
  content ideas, decision patterns, meeting advice.
Keep replies short and friendly."""

server = MCPServer("Personal agent", instructions=INSTRUCTIONS)
USER_HEADER = "x-agent-user"


def tool(fn):
    """Register a tool. Plain problems (ValueError) are shown to Claude so it can explain them."""
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except ValueError as e:
            raise ToolError(str(e)) from e
    return server.tool()(wrapper)


def me(ctx: Context):
    """Use the friend's own data in the shared version; your normal files otherwise."""
    if not storage.per_user():
        return nullcontext()
    user = (ctx.headers or {}).get(USER_HEADER, "") if ctx else ""
    if not user:
        raise ValueError("Use your personal link to save data (ask whoever shared this with you).")
    return storage.as_user(user)


def _json(data) -> str:
    return json.dumps(data, indent=1, ensure_ascii=False)


# ---------------- Job tracker ----------------
@tool
def jobs_list(ctx: Context, show_all: bool = False) -> str:
    """Show saved job applications, most urgent first. show_all includes closed ones."""
    from job_search_tracker import store
    from job_search_tracker.tracker import table
    with me(ctx):
        return table(store.load(), show_all=show_all).replace(
            "Add one with: python -m job_search_tracker.main add --posting job.txt", "Add one with jobs_add.")


@tool
def jobs_add(ctx: Context, company: str, role: str, summary: str, checklist: list[str], next_action: str,
             location: str = "", salary: str = "", url: str = "", deadline: str = "",
             must_have_skills: list[str] | None = None, nice_to_have_skills: list[str] | None = None,
             posting: str = "") -> str:
    """Save a job to the tracker. Read the posting yourself and fill in the fields: a one-line summary,
    3-6 checklist steps to apply, the next action, deadline as YYYY-MM-DD if stated."""
    from job_search_tracker import store
    from job_search_tracker.tracker import details
    if deadline:
        store.check_date(deadline)
    job = {"company": company, "role": role, "location": location, "salary": salary, "url": url,
           "summary": summary, "deadline": deadline, "must_have_skills": must_have_skills or [],
           "nice_to_have_skills": nice_to_have_skills or [],
           "checklist": [{"step": s, "done": False} for s in checklist], "next_action": next_action,
           "next_action_date": "", "notes": "", "posting": posting[:30000]}
    with me(ctx):
        return "Saved.\n\n" + details(store.add(job))


@tool
def jobs_update(ctx: Context, job_id: int, status: str | None = None, next_action: str | None = None,
                next_action_date: str | None = None, notes: str | None = None,
                toggle_step: int | None = None) -> str:
    """Update a saved job, or call with only job_id to see its details (including the saved posting).
    status: saved, applying, applied, interviewing, offer, rejected or withdrawn. toggle_step: checklist
    step number (from 1) to tick or untick. Dates as YYYY-MM-DD."""
    from job_search_tracker import store
    from job_search_tracker.tracker import details
    with me(ctx):
        if toggle_step:
            store.toggle_step(job_id, toggle_step - 1)
        changes = {"status": status, "next_action": next_action, "next_action_date": next_action_date,
                   "notes": notes}
        if any(v is not None for v in changes.values()):
            store.update(job_id, **changes)
        job = store.get(job_id)
        posting = f"\n\n**Saved posting:**\n{job['posting'][:6000]}" if job.get("posting") else ""
        return details(job) + posting


# ---------------- Reading library ----------------
@tool
def library_save(ctx: Context, title: str, summary: str, why_it_matters: str, tags: list[str],
                 kind: str = "article", url: str = "", minutes: int = 0, note: str = "") -> str:
    """Save something to read/watch later. Read it yourself (fetch the link if you can) and fill in a
    2-3 sentence summary, why it matters to the user, 2-5 short lowercase tags (reuse existing tags from
    library_find when they fit), kind (article, video, podcast, paper, thread, tool, other) and minutes."""
    from saved_content_organiser.library import KINDS, _clean_tag, card, load, save
    if kind not in KINDS:
        kind = "other"
    with me(ctx):
        items = load()
        if url and any(i.get("url") == url for i in items):
            raise ValueError("That link is already in the library.")
        item = {"id": max((i["id"] for i in items), default=0) + 1, "title": title, "url": url, "kind": kind,
                "minutes": max(0, minutes), "tags": sorted({_clean_tag(t) for t in tags if _clean_tag(t)}),
                "summary": summary, "why_it_matters": why_it_matters, "my_note": note, "read_ok": True,
                "added": date.today().isoformat(), "done": False}
        save(items + [item])
        return "Saved.\n\n" + card(item)


@tool
def library_find(ctx: Context, query: str = "", tag: str = "", kind: str = "", include_done: bool = False) -> str:
    """Search the saved library by words, tag or kind. With no filters, lists unread items and all tags."""
    from saved_content_organiser.library import find, load, overview, tag_counts
    with me(ctx):
        items = load()
        found = find(items, tag, query, kind, include_done)
        tags = ", ".join(f"{t} ({n})" for t, n in tag_counts(items).most_common(30)) or "none yet"
        return (overview(found[:15]) if found else "Nothing matches.") + f"\n\nTags in use: {tags}"


@tool
def library_mark(ctx: Context, item_id: int, done: bool = True) -> str:
    """Mark a saved item as done (read/watched), or not done."""
    from saved_content_organiser.library import card, mark
    with me(ctx):
        return card(mark(item_id, done))


# ---------------- Decision journal ----------------
@tool
def decision_log(ctx: Context, decision: str, assumptions: list[str], watch_for: list[str], change_mind_if: str,
                 review_on: str, context: str = "", options: str = "", expected: str = "",
                 confidence: int = 70) -> str:
    """Save a decision. First get the decision_patterns playbook's sharpen step if useful; fill in 2-4
    hidden assumptions, 2-3 signals to watch, what would change their mind, and a review date (YYYY-MM-DD,
    usually 1-6 months out). confidence is 0-100."""
    from decision_journal.journal import card, load, log_decision, save
    with me(ctx):
        entry = log_decision(decision, context, options, expected, confidence, review_on, sharpen=False)
        items = load()
        for d in items:
            if d["id"] == entry["id"]:
                d.update(assumptions=assumptions, watch_for=watch_for, change_mind_if=change_mind_if)
                entry = d
        save(items)
        return "Saved.\n\n" + card(entry)


@tool
def decision_list(ctx: Context, due_only: bool = False, reviewed_only: bool = False) -> str:
    """Show decisions: the latest 10, only those due for review, or all reviewed ones (to look for patterns
    with the decision_patterns playbook)."""
    from decision_journal.journal import card, due, load
    with me(ctx):
        items = load()
    if due_only:
        items = due(items)
    elif reviewed_only:
        items = [d for d in items if d.get("review")]
    else:
        items = items[-10:]
    return "\n\n".join(card(d) for d in items) or "Nothing to show."


@tool
def decision_review(ctx: Context, decision_id: int, outcome: str, what_happened: str, assumptions_held: str = "",
                    lesson: str = "") -> str:
    """Record how a decision turned out. outcome: better, as expected, worse, or too early to tell."""
    from decision_journal.journal import card, record_review
    with me(ctx):
        return card(record_review(decision_id, outcome, what_happened, assumptions_held, lesson))


# ---------------- Content-idea bank ----------------
@tool
def ideas_save(ctx: Context, niche: str, platform: str, ideas: list[dict]) -> str:
    """Save researched content ideas (use the content_ideas playbook first). Each idea: title, angle, why_now,
    source_url, format, outline (list of points), and scores 1-5 for timeliness, audience_fit, originality."""
    from content_ideas.ideas import SCORES, card, load, save, score
    with me(ctx):
        bank = load()
        next_id = max((i["id"] for i in bank), default=0) + 1
        clean = []
        for n, raw in enumerate(ideas):
            idea = {k: raw.get(k, "") for k in ("title", "angle", "why_now", "source_url", "format")}
            idea["outline"] = list(raw.get("outline") or [])
            for k in SCORES:
                idea[k] = min(max(int(raw.get(k) or 3), 1), 5)
            idea.update(id=next_id + n, score=score(idea), platform=platform, niche=niche,
                        found=date.today().isoformat(), status="new")
            clean.append(idea)
        save(bank + clean)
        return "Saved.\n\n" + "\n\n".join(card(i) for i in clean)


@tool
def ideas_list(ctx: Context, show_all: bool = False) -> str:
    """Show the content-idea bank (open ideas, or all with show_all)."""
    from content_ideas.ideas import bank_table, load
    with me(ctx):
        return bank_table(load(), show_all)


@tool
def ideas_update(ctx: Context, idea_id: int, status: str) -> str:
    """Set an idea's status: new, drafted, posted or skipped. (To draft one, read it with ideas_list and
    use the content_ideas playbook's drafting part.)"""
    from content_ideas.ideas import card, set_status
    with me(ctx):
        return card(set_status(idea_id, status))


# ---------------- Exact maths ----------------
@tool
def meeting_costs(meetings: list[dict], hourly_rate: float, currency: str = "$") -> str:
    """Monthly cost of recurring meetings. Each meeting: title, minutes, attendees, per_month (times per
    month, e.g. weekly = 4.33). hourly_rate is the average cost per person per hour (ask if unknown)."""
    from meeting_cost_calculator.costs import _check, add_costs, report
    if hourly_rate <= 0:
        raise ValueError("The hourly rate must be more than 0.")
    rows = [_check({"title": m.get("title", "Meeting"), "minutes": m.get("minutes"),
                    "attendees": m.get("attendees"), "per_month": m.get("per_month")}) for m in meetings]
    return report(add_costs(rows, hourly_rate), hourly_rate, currency)


@tool
def calendar_clashes(calendar: str, week_start: str = "") -> str:
    """Read a calendar export (.ics text) for one week and list events and clashes, checked in code.
    week_start as YYYY-MM-DD (default next Monday)."""
    from life_admin_planner.main import calendar_snapshot, next_monday
    start = date.fromisoformat(week_start) if week_start else next_monday()
    listing, found = calendar_snapshot(calendar, start)
    return listing + ("\n\nClashes:\n" + "\n".join(f"- {c}" for c in found) if found else "\n\nNo clashes.")


# ---------------- Playbooks ----------------
def _playbooks() -> dict:
    import content_ideas.prompt as content
    import decision_journal.prompt as decisions
    import finance_explainer.prompt as finance
    import gift_idea_finder.prompt as gifts
    import inbox_cleanup.prompt as inbox
    import life_admin_planner.prompt as week
    import meeting_cost_calculator.prompt as meetings
    import notes_to_actions.prompt as notes
    import reading_list.prompt as reading
    import resume_matcher.prompt as resume
    import travel_planner.prompt as travel
    return {
        "notes_to_actions": (notes.SYSTEM, "The user's notes."),
        "gift_ideas": (gifts.SYSTEM, "Who it's for, budget, what they like. Search the web for real products."),
        "inbox_cleanup": (inbox.SYSTEM, "The emails, pasted."),
        "travel_check": (travel.SYSTEM, "Route, dates, passport. Search the web for current rules."),
        "resume_match": (resume.SYSTEM, "The resume (attached or pasted) and the job (or jobs_update for a saved one)."),
        "weekly_plan": (week.SYSTEM, "Tasks and the calendar (use calendar_clashes for an .ics file)."),
        "reading_briefing": (reading.BRIEFING_SYSTEM, "Links (fetch them) or library_find for unread items."),
        "spending_explainer": (finance.CATEGORISE_SYSTEM + "\n\n" + finance.EXPLAIN_SYSTEM,
                               "A bank export (CSV). Do the totals carefully. Not financial advice."),
        "content_ideas": (content.RESEARCH_SYSTEM + "\n\nDRAFTING:\n" + content.DRAFT_SYSTEM,
                          "Niche, audience, platform. Then offer ideas_save."),
        "decision_patterns": (decisions.SHARPEN_SYSTEM + "\n\nPATTERNS:\n" + decisions.PATTERNS_SYSTEM,
                              "Use decision_list(reviewed_only=true) for patterns."),
        "meeting_advice": (meetings.ADVICE_SYSTEM, "Get the numbers from meeting_costs first."),
    }


PLAYBOOK_NAMES = ["notes_to_actions", "gift_ideas", "inbox_cleanup", "travel_check", "resume_match", "weekly_plan",
                  "reading_briefing", "spending_explainer", "content_ideas", "decision_patterns", "meeting_advice"]


def project_playbook(project: str) -> str:
    books = _playbooks()
    if project not in books:
        raise ValueError(f"Pick one of: {', '.join(books)}")
    system, needs = books[project]
    return (f"Follow these instructions for the user's request (placeholders like {{today}} or {{count}}: use "
            f"sensible values; ignore anything about a fixed JSON format and just answer clearly).\n\n"
            f"What you need from the user: {needs}\n\n---\n{system}")


project_playbook.__doc__ = (f"Get the instructions one of the projects uses, then follow them yourself with the "
                            f"user's input. project: one of {', '.join(PLAYBOOK_NAMES)}.")
tool(project_playbook)


# ---------------- Run a project with your API key (optional, capped per friend) ----------------
RUNNABLE = {  # project -> tool in personal_agent/tools.py (the same code the chat page uses)
    "notes_to_actions": "notes_to_actions", "gift_ideas": "find_gifts", "inbox_cleanup": "sort_emails",
    "travel_check": "check_trip", "resume_match": "match_resume", "weekly_plan": "plan_week",
    "reading_briefing": "reading_briefing", "spending_explainer": "explain_finances",
    "meeting_advice": "meeting_costs", "content_ideas": "content_ideas",
}


def run_limit() -> int:
    return int(os.environ.get("FRIEND_RUN_LIMIT", "10"))


def _inputs_help() -> str:
    from personal_agent.tools import TOOLS
    by_name = {t["name"]: t for t in TOOLS}
    lines = []
    for project, name in RUNNABLE.items():
        props = by_name[name]["input_schema"]["properties"]
        need = by_name[name]["input_schema"].get("required", [])
        fields = ", ".join(f"{k}{'*' if k in need else ''}" for k in props if not k.endswith("path"))
        lines.append(f"- {project}: {fields}")
    return "\n".join(lines)


def run_project(ctx: Context, project: str, inputs: dict) -> str:
    from personal_agent.tools import HANDLERS
    if not os.environ.get("ANTHROPIC_API_KEY", "").strip():
        raise ValueError("Running projects on the server is switched off. Use project_playbook instead.")
    if project not in RUNNABLE:
        raise ValueError(f"Pick one of: {', '.join(RUNNABLE)}")
    inputs = {k: v for k, v in (inputs or {}).items() if not k.endswith("path")}  # no server files
    with me(ctx):
        usage = storage.read_json("usage", _local_usage_file()) or [{"runs": 0}]
        if usage[0]["runs"] >= run_limit():
            raise ValueError(f"You've used all {run_limit()} project runs in this demo. You can still use "
                             "project_playbook and the trackers as much as you like.")
        usage[0]["runs"] += 1
        storage.write_json("usage", _local_usage_file(), usage)
        try:
            result = HANDLERS[RUNNABLE[project]](None, **inputs)
        except (SystemExit, TypeError, ValueError) as e:
            usage[0]["runs"] -= 1  # a failed run doesn't count
            storage.write_json("usage", _local_usage_file(), usage)
            message = e.code if isinstance(e, SystemExit) else str(e)
            raise ValueError(f"The project couldn't run: {message}") from e
    left = run_limit() - usage[0]["runs"]
    return result + f"\n\n_({left} of {run_limit()} project runs left for this person.)_"


def _local_usage_file():
    from pathlib import Path
    return Path.home() / ".ai-diy-projects" / "connector-usage.json"


run_project.__doc__ = (
    "Run one of the projects on the server with its own prompts and web search, and return its full report. "
    f"Each person can do this {run_limit()} times; use project_playbook (unlimited) when you can do the job "
    "yourself just as well. Put the project's inputs in `inputs` (* = required):\n" + _inputs_help())
tool(run_project)


# ---------------- Friend links (shared version) ----------------
LINK_RE = re.compile(r"^/mcp/([^/]+)/([a-z0-9][a-z0-9-]{1,29})/([^/]+)/?$")
_verified: dict[tuple[str, str], str] = {}


def _check_friend(name: str, pin: str) -> str:
    key = (name, hashlib.sha256(pin.encode()).hexdigest())
    if key not in _verified:
        user, _ = storage.sign_in(name, pin)  # creates the account the first time a name is used
        _verified[key] = user
    return _verified[key]


class FriendLinks:
    """Turns /mcp/<invite>/<name>/<pin> into the MCP endpoint, telling the tools who is calling."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        path = scope["path"]
        if path in ("/", "/health"):
            return await _text(send, 200, "Personal agent connector is running. Add your personal link in Claude.")
        m = LINK_RE.match(path)
        if not m:
            return await _text(send, 404, "Use your personal link: /mcp/<invite code>/<your-name>/<your-PIN>")
        invite, name, pin = m.groups()
        if not hmac.compare_digest(invite.encode(), os.environ.get("INVITE_CODE", "").encode()):
            return await _text(send, 403, "That invite code isn't right.")
        try:
            user = await anyio.to_thread.run_sync(_check_friend, name, pin)
        except ValueError as e:
            return await _text(send, 403, str(e))
        headers = [(k, v) for k, v in scope["headers"] if k.lower() != USER_HEADER.encode()]
        headers.append((USER_HEADER.encode(), user.encode()))
        await self.app(dict(scope, path="/mcp", raw_path=b"/mcp", headers=headers), receive, send)


async def _text(send, status: int, body: str) -> None:
    await send({"type": "http.response.start", "status": status,
                "headers": [(b"content-type", b"text/plain; charset=utf-8")]})
    await send({"type": "http.response.body", "body": body.encode()})


def http_app():
    if not os.environ.get("INVITE_CODE", "").strip():
        sys.exit("Set INVITE_CODE (a secret word friends need in their link).")
    if not storage.per_user():
        sys.exit("Set AGENT_HOSTED=1 and DATABASE_URL so each friend gets their own data.")
    from mcp.server.transport_security import TransportSecuritySettings
    app = server.streamable_http_app(
        stateless_http=True, json_response=True,
        # The server sits behind the host's HTTPS proxy under its own domain, so don't pin the Host header.
        transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False))
    return FriendLinks(app)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--http", action="store_true", help="Run as a shared web server (see CONNECTOR.md).")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8000")))
    args = parser.parse_args()
    if not args.http:
        server.run("stdio")  # Claude Desktop starts this itself
        return
    import uvicorn
    uvicorn.run(http_app(), host="0.0.0.0", port=args.port, proxy_headers=True, forwarded_allow_ips="*")


if __name__ == "__main__":
    main()
