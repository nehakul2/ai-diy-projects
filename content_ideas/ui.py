"""Test page for the content-idea research assistant."""
from pathlib import Path

import streamlit as st

from common.ui import pasted_key_for_call
from content_ideas.ideas import bank_table, card, draft, ideas_file, load, research, set_status
from content_ideas.prompt import PLATFORMS

TITLE = "Content-idea assistant"
ORDER = 16

EXAMPLE = Path(__file__).parent / "examples" / "past_posts.txt"


def _call(fn, *args, spinner: str, **kwargs):
    try:
        with st.spinner(spinner), pasted_key_for_call():
            return fn(*args, **kwargs)
    except SystemExit as e:
        st.error(str(e.code))
    except ValueError as e:
        st.warning(str(e))
    return None


def _research() -> None:
    if st.button("Load example (product management niche)"):
        st.session_state.update(ci_niche="AI tools and habits for product managers",
                                ci_audience="PMs at startups and mid-size tech companies",
                                ci_past=EXAMPLE.read_text(encoding="utf-8"))
    with st.form("ci_form"):
        niche = st.text_input("What do you create content about?", key="ci_niche")
        audience = st.text_input("Who's it for? (optional)", key="ci_audience")
        c1, c2 = st.columns(2)
        platform = c1.selectbox("Platform", PLATFORMS)
        count = c2.slider("How many ideas", 1, 10, 5)
        past = st.text_area("A few of your past posts (optional: matches your voice, avoids repeats)",
                            key="ci_past", height=140)
        submitted = st.form_submit_button("Find ideas", type="primary")
    if submitted:
        found = _call(research, niche, audience, platform, past, count,
                      spinner="Researching what your audience is talking about (a couple of minutes)...")
        if found:
            st.success(f"Found {len(found)} ideas and saved them to your idea bank.")
            for i in found:
                with st.container(border=True):
                    st.markdown(card(i))


def _bank() -> None:
    items = load()
    show_all = st.checkbox("Include posted and skipped ideas")
    st.markdown(bank_table(items, show_all))
    st.caption(f"Saved in {ideas_file()}")
    open_items = [i for i in items if show_all or i["status"] in ("new", "drafted")]
    if not open_items:
        return
    choice = st.selectbox("Pick an idea", open_items, format_func=lambda i: f"{i['id']}. {i['title']}")
    st.markdown(card(choice))
    c1, c2, c3 = st.columns(3)
    if c1.button("Write a first draft", type="primary"):
        text = _call(draft, choice["id"], st.session_state.get("ci_past", ""), spinner="Writing a first draft...")
        if text:
            st.markdown("---")
            st.markdown(text)
            st.download_button("Download draft", text + "\n", file_name=f"draft-{choice['id']}.md")
    if c2.button("Mark as posted"):
        set_status(choice["id"], "posted")
        st.rerun()
    if c3.button("Skip this idea"):
        set_status(choice["id"], "skipped")
        st.rerun()


def render() -> None:
    st.header(TITLE)
    st.write("Tell it your niche and platform. Claude searches what your audience is discussing right now and "
             "suggests ideas, each with a hook, a fresh angle, why it's timely (with a source), an outline and a "
             "score. Save the good ones and turn them into first drafts in your voice.")
    tab_find, tab_bank = st.tabs(["Find ideas", f"Idea bank ({len(load())})"])
    with tab_find:
        _research()
    with tab_bank:
        _bank()
