"""Test page for the downloads organiser."""
from pathlib import Path

import streamlit as st

from common.ui import pasted_key_for_call
from downloads_organiser.organiser import DEFAULT_LIMIT, apply_plan, make_plan, plan_to_markdown, undo

TITLE = "Downloads organiser"
ORDER = 5


def render() -> None:
    st.header(TITLE)
    st.write(
        "Point it at a folder. Claude looks at file **names, sizes and dates only** (never contents) and "
        "suggests clearer names and a few folders. You see a preview first, and nothing moves until you confirm."
    )

    with st.form("organiser_form"):
        folder = st.text_input("Folder", value=str(Path.home() / "Downloads"))
        limit = st.number_input("How many of the newest files", min_value=1, max_value=200, value=DEFAULT_LIMIT)
        submitted = st.form_submit_button("Preview the plan", type="primary")

    if submitted:
        try:
            with st.spinner("Asking Claude for a plan..."), pasted_key_for_call():
                st.session_state["organiser_plan"] = make_plan(folder, int(limit))
        except SystemExit as e:
            st.error(str(e.code))
        except Exception as e:
            st.error(f"{type(e).__name__}: {e}")

    plan = st.session_state.get("organiser_plan")
    if plan:
        st.markdown(plan_to_markdown(plan))
        if plan["moves"]:
            sure = st.checkbox(f"I've checked the preview. Move {len(plan['moves'])} files in {plan['folder']}.")
            if st.button("Apply changes", disabled=not sure):
                log, messages = apply_plan(plan)
                st.session_state.pop("organiser_plan")
                st.session_state["organiser_last_log"] = str(log)
                for m in messages:
                    st.write(m)

    last = st.session_state.get("organiser_last_log")
    if last and Path(last).exists():
        if st.button("Undo the last change"):
            for m in undo(last):
                st.write(m)
            st.session_state.pop("organiser_last_log")
    st.caption("Tip: try it on a test folder with a few copied files first.")
