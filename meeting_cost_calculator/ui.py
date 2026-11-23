"""Test page for the meeting cost calculator."""
from pathlib import Path

import streamlit as st

from common.ui import run_and_show
from meeting_cost_calculator.costs import looks_like_csv
from meeting_cost_calculator.main import calculate

TITLE = "Meeting cost calculator"
ORDER = 11

EXAMPLES = Path(__file__).parent / "examples"


def render() -> None:
    st.header(TITLE)
    st.write("Describe your recurring meetings (or upload a calendar export or CSV). You'll see what they cost "
             "each month and year, and Claude suggests which to shorten, trim, make async or cancel.")

    col1, col2 = st.columns(2)
    if col1.button("Load example: team description"):
        st.session_state["mc_text"] = (EXAMPLES / "team_meetings.txt").read_text(encoding="utf-8")
    if col2.button("Load example: CSV"):
        st.session_state["mc_text"] = (EXAMPLES / "meetings.csv").read_text(encoding="utf-8")

    with st.form("mc_form"):
        upload = st.file_uploader("Calendar export (.ics), CSV or text file", type=["ics", "csv", "txt", "md"])
        text = st.text_area("Or describe your meetings", key="mc_text", height=200,
                            placeholder="Daily standup, 15 min, 6 people, every weekday...")
        c1, c2 = st.columns([2, 1])
        rate = c1.number_input("Average cost of one person's hour (salary plus overheads)",
                               min_value=1.0, value=75.0, step=5.0)
        currency = c2.text_input("Currency symbol", value="$")
        context = st.text_input("About your team (optional)", placeholder="8-person product team, mostly remote")
        advice = st.checkbox("Ask Claude where to cut", value=True,
                             help="Untick to only do the maths. That needs CSV input and makes no API call.")
        submitted = st.form_submit_button("Calculate", type="primary")

    if submitted:
        if upload is not None:
            text = upload.getvalue().decode("utf-8", errors="replace")
        if not text.strip():
            st.warning("Describe your meetings or upload a file.")
            return
        if not advice and not looks_like_csv(text):
            st.warning("Without Claude, the input must be a CSV with columns title, minutes, attendees, per_month.")
            return
        run_and_show(calculate, text, rate, currency or "$", context, advice=advice,
                     spinner="Reading your meetings and looking for savings...", filename="meeting_costs.md")
    st.caption("All the maths happens on your computer. Only the meeting list is sent to Claude, for the advice.")
