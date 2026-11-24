"""The personal agent: one chat that picks the right project for what you ask.

Claude sees every project as a tool (personal_agent/tools.py), decides which to call,
reads the result, and replies. File moves never happen inside this loop: the agent can
only *ask* to move files, and the chat page or CLI moves them after you say yes.
"""
import json
import os
import sys
from datetime import date

from common.claude import create, friendly_errors, make_client
from personal_agent.tools import HANDLERS, HOSTED, LABELS, available_tools, blocked_tools, run_confirmed

MAX_STEPS = 12  # tool rounds per message, so a confused run can't loop forever
MAX_RESULT_CHARS = 30000

SYSTEM = """You are a personal assistant for {name}. Today is {today}. You run on their own computer and can use
these tools, each one a small project they built:

- notes into actions, gift ideas, inbox clean-up, travel checks, resume vs job matching, weekly planning
- a job-search tracker, a saved-reading library, a decision journal, a content-idea bank
- meeting costs, a reading-list briefing, a bank-export explainer, a personal dashboard
- answers with sources from their notes folder or their team's documents
- tidying a folder (Downloads) or sorting photos into event folders

How to work:
- Pick the tool that fits and call it. If something essential is missing (a budget, an hourly rate, which
  file), ask one short question instead of guessing. Use sensible defaults for anything optional.
- Files are given as paths on this computer (e.g. ~/Downloads/statement.csv). If the user attached a file,
  its path is in their message.
- The user sees each tool's full result under your reply, so don't repeat it. Reply in a few sentences:
  the headline, anything that needs their attention, and a natural next step.
- Moving files: always make a preview first (plan_downloads_tidy / plan_photo_tidy) and stop so they can look.
  Call confirm_tidy only after they say to go ahead; the files move only when they press Confirm. Never say
  files were moved unless you were told they were.
- If a tool fails, explain the problem in plain words and how to fix it.
- Plain, friendly language. No jargon."""


HOSTED_SYSTEM = """You are a demo of a personal assistant that {name} built from 18 small AI projects.
Today is {today}. The person chatting is probably one of {name}'s friends trying it out. You can use the
tools you've been given, for example: notes into actions, gift ideas, inbox clean-up (pasted or attached
emails), travel checks, resume vs job matching, weekly planning, meeting costs, a reading-list briefing, a
bank-export explainer and content-idea research. If you have the job tracker, library, decision journal or
idea-bank tools, what you save there is private to this person and is kept for their next visit.

How to work:
- Pick the tool that fits and call it. If something essential is missing (a budget, an hourly rate), ask
  one short question instead of guessing. Use sensible defaults for anything optional.
- Files: they attach them with the 📎 button and the path appears in their message. You can't open
  anything else on any computer. Projects you have no tool for (tidying a Downloads folder, sorting photos,
  the dashboard) only work in the version on {name}'s own computer; say so if asked.
- The user sees each tool's full result under your reply, so don't repeat it. Reply in a few sentences:
  the headline, anything that needs their attention, and a natural next step.
- If a tool fails, explain the problem in plain words.
- Plain, friendly language. If they ask what you can do, give a short list with an example for each."""


def _blocks_text(content) -> str:
    return "".join(b.text for b in content if b.type == "text").strip()


class Agent:
    def __init__(self, name: str = "", effort: str = "medium"):
        self.name = name or os.environ.get("AGENT_NAME", "").strip() or ("the builder" if HOSTED else "the user")
        self.effort = effort
        self.messages: list = []
        self.plans: dict = {}        # plan_id -> tidy-up plan made in this chat
        self.pending: dict | None = None  # a file move waiting for the user's yes/no

    # Called by the confirm_* tools.
    def request_confirmation(self, question: str, kind: str, **details) -> None:
        if kind == "apply":
            details["plan"] = self.plans[details["plan_id"]]
        self.pending = {"question": question, "kind": kind, **details}

    def answer_confirmation(self, yes: bool) -> str:
        """Run (or cancel) the pending file move. The outcome is noted for Claude's next turn."""
        action, self.pending = self.pending, None
        if not action:
            return "Nothing is waiting for confirmation."
        if yes:
            try:
                outcome = run_confirmed(action)
            except Exception as e:
                outcome = f"It failed: {e}"
            if action["kind"] == "apply":
                self.plans.pop(action.get("plan_id"), None)  # a plan can only be applied once
        else:
            outcome = "Cancelled. Nothing moved."
        self.messages.append({"role": "user", "content": f"[I answered the confirmation: {'yes' if yes else 'no'}. "
                              f"Result:\n{outcome}]"})
        return outcome

    def send(self, text: str, on_tool=None) -> dict:
        """Send one message. Returns {"reply": str, "results": [(label, markdown, ok)]}.

        on_tool(label) is called before each tool runs, so a UI can show progress.
        """
        self.messages.append({"role": "user", "content": text})
        system = (HOSTED_SYSTEM if HOSTED else SYSTEM).format(name=self.name, today=f"{date.today():%A %d %B %Y}")
        results = []
        with friendly_errors():
            client = make_client()
            for _ in range(MAX_STEPS):
                response = create(client, system=system, messages=self.messages, tools=available_tools(),
                                  max_tokens=16000, output_config={"effort": self.effort})
                # Keep the whole reply (including thinking blocks) so the next turn has full context.
                self.messages.append({"role": "assistant", "content": response.content})
                if response.stop_reason != "tool_use":
                    break
                tool_results = []
                for block in response.content:
                    if block.type != "tool_use":
                        continue
                    label = LABELS.get(block.name, block.name)
                    if on_tool:
                        on_tool(label)
                    output, ok = self._run(block.name, block.input)
                    results.append((label, output, ok))
                    tool_results.append({"type": "tool_result", "tool_use_id": block.id,
                                         "content": output[:MAX_RESULT_CHARS], "is_error": not ok})
                # All results go back together in one message.
                self.messages.append({"role": "user", "content": tool_results})
            else:
                return {"reply": "I took too many steps on that one and stopped. Could you rephrase or split it up?",
                        "results": results}

        if response.stop_reason == "refusal":
            reply = "I can't help with that one."
        else:
            reply = _blocks_text(response.content)
            if response.stop_reason == "max_tokens":
                reply += "\n\n[My reply was cut off.]"
        return {"reply": reply, "results": results}

    def _run(self, name: str, args: dict) -> tuple[str, bool]:
        fn = HANDLERS.get(name)
        if not fn or name in blocked_tools():
            return f"Unknown tool {name}.", False
        try:
            return fn(self, **(args or {})), True
        except SystemExit as e:  # the projects stop with a friendly message on API errors
            return str(e.code or "The project stopped without a message."), False
        except TypeError as e:
            return f"Wrong inputs for {name}: {e}", False
        except Exception as e:
            return f"{type(e).__name__}: {e}", False


def describe_tools() -> str:
    """A short list of what the agent can do (used by the CLI's 'help')."""
    seen = []
    for t in available_tools():
        label = LABELS[t["name"]].split(" (")[0]
        if label not in seen and not label.startswith("Ask to"):
            seen.append(label)
    return ", ".join(seen)


if __name__ == "__main__":  # quick check: python -m personal_agent.agent
    print(json.dumps([t["name"] for t in available_tools()], indent=1), file=sys.stderr)
