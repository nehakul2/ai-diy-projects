"""Test page for the decision journal pattern finder."""
from datetime import date

import streamlit as st

from common.ui import pasted_key_for_call
from decision_journal.journal import (MIN_REVIEWED_FOR_PATTERNS, OUTCOMES, card, decisions_file, due,
                                      find_patterns, load, load_samples, log_decision, record_review)

TITLE = "Decision journal"
ORDER = 10


def _call(fn, *args, spinner: str, **kwargs):
    """Run a function that may call Claude; show errors the same way as the other pages."""
    try:
        with st.spinner(spinner), pasted_key_for_call():
            return fn(*args, **kwargs)
    except SystemExit as e:
        st.error(str(e.code))
    except ValueError as e:
        st.warning(str(e))
    return None


def _log() -> None:
    with st.form("dj_log"):
        decision = st.text_input("Decision", placeholder="Accept the team lead role")
        context = st.text_area("Context: what's going on and why now", height=80)
        options = st.text_input("Options you considered", placeholder="take the role; stay as engineer")
        expected = st.text_input("What you expect to happen")
        confidence = st.slider("How confident are you it's the right call? (%)", 0, 100, 70, step=5)
        col1, col2 = st.columns(2)
        pick_date = col1.checkbox("Choose my own review date")
        review_on = col2.date_input("Review on", value=None, min_value=date.today())
        sharpen = st.checkbox("Ask Claude for hidden assumptions and signals to watch", value=True)
        submitted = st.form_submit_button("Log decision", type="primary")
    if submitted:
        d = _call(log_decision, decision, context, options, expected, confidence,
                  review_on.isoformat() if pick_date and review_on else "", sharpen=sharpen,
                  spinner="Finding assumptions and signals to watch...")
        if d:
            st.success(f"Saved. Review it on {d['review_on']}.")
            st.markdown(card(d))


def _journal(items: list[dict]) -> None:
    show = st.radio("Show", ["All", "Waiting for review", "Reviewed"], horizontal=True)
    if show == "Waiting for review":
        items = [d for d in items if not d.get("review")]
    elif show == "Reviewed":
        items = [d for d in items if d.get("review")]
    st.caption(f"{len(items)} decisions · saved in {decisions_file()}")
    for d in reversed(items):
        with st.container(border=True):
            st.markdown(card(d))


def _review(items: list[dict]) -> None:
    open_items = [d for d in items if not d.get("review")]
    if not open_items:
        st.info("Every decision has been reviewed.")
        return
    due_ids = {d["id"] for d in due(items)}
    choice = st.selectbox("Decision", open_items, format_func=lambda d: (
        f"{d['id']}. {d['decision']}" + (" (due now)" if d["id"] in due_ids else f" (due {d['review_on']})")))
    with st.expander("What you wrote at the time"):
        st.markdown(card(choice))
    with st.form("dj_review"):
        outcome = st.radio("How did it turn out compared with what you expected?", OUTCOMES, horizontal=True)
        what = st.text_area("What happened", height=80)
        held = st.text_input("Which assumptions held or failed?")
        lesson = st.text_input("Lesson (optional)")
        submitted = st.form_submit_button("Save review", type="primary")
    if submitted:
        d = _call(record_review, choice["id"], outcome, what, held, lesson, spinner="Saving...")
        if d:
            st.success("Review saved.")
            st.markdown(card(d))


def _patterns(items: list[dict]) -> None:
    reviewed = sum(1 for d in items if d.get("review") and d["review"]["outcome"] != "too early to tell")
    st.write(f"Claude looks across your reviewed decisions for patterns in how you decide. "
             f"You have {reviewed} reviewed (at least {MIN_REVIEWED_FOR_PATTERNS} needed).")
    if st.button("Find patterns", type="primary", disabled=reviewed < MIN_REVIEWED_FOR_PATTERNS):
        result = _call(find_patterns, items, spinner="Looking for patterns (this can take a minute)...")
        if result:
            st.markdown(result)
            st.download_button("Download as Markdown", result, file_name="decision-patterns.md")


def render() -> None:
    st.header(TITLE)
    st.write("Log important decisions with what you expect and why. Review them later, and Claude finds "
             "patterns in how you decide.")
    items = load()
    if not items:
        st.info("Your journal is empty. Log a decision below, or load 5 sample decisions to try the pattern finder.")
        if st.button("Load sample decisions"):
            _call(load_samples, spinner="Loading...")
            st.rerun()
    tabs = st.tabs(["Log a decision", f"Journal ({len(items)})", f"Review ({len(due(items))} due)", "Patterns"])
    with tabs[0]:
        _log()
    with tabs[1]:
        _journal(items)
    with tabs[2]:
        _review(items)
    with tabs[3]:
        _patterns(items)
