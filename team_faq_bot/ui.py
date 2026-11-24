"""Test page for the team FAQ bot."""
import streamlit as st

from common.answer import to_markdown
from common.search import Index
from common.ui import pasted_key_for_call
from team_faq_bot.bot import EXAMPLE_DOCS, ask_faq, gaps_report, load_gaps

TITLE = "Team FAQ bot"
ORDER = 17


@st.cache_resource(show_spinner="Reading the documents...")
def _index(folder: str, _stamp: int) -> Index:
    return Index.from_folder(folder)


def _chat(folder: str) -> None:
    try:
        index = _index(folder, st.session_state.get("faq_reload", 0))
    except ValueError as e:
        st.warning(str(e))
        return
    st.caption(f"{len(index.files())} documents, {len(index.passages)} passages: " + ", ".join(index.files()[:8])
               + (" ..." if len(index.files()) > 8 else ""))
    for s in index.skipped:
        st.caption(s)
    if st.session_state.get("faq_folder") != folder:
        st.session_state["faq_folder"] = folder
        st.session_state["faq_history"] = []
    history = st.session_state.setdefault("faq_history", [])
    for q, md in history:
        st.chat_message("user").write(q)
        st.chat_message("assistant").markdown(md)
    q = st.chat_input("Ask about the team's docs, e.g. How many holiday days can I carry over?")
    if q:
        st.chat_message("user").write(q)
        try:
            with st.spinner("Looking it up..."), pasted_key_for_call():
                result = ask_faq(index, q, folder, [(hq, hmd.split("\n\n**Sources**")[0]) for hq, hmd in history])
        except SystemExit as e:
            st.error(str(e.code))
            return
        except ValueError as e:
            st.warning(str(e))
            return
        md = to_markdown(result)
        st.chat_message("assistant").markdown(md)
        history.append((q, md))


def render() -> None:
    st.header(TITLE)
    st.write("Point it at a folder of team documents (handbook, policies, how-tos). Ask questions in plain "
             "words and get short answers with the exact passages they came from. If the docs don't cover "
             "something, it says so instead of guessing, and logs the question so you know what to write next.")
    c1, c2 = st.columns([4, 1])
    folder = c1.text_input("Documents folder", value=str(EXAMPLE_DOCS),
                           help="Reads .md, .txt and .html (and .pdf with pypdf) in this folder and subfolders.")
    if c2.button("Reload docs"):
        st.session_state["faq_reload"] = st.session_state.get("faq_reload", 0) + 1
    tab_chat, tab_gaps = st.tabs(["Ask", "Unanswered questions"])
    with tab_chat:
        _chat(folder)
    with tab_gaps:
        st.markdown(gaps_report(load_gaps()))
