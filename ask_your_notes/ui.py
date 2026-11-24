"""Test page for the ask-your-notes assistant."""
import streamlit as st

from ask_your_notes.notes import EXAMPLE_NOTES, EXTRAS, ask_notes, build_index
from common.answer import to_markdown
from common.ui import pasted_key_for_call

TITLE = "Ask your notes"
ORDER = 18


@st.cache_resource(show_spinner="Reading your notes...")
def _index(folder: str, extras: tuple[str, ...], _stamp: int):
    return build_index(folder, list(extras))


def render() -> None:
    st.header(TITLE)
    st.write("Ask questions across your own notes (an Obsidian vault, Markdown or text files, exported docs), "
             "plus your saved articles and decision journal from the earlier projects. Answers quote the notes "
             "they came from, with dates and numbers, and say so when your notes don't cover it.")
    c1, c2 = st.columns([4, 1])
    folder = c1.text_input("Notes folder (leave empty to search only the extras)", value=str(EXAMPLE_NOTES))
    if c2.button("Reload"):
        st.session_state["notes_reload"] = st.session_state.get("notes_reload", 0) + 1
    extras = st.multiselect("Also search", EXTRAS, format_func={"library": "Saved-content library (project 9)",
                                                                "decisions": "Decision journal (project 10)"}.get)
    try:
        index = _index(folder.strip(), tuple(extras), st.session_state.get("notes_reload", 0))
    except ValueError as e:
        st.warning(str(e))
        return
    st.caption(f"Searching {len(index.files())} notes and items ({len(index.passages)} passages).")
    for s in index.skipped:
        st.caption(s)
    key = (folder.strip(), tuple(extras))
    if st.session_state.get("notes_key") != key:
        st.session_state["notes_key"] = key
        st.session_state["notes_history"] = []
    history = st.session_state["notes_history"]
    for q, md in history:
        st.chat_message("user").write(q)
        st.chat_message("assistant").markdown(md)
    q = st.chat_input("Ask your notes, e.g. When is my Lisbon trip?")
    if q:
        st.chat_message("user").write(q)
        try:
            with st.spinner("Searching your notes..."), pasted_key_for_call():
                result = ask_notes(index, q, [(hq, hmd.split("\n\n**Sources**")[0]) for hq, hmd in history])
        except SystemExit as e:
            st.error(str(e.code))
            return
        except ValueError as e:
            st.warning(str(e))
            return
        md = to_markdown(result)
        st.chat_message("assistant").markdown(md)
        history.append((q, md))
