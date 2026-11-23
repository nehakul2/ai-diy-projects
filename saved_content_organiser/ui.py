"""Test page for the saved-content organiser."""
from pathlib import Path

import streamlit as st

from common.ui import pasted_key_for_call
from saved_content_organiser.library import KINDS, add_item, card, find, library_file, load, mark, tag_counts

TITLE = "Saved-content organiser"
ORDER = 9

EXAMPLE = Path(__file__).parent / "examples" / "podcast_notes.txt"


def _add() -> None:
    if st.button("Load example podcast notes"):
        st.session_state["sco_text"] = EXAMPLE.read_text(encoding="utf-8")
        st.session_state["sco_note"] = "Want to try the 'two-minute rule' idea for my weekly planning."
    with st.form("sco_add"):
        url = st.text_input("Link (article, video, podcast page)", placeholder="https://...")
        text = st.text_area("Or paste text / your notes", key="sco_text", height=150)
        note = st.text_input("Why you saved it (optional)", key="sco_note")
        interests = st.text_input("Your interests (optional)", key="sco_interests",
                                  placeholder="product analytics, parenting, running")
        submitted = st.form_submit_button("Save to library", type="primary")
    if submitted:
        try:
            with st.spinner("Reading and summarising..."), pasted_key_for_call():
                item = add_item(url, note, text, interests)
        except SystemExit as e:
            st.error(str(e.code))
            return
        except ValueError as e:
            st.warning(str(e))
            return
        st.success("Saved.")
        st.markdown(card(item))


def _browse(items: list[dict]) -> None:
    counts = tag_counts(items)
    col1, col2, col3 = st.columns(3)
    tag = col1.selectbox("Tag", [""] + [t for t, _ in counts.most_common()],
                         format_func=lambda t: t and f"{t} ({counts[t]})" or "All tags")
    kind = col2.selectbox("Type", [""] + KINDS, format_func=lambda k: k or "All types")
    query = col3.text_input("Search")
    show_done = st.checkbox("Include items marked done")
    results = find(items, tag, query, kind, show_done)
    st.caption(f"{len(results)} items · saved in {library_file()}")
    for i in results:
        with st.container(border=True):
            st.markdown(card(i))
            label = "Mark not done" if i.get("done") else "Mark done"
            if st.button(label, key=f"sco_done_{i['id']}"):
                mark(i["id"], done=not i.get("done"))
                st.rerun()


def render() -> None:
    st.header(TITLE)
    st.write("Save articles, videos and podcast notes. Claude tags them, summarises them and notes why they "
             "matter to you, so you can find them again.")
    items = load()
    tab_browse, tab_add = st.tabs([f"Library ({len(items)})", "Add something"])
    with tab_browse:
        if items:
            _browse(items)
        else:
            st.info("Nothing saved yet. Add something in the next tab.")
    with tab_add:
        _add()
