"""The tools the personal agent can use. Each one is a thin wrapper around an existing project.

Every tool is registered with @tool(...) and gets the agent (for saved plans and pending
confirmations) plus the inputs Claude chose. A tool returns Markdown text, which is
shown to you in full and also sent back to Claude.

Nothing here moves files. The two tidy-up tools only make a plan; moving files (or
undoing a move) is requested with confirm_* tools and only happens after you say yes.
"""
import os
import tempfile
from pathlib import Path

from content_ideas.prompt import PLATFORMS

TOOLS: list[dict] = []      # tool definitions sent to Claude
HANDLERS: dict = {}         # tool name -> function
LABELS: dict = {}           # tool name -> friendly name shown while it runs

MAX_FILE_CHARS = 60000

# Shared (hosted) mode: set AGENT_HOSTED=1 on a server that friends use. Tools that touch the
# server's own folders or your personal data files are left out, and file paths are only
# allowed inside the uploads folder (each visitor gets their own, unguessable subfolder).
HOSTED = os.environ.get("AGENT_HOSTED", "").strip().lower() in ("1", "true", "yes")
UPLOADS = Path(tempfile.gettempdir()) / "ai-diy-agent-uploads"
LOCAL_ONLY = {
    "plan_downloads_tidy", "plan_photo_tidy", "confirm_tidy", "confirm_undo_tidy",  # move files
    "list_jobs", "add_job", "update_job",                                              # your job tracker
    "save_to_library", "find_in_library", "mark_library_item",                         # your library
    "log_decision", "list_decisions", "review_decision", "decision_patterns",          # your journal
    "build_dashboard", "list_content_ideas", "draft_post",                             # your dashboard / bank
}


def available_tools() -> list[dict]:
    return [t for t in TOOLS if not (HOSTED and t["name"] in LOCAL_ONLY)]


def tool(name: str, label: str, description: str, properties: dict | None = None, required: list | None = None):
    def register(fn):
        TOOLS.append({"name": name, "description": description,
                      "input_schema": {"type": "object", "properties": properties or {},
                                       "required": required or []}})
        HANDLERS[name] = fn
        LABELS[name] = label
        return fn
    return register


def s(description: str) -> dict:
    return {"type": "string", "description": description}


def _path(p: str) -> Path:
    path = Path(p.strip().strip("'\"")).expanduser()
    if HOSTED and not path.resolve().is_relative_to(UPLOADS.resolve()):
        raise ValueError("In the shared version I can only open files you attach with the 📎 button.")
    if not path.exists():
        raise ValueError(f"I can't find {path}. Check the path (tip: drag the file into Terminal to copy its path).")
    return path


def _text(text: str = "", path: str = "") -> str:
    """Pasted text, or the contents of a file on this computer."""
    if path:
        p = _path(path)
        if p.is_dir():
            raise ValueError(f"{p} is a folder; I need a file.")
        return p.read_text(encoding="utf-8", errors="replace")[:MAX_FILE_CHARS]
    return text or ""


PATH_HINT = "Full path to a file on this computer, e.g. ~/Downloads/file.txt. Use instead of pasting text."


# ---------- 1. Notes into actions ----------
@tool("notes_to_actions", "Notes into actions",
      "Turn messy notes (meeting notes, voice-memo transcript, brain dump) into a summary, task list and a "
      "follow-up message.",
      {"notes": s("The notes, as pasted."), "path": s(PATH_HINT)})
def _notes_to_actions(agent, notes: str = "", path: str = "") -> str:
    from notes_to_actions.main import notes_to_actions
    text = _text(notes, path)
    if not text.strip():
        raise ValueError("Paste the notes or give a file path.")
    return notes_to_actions(text)


# ---------- 2. Gift idea finder ----------
@tool("find_gifts", "Gift idea finder",
      "Search the web for five gift ideas with links. Needs who it's for, a budget and what they like.",
      {"who": s("Who the gift is for, e.g. 'my sister, 30'."), "budget": s("e.g. '$50' or 'under £30'."),
       "likes": s("Their interests and hobbies."), "occasion": s("Optional, e.g. birthday."),
       "country": s("Optional, where to buy/ship.")},
      ["who", "budget", "likes"])
def _find_gifts(agent, who: str, budget: str, likes: str, occasion: str = "", country: str = "") -> str:
    from gift_idea_finder.main import find_gifts
    return find_gifts(who, budget, likes, occasion, country)


# ---------- 3. Inbox clean-up ----------
@tool("sort_emails", "Inbox clean-up",
      "Suggest an action (reply, archive, unsubscribe, etc.) for each email. Give pasted emails separated by a "
      "line with only ---, or a path to a text file, an .eml file, or a folder of .eml files.",
      {"emails": s("Pasted emails separated by lines containing only ---."),
       "path": s("A text file, an .eml file, or a folder of .eml files.")})
def _sort_emails(agent, emails: str = "", path: str = "") -> str:
    from inbox_cleanup.emails import from_text, load
    from inbox_cleanup.main import MAX_EMAILS, sort_emails
    items = load(str(_path(path))) if path else from_text(emails)
    if not items:
        raise ValueError("No emails found. Paste some (separated by ---) or give a file or folder.")
    return sort_emails(items[:MAX_EMAILS])


# ---------- 4. Travel planner ----------
@tool("check_trip", "Travel planner",
      "Check a trip for visa, passport, luggage and transfer problems (searches the web). Needs the route and "
      "dates, or bookings.",
      {"trip": s("Route and dates, e.g. 'London to Tokyo via Doha, 3-17 March'."),
       "passport": s("Passport nationality."), "airline": s("Airline and fare type, if known."),
       "notes": s("Anything else (kids, pets, tight connections...)."),
       "bookings": s("Pasted booking confirmations."), "bookings_path": s(PATH_HINT)})
def _check_trip(agent, trip: str = "", passport: str = "", airline: str = "", notes: str = "",
                bookings: str = "", bookings_path: str = "") -> str:
    from travel_planner.main import plan_trip
    return plan_trip(trip, passport, airline, notes, _text(bookings, bookings_path))


# ---------- 5 & 14. Tidy-ups (plan only) ----------
def _remember_plan(agent, kind: str, plan: dict) -> str:
    plan_id = f"{kind}-{len(agent.plans) + 1}"
    agent.plans[plan_id] = plan
    return plan_id


@tool("plan_downloads_tidy", "Downloads organiser (preview)",
      "Look at the newest files in a folder (default ~/Downloads) and propose folders and clearer names. "
      "This only makes a plan; nothing moves. Returns a plan_id for confirm_tidy.",
      {"folder": s("Folder to tidy. Default ~/Downloads."),
       "limit": {"type": "integer", "description": "How many of the newest files to look at (default 20, max 100)."}})
def _plan_downloads(agent, folder: str = "~/Downloads", limit: int = 20) -> str:
    from downloads_organiser.organiser import make_plan, plan_to_markdown
    plan = make_plan(folder or "~/Downloads", max(1, min(int(limit), 100)))
    plan_id = _remember_plan(agent, "downloads", plan)
    return plan_to_markdown(plan) + f"\n\n_plan_id: `{plan_id}`_"


@tool("plan_photo_tidy", "Photo organiser (preview)",
      "Group the photos in a folder into events by date and place, and propose one folder per event. "
      "This only makes a plan; nothing moves. Returns a plan_id for confirm_tidy.",
      {"folder": s("Folder of photos."),
       "gap_hours": {"type": "number", "description": "Hours between photos that start a new event (default 6)."},
       "thumbnails": {"type": "boolean", "description": "Send 3 small thumbnails per event so names are better "
                      "(default true). Set false if the user doesn't want photos sent."}},
      ["folder"])
def _plan_photos(agent, folder: str, gap_hours: float = 6, thumbnails: bool = True) -> str:
    from photo_organiser.organiser import make_plan, plan_to_markdown
    plan = make_plan(str(_path(folder)), gap_hours=float(gap_hours), thumbnails=bool(thumbnails))
    if not plan["moves"]:
        return plan_to_markdown(plan) + "\n\nNothing to move."
    plan_id = _remember_plan(agent, "photos", plan)
    return plan_to_markdown(plan) + f"\n\n_{len(plan['moves'])} files would move. plan_id: `{plan_id}`_"


@tool("confirm_tidy", "Ask to move files",
      "Ask the user to confirm moving files for a plan from plan_downloads_tidy or plan_photo_tidy. Only call "
      "this when the user has seen the plan and said to go ahead. The files move only if they then press "
      "Confirm (or type yes).",
      {"plan_id": s("The plan_id from the preview.")}, ["plan_id"])
def _confirm_tidy(agent, plan_id: str) -> str:
    plan = agent.plans.get(plan_id)
    if not plan:
        raise ValueError(f"No plan called {plan_id}. Make a new preview first.")
    n = len(plan["moves"])
    agent.request_confirmation(
        f"Move {n} file{'s' if n != 1 else ''} in {plan['folder']}? Nothing is deleted or overwritten, "
        "and an undo log is saved.", "apply", plan_id=plan_id)
    return "Asked the user to confirm. Nothing has moved yet; wait for their answer."


@tool("confirm_undo_tidy", "Ask to undo a tidy-up",
      "Ask the user to confirm undoing a previous tidy-up, using its undo log (a .organiser-undo-*.json file "
      "in the tidied folder). Files move back only if they then press Confirm.",
      {"log_path": s("Path to the undo log.")}, ["log_path"])
def _confirm_undo(agent, log_path: str) -> str:
    log = _path(log_path)
    agent.request_confirmation(f"Put files back using {log.name}?", "undo", log_path=str(log))
    return "Asked the user to confirm the undo. Nothing has moved yet."


def run_confirmed(action: dict) -> str:
    """Called by the chat page or CLI after the user said yes. Returns what happened."""
    from downloads_organiser.organiser import apply_plan, undo
    if action["kind"] == "apply":
        _, messages = apply_plan(action["plan"])
    else:
        messages = undo(action["log_path"])
    return "\n".join(f"- {m}" for m in messages)


# ---------- 6. Resume matcher ----------
@tool("match_resume", "Resume matcher",
      "Compare a resume (PDF or text file path, or pasted text) with a job description: fit, gaps, and edits.",
      {"resume_path": s("Path to the resume (.pdf, .txt, .md)."), "resume_text": s("Pasted resume text."),
       "job": s("The job description, pasted."), "job_path": s("Path to a file with the job description."),
       "job_id": {"type": "integer", "description": "Use the posting saved in the job tracker with this id."}})
def _match_resume(agent, resume_path: str = "", resume_text: str = "", job: str = "", job_path: str = "",
                  job_id: int | None = None) -> str:
    from resume_matcher.main import match_resume, resume_block
    if resume_path:
        p = _path(resume_path)
        block = resume_block(p.read_bytes(), p.name)
    elif resume_text.strip():
        block = resume_block(resume_text.encode(), "resume.txt")
    else:
        raise ValueError("I need the resume: a file path or pasted text.")
    if job_id:
        from job_search_tracker import store
        job = store.get(int(job_id)).get("posting", "")
    job = _text(job, job_path)
    if not job.strip():
        raise ValueError("I need the job description (pasted, a file, or a saved job id).")
    return match_resume(block, job)


# ---------- 7. Life-admin planner ----------
@tool("plan_week", "Life-admin planner",
      "Plan the coming week around the user's calendar: fit tasks into free time and flag clashes.",
      {"tasks": s("Tasks to fit in, one per line."), "calendar": s("The week's events as text."),
       "calendar_path": s("Path to a calendar export (.ics) or a text file."),
       "week_start": s("First day, YYYY-MM-DD. Default next Monday."), "notes": s("Preferences, e.g. 'gym Tue/Thu'.")},
      ["tasks"])
def _plan_week(agent, tasks: str, calendar: str = "", calendar_path: str = "", week_start: str = "",
               notes: str = "") -> str:
    from datetime import date

    from life_admin_planner.main import plan_week
    start = date.fromisoformat(week_start) if week_start else None
    return plan_week(_text(calendar, calendar_path), tasks, start, notes)


# ---------- 8. Job-search tracker ----------
@tool("list_jobs", "Job tracker",
      "Show saved job applications, most urgent first.",
      {"show_all": {"type": "boolean", "description": "Include rejected/withdrawn/offer roles."}})
def _list_jobs(agent, show_all: bool = False) -> str:
    from job_search_tracker import store
    from job_search_tracker.tracker import table
    return table(store.load(), show_all=bool(show_all))


@tool("add_job", "Job tracker (add)",
      "Read a job posting and save it to the tracker with a checklist and deadline.",
      {"posting": s("The job posting text."), "posting_path": s(PATH_HINT), "url": s("Link to the posting."),
       "deadline": s("YYYY-MM-DD, if known.")})
def _add_job(agent, posting: str = "", posting_path: str = "", url: str = "", deadline: str = "") -> str:
    from job_search_tracker.tracker import add_role, details
    return "Saved.\n\n" + details(add_role(_text(posting, posting_path), url, deadline))


@tool("update_job", "Job tracker (update)",
      "Update a saved job: status, next action, its date, notes, or tick a checklist step. Or just show its details.",
      {"job_id": {"type": "integer"},
       "status": {"type": "string", "enum": ["saved", "applying", "applied", "interviewing", "offer", "rejected",
                                             "withdrawn"]},
       "next_action": s("What to do next."), "next_action_date": s("YYYY-MM-DD."), "notes": s("Replaces the notes."),
       "toggle_step": {"type": "integer", "description": "Checklist step number to tick/untick, starting at 1."}},
      ["job_id"])
def _update_job(agent, job_id: int, status: str | None = None, next_action: str | None = None,
                next_action_date: str | None = None, notes: str | None = None, toggle_step: int | None = None) -> str:
    from job_search_tracker import store
    from job_search_tracker.tracker import details
    job_id = int(job_id)
    if toggle_step:
        store.toggle_step(job_id, int(toggle_step) - 1)
    changes = {"status": status, "next_action": next_action, "next_action_date": next_action_date, "notes": notes}
    if any(v is not None for v in changes.values()):
        store.update(job_id, **changes)
    return details(store.get(job_id))


# ---------- 9. Saved-content organiser ----------
@tool("save_to_library", "Saved-content organiser",
      "Save a link (or pasted text) to the reading library, tagged and summarised.",
      {"url": s("Link to save."), "note": s("Why it was saved."), "text": s("Pasted text, if no link.")})
def _save_item(agent, url: str = "", note: str = "", text: str = "") -> str:
    from saved_content_organiser.library import add_item, card
    return "Saved.\n\n" + card(add_item(url, note, text))


@tool("find_in_library", "Saved-content organiser (search)",
      "Search the saved library by words, tag or kind (no AI call).",
      {"query": s("Words to look for."), "tag": s("A tag."),
       "kind": {"type": "string", "enum": ["article", "video", "podcast", "paper", "thread", "tool", "other"]},
       "include_done": {"type": "boolean"}})
def _find_items(agent, query: str = "", tag: str = "", kind: str = "", include_done: bool = False) -> str:
    from saved_content_organiser.library import find, load, overview
    found = find(load(), tag, query, kind, bool(include_done))
    return overview(found[:15]) if found else "Nothing in the library matches."


@tool("mark_library_item", "Saved-content organiser (mark done)",
      "Mark a saved item as done (read/watched) or not done.",
      {"item_id": {"type": "integer"}, "done": {"type": "boolean"}}, ["item_id"])
def _mark_item(agent, item_id: int, done: bool = True) -> str:
    from saved_content_organiser.library import card, mark
    return card(mark(int(item_id), bool(done)))


# ---------- 10. Decision journal ----------
@tool("log_decision", "Decision journal",
      "Save a decision to the journal. Claude adds hidden assumptions and a review date.",
      {"decision": s("What was decided."), "context": s("Situation."), "options": s("Options considered."),
       "expected": s("What they expect to happen."),
       "confidence": {"type": "integer", "description": "0-100, default 70."},
       "review_on": s("YYYY-MM-DD, optional.")},
      ["decision"])
def _log_decision(agent, decision: str, context: str = "", options: str = "", expected: str = "",
                  confidence: int = 70, review_on: str = "") -> str:
    from decision_journal.journal import card, log_decision
    return "Saved.\n\n" + card(log_decision(decision, context, options, expected, int(confidence), review_on))


@tool("list_decisions", "Decision journal (list)",
      "Show decisions in the journal, or only those due for review.",
      {"due_only": {"type": "boolean"}})
def _list_decisions(agent, due_only: bool = False) -> str:
    from decision_journal.journal import card, due, load
    items = load()
    items = due(items) if due_only else items[-10:]
    if not items:
        return "No decisions due for review." if due_only else "The journal is empty."
    return "\n\n".join(card(d) for d in items)


@tool("review_decision", "Decision journal (review)",
      "Record how a past decision turned out.",
      {"decision_id": {"type": "integer"},
       "outcome": {"type": "string", "enum": ["better", "as expected", "worse", "too early to tell"]},
       "what_happened": s("Briefly, what happened."), "assumptions_held": s("Which assumptions held."),
       "lesson": s("Any lesson.")},
      ["decision_id", "outcome", "what_happened"])
def _review_decision(agent, decision_id: int, outcome: str, what_happened: str, assumptions_held: str = "",
                     lesson: str = "") -> str:
    from decision_journal.journal import card, record_review
    return card(record_review(int(decision_id), outcome, what_happened, assumptions_held, lesson))


@tool("decision_patterns", "Decision journal (patterns)",
      "Look across reviewed decisions for patterns in how the user decides (needs 3+ reviewed).")
def _patterns(agent) -> str:
    from decision_journal.journal import find_patterns, load
    return find_patterns(load())


# ---------- 11. Meeting cost calculator ----------
@tool("meeting_costs", "Meeting cost calculator",
      "Work out what recurring meetings cost per month and suggest cuts. Meetings as text, .ics or CSV.",
      {"meetings": s("Description of the meetings."), "path": s(PATH_HINT),
       "rate": {"type": "number", "description": "Average hourly cost per person. Ask if unknown."},
       "currency": s("Symbol, default $."), "context": s("Team context.")},
      ["rate"])
def _meetings(agent, rate: float, meetings: str = "", path: str = "", currency: str = "$", context: str = "") -> str:
    from meeting_cost_calculator.main import calculate
    text = _text(meetings, path)
    if not text.strip():
        raise ValueError("Describe the meetings or give a file.")
    return calculate(text, float(rate), currency or "$", context)


# ---------- 12. Reading list ----------
@tool("reading_briefing", "Reading list briefing",
      "Read a list of links (or the unread articles in the library) and write a short spoken-style briefing "
      "with a read/skim/skip verdict for each.",
      {"links": s("Links, one per line, and/or pasted article text."),
       "from_library": {"type": "boolean", "description": "Use unread articles from the saved library."},
       "minutes": {"type": "integer", "description": "Briefing length, 1-15 (default 3)."}})
def _briefing(agent, links: str = "", from_library: bool = False, minutes: int = 3) -> str:
    from reading_list.briefing import from_library as library_links
    from reading_list.briefing import make_briefing, to_markdown
    text = library_links() if from_library and not links.strip() else links
    b = make_briefing(text, int(minutes))
    return to_markdown(b) + "\n\n### Script to listen to\n\n" + b["script"]


# ---------- 13. Finance explainer ----------
@tool("explain_finances", "Finance explainer",
      "Explain spending from a bank export (CSV) in plain English. Not financial advice.",
      {"path": s("Path to the bank export CSV."), "text": s("Pasted CSV."), "currency": s("Symbol, default $."),
       "day_first": {"type": "boolean", "description": "Dates are DD/MM (UK/EU/India)."},
       "context": s("Household context.")})
def _finance(agent, path: str = "", text: str = "", currency: str = "$", day_first: bool = False,
             context: str = "") -> str:
    from finance_explainer.main import explain_export
    data = _text(text, path)
    if not data.strip():
        raise ValueError("Give the bank export: a file path or pasted CSV.")
    return explain_export(data, currency or "$", bool(day_first), context)


# ---------- 15. Personal dashboard ----------
@tool("build_dashboard", "Personal dashboard",
      "Build the personal dashboard (weather, news, calendar, jobs, decisions due) and save dashboard.html.",
      {"local_only": {"type": "boolean", "description": "Skip weather/news (no web search)."}})
def _dashboard(agent, local_only: bool = False) -> str:
    from personal_dashboard.cards import load_config
    from personal_dashboard.dashboard import build, save, to_markdown
    data = build(load_config(None), use_web=not local_only)
    path = save(data)
    return to_markdown(data) + f"\n\n_Saved {path} (open it in your browser)._"


# ---------- 16. Content ideas ----------
@tool("content_ideas", "Content-idea assistant",
      "Research timely content ideas for a niche (web search) and save them to the idea bank, scored.",
      {"niche": s("What they create content about."), "audience": s("Who it's for."),
       "platform": {"type": "string", "enum": PLATFORMS},
       "count": {"type": "integer", "description": "How many ideas, 1-10 (default 5)."}},
      ["niche"])
def _ideas(agent, niche: str, audience: str = "", platform: str = "LinkedIn", count: int = 5) -> str:
    from content_ideas.ideas import card, research
    ideas = research(niche, audience, platform or "LinkedIn", count=int(count), keep=not HOSTED)
    return "\n\n".join(card(i) for i in ideas)


@tool("list_content_ideas", "Content-idea assistant (bank)", "Show the saved idea bank.")
def _list_ideas(agent) -> str:
    from content_ideas.ideas import bank_table, load
    return bank_table(load())


@tool("draft_post", "Content-idea assistant (draft)",
      "Write a first draft for a saved idea by its id.",
      {"idea_id": {"type": "integer"}, "past_posts": s("Past posts to match the voice.")}, ["idea_id"])
def _draft(agent, idea_id: int, past_posts: str = "") -> str:
    from content_ideas.ideas import draft
    return draft(int(idea_id), past_posts)


# ---------- 17 & 18. Answers from documents ----------
_INDEXES: dict = {}


def _index(key, build):
    if key not in _INDEXES:
        _INDEXES[key] = build()
    return _INDEXES[key]


def _with_sources(result: dict) -> str:
    from common.answer import to_markdown
    return to_markdown(result)


@tool("ask_team_docs", "Team FAQ bot",
      "Answer a question from a folder of team documents (handbook, policies), with sources. Without a folder "
      "it uses the example handbook.",
      {"question": s("The question."), "folder": s("Folder of team documents.")}, ["question"])
def _faq(agent, question: str, folder: str = "") -> str:
    from common.search import Index
    from team_faq_bot.bot import EXAMPLE_DOCS, ask_faq
    docs = str(_path(folder)) if folder else str(EXAMPLE_DOCS)
    index = _index(("faq", docs), lambda: Index.from_folder(docs))
    note = "" if folder else "\n\n_(Answered from the example handbook. Give a folder to use your own docs.)_"
    return _with_sources(ask_faq(index, question, docs)) + note


@tool("ask_my_notes", "Ask your notes",
      "Answer a question from the user's own notes folder, and optionally their saved library and decision "
      "journal, with sources. Without a folder or extras it uses the example notes.",
      {"question": s("The question."), "folder": s("Notes folder, e.g. an Obsidian vault."),
       "include_library": {"type": "boolean"}, "include_decisions": {"type": "boolean"}},
      ["question"])
def _notes(agent, question: str, folder: str = "", include_library: bool = False,
           include_decisions: bool = False) -> str:
    from ask_your_notes.notes import EXAMPLE_NOTES, ask_notes, build_index
    extras = [x for x, on in (("library", include_library), ("decisions", include_decisions)) if on and not HOSTED]
    notes = str(_path(folder)) if folder else ("" if extras else str(EXAMPLE_NOTES))
    # Library and journal change as you use them, so only cache plain folders.
    index = build_index(notes, extras) if extras else _index(("notes", notes), lambda: build_index(notes))
    note = "" if folder or extras else "\n\n_(Answered from the example notes. Give a folder to use yours.)_"
    return _with_sources(ask_notes(index, question)) + note
