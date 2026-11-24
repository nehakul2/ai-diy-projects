"""Chat page for the personal agent: one assistant that uses every project."""
import tempfile
from pathlib import Path

import streamlit as st

from common.ui import pasted_key_for_call
from personal_agent.agent import Agent

TITLE = "Personal agent (chat)"
ORDER = 0

UPLOADS = Path(tempfile.gettempdir()) / "ai-diy-agent-uploads"
EXAMPLES = [
    "Gift ideas for my dad, around $60, he loves gardening and jazz",
    "What's on my job tracker this week?",
    "Tidy my Downloads folder (just show me the plan first)",
    "Turn these notes into actions: call bank re card, Sam wants slides by Fri, book dentist",
]


def _agent() -> Agent:
    if "agent" not in st.session_state:
        st.session_state["agent"] = Agent()
        st.session_state["chat"] = []  # what's shown: {"role", "text", "results"}
    return st.session_state["agent"]


def _show(entry: dict) -> None:
    with st.chat_message(entry["role"]):
        st.markdown(entry["text"])
        for label, output, ok in entry.get("results", []):
            with st.expander(f"{'📎' if ok else '⚠️'} {label}", expanded=False):
                st.markdown(output)


def _attachment_note() -> str:
    """Save an attached file to a temp folder and tell the agent where it is."""
    f = st.session_state.get("agent_file")
    if not f or st.session_state.get("agent_file_sent") == f.file_id:
        return ""
    UPLOADS.mkdir(exist_ok=True)
    path = UPLOADS / Path(f.name).name
    path.write_bytes(f.getvalue())
    st.session_state["agent_file_sent"] = f.file_id
    return f"\n\n[Attached file: {path}]"


def _ask(agent: Agent, text: str) -> None:
    text = text + _attachment_note()
    st.session_state["chat"].append({"role": "user", "text": text})
    _show(st.session_state["chat"][-1])
    with st.chat_message("assistant"):
        status = st.status("Thinking...", expanded=False)
        try:
            with pasted_key_for_call():
                result = agent.send(text, on_tool=lambda label: status.update(label=f"Using {label}..."))
        except SystemExit as e:
            result = {"reply": f"⚠️ {e.code}", "results": []}
        except Exception as e:
            result = {"reply": f"⚠️ Something went wrong: {type(e).__name__}: {e}", "results": []}
        status.update(label="Done", state="complete")
    st.session_state["chat"].append({"role": "assistant", "text": result["reply"], "results": result["results"]})
    st.rerun()


def _confirm(agent: Agent, yes: bool) -> None:
    outcome = agent.answer_confirmation(yes)
    icon = "" if not yes else ("⚠️ " if outcome.startswith("It failed") else "✅ ")
    st.session_state["chat"].append({"role": "assistant", "text": icon + outcome})


def render() -> None:
    agent = _agent()
    st.header("Your personal agent")
    st.write("Ask for anything your projects can do, in plain words. It picks the right one. "
             "Files: attach one below, or type its path (like `~/Downloads/statement.csv`).")

    for entry in st.session_state["chat"]:
        _show(entry)

    if agent.pending:
        with st.chat_message("assistant"):
            st.warning(agent.pending["question"])
            yes, no = st.columns(2)
            if yes.button("Confirm", type="primary", use_container_width=True):
                _confirm(agent, True)
                st.rerun()
            if no.button("Cancel", use_container_width=True):
                _confirm(agent, False)
                st.rerun()

    if not st.session_state["chat"]:
        st.caption("Try one of these:")
        for i, example in enumerate(EXAMPLES):
            if st.button(example, key=f"example_{i}"):
                _ask(agent, example)

    with st.expander("📎 Attach a file (resume, bank export, calendar, emails...)"):
        st.file_uploader("File", key="agent_file", label_visibility="collapsed")
        st.caption("It's saved to a temporary folder on this computer and only its path goes into the chat.")

    if st.button("Start a new chat"):
        for key in ("agent", "chat", "agent_file_sent"):
            st.session_state.pop(key, None)
        st.rerun()

    text = st.chat_input("Ask me anything...", disabled=bool(agent.pending))
    if text:
        _ask(agent, text)
