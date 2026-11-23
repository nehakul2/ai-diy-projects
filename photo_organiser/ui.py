"""Test page for the photo organiser by event."""
import tempfile
from pathlib import Path

import streamlit as st

from common.ui import pasted_key_for_call
from photo_organiser.organiser import apply_plan, make_plan, plan_to_markdown, undo

TITLE = "Photo organiser by event"
ORDER = 14


def _make_samples() -> None:
    from photo_organiser.examples.make_sample_photos import make
    folder = Path(tempfile.mkdtemp(prefix="sample-photos-"))
    make(folder)
    st.session_state["po_folder"] = str(folder)
    st.session_state.pop("po_plan", None)


def render() -> None:
    st.header(TITLE)
    st.write("Point it at a folder of photos. They're grouped into events by when (and where) they were taken, "
             "and Claude names each one from a few small thumbnails, like \"2026-07-14 Beach day in Santa Cruz\". "
             "You see a preview first, nothing moves until you confirm, and you can undo.")
    st.session_state.setdefault("po_folder", str(Path.home() / "Pictures"))
    st.button("Make a folder of sample photos to try it on", on_click=_make_samples)

    with st.form("po_form"):
        folder = st.text_input("Folder (only photos directly inside it are sorted)", key="po_folder")
        c1, c2 = st.columns(2)
        gap = c1.number_input("Hours between photos that start a new event", 1.0, 72.0, 6.0, step=1.0)
        min_photos = c2.number_input("Groups smaller than this go into 'Other photos'", 1, 20, 3)
        use_ai = st.checkbox("Ask Claude to name the events", value=True)
        thumbs = st.checkbox("Send 3 small thumbnails per event (better names)", value=True)
        submitted = st.form_submit_button("Preview the plan", type="primary")

    if submitted:
        try:
            with st.spinner("Reading photo dates and naming events..."), pasted_key_for_call():
                st.session_state["po_plan"] = make_plan(folder, gap, int(min_photos), use_ai=use_ai,
                                                        thumbnails=thumbs)
        except SystemExit as e:
            st.error(str(e.code))
        except ValueError as e:
            st.warning(str(e))

    plan = st.session_state.get("po_plan")
    if plan:
        st.markdown(plan_to_markdown(plan))
        if plan["moves"]:
            sure = st.checkbox(f"I've checked the preview. Move {len(plan['moves'])} files into "
                               f"{len(plan['events'])} folders in {plan['folder']}.")
            if st.button("Move the photos", disabled=not sure):
                log, messages = apply_plan(plan)
                st.session_state.pop("po_plan")
                st.session_state["po_last_log"] = str(log)
                for m in messages:
                    st.write(m)

    last = st.session_state.get("po_last_log")
    if last and Path(last).exists():
        if st.button("Undo the last change"):
            for m in undo(last):
                st.write(m)
            st.session_state.pop("po_last_log")
    st.caption("Sent to Claude: dates, counts, a few file names, rough location (about 1 km) and, if ticked, "
               "3 small thumbnails per event. Never the full photos. Nothing is deleted or overwritten.")
