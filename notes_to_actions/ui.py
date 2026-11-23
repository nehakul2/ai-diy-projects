"""Test page for Notes into actions."""
from pathlib import Path

import streamlit as st

from common.ui import run_and_show
from notes_to_actions.main import notes_to_actions

TITLE = "Notes into actions"
ORDER = 1

EXAMPLE = Path(__file__).parent / "examples" / "team_sync.txt"


def _load_upload() -> None:
    """Copy a newly uploaded file into the notes box (only when the upload changes)."""
    uploaded = st.session_state.get("notes_file")
    if uploaded:
        st.session_state["notes_input"] = uploaded.getvalue().decode("utf-8", errors="replace")


def render() -> None:
    st.header(TITLE)
    st.write("Paste messy notes and get a summary, a task list and a follow-up message.")

    if st.button("Load example notes"):
        st.session_state["notes_input"] = EXAMPLE.read_text(encoding="utf-8")
    st.file_uploader("Or upload a .txt or .md file", type=["txt", "md"],
                     key="notes_file", on_change=_load_upload)

    notes = st.text_area("Notes", key="notes_input", height=300)
    if st.button("Turn into actions", type="primary"):
        if not notes.strip():
            st.warning("Add some notes first.")
        else:
            run_and_show(notes_to_actions, notes, filename="actions.md")
