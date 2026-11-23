"""Test page for the weekly life-admin planner."""
from datetime import date
from pathlib import Path

import streamlit as st

from common.ui import run_and_show
from life_admin_planner.main import next_monday, plan_week

TITLE = "Weekly life-admin planner"
ORDER = 7

EXAMPLES = Path(__file__).parent / "examples"


def render() -> None:
    st.header(TITLE)
    st.write(
        "Give it your calendar for the week (upload an .ics export or paste it) and your task list. "
        "It flags clashes and picks three realistic priorities with a time slot for each."
    )

    if st.button("Load the example week"):
        st.session_state["lap_tasks"] = (EXAMPLES / "tasks.txt").read_text(encoding="utf-8")
        st.session_state["lap_cal_text"] = (EXAMPLES / "calendar.ics").read_text(encoding="utf-8")
        st.session_state["lap_week"] = date(2026, 11, 30)

    st.session_state.setdefault("lap_week", next_monday())
    with st.form("lap_form"):
        week_start = st.date_input("Week starting", key="lap_week")
        upload = st.file_uploader("Calendar export (.ics)", type=["ics"])
        cal_text = st.text_area("Or paste your week", key="lap_cal_text", height=150,
                                placeholder="Mon 9:30 standup\nTue 15:00 dentist\n...")
        tasks = st.text_area("Tasks (one per line)", key="lap_tasks", height=180)
        notes = st.text_input("Anything else (optional)", placeholder="gym Tue/Thu evenings")
        submitted = st.form_submit_button("Plan my week", type="primary")

    if submitted:
        calendar_text = upload.getvalue().decode("utf-8", errors="replace") if upload else cal_text
        if not tasks.strip():
            st.warning("Add at least a few tasks.")
            return
        run_and_show(plan_week, calendar_text, tasks, week_start, notes,
                     spinner="Planning your week...", filename="week_plan.md")
    st.caption("To export a calendar: Google Calendar > Settings > Import & export, or Apple Calendar > File > Export.")
