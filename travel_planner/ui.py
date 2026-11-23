"""Test page for the travel planner."""
import streamlit as st

from common.ui import run_and_show
from travel_planner.main import plan_trip

TITLE = "Travel planner"
ORDER = 4


def render() -> None:
    st.header(TITLE)
    st.write(
        "Describe your trip or paste your booking emails. Claude checks visas and entry rules, "
        "passport validity, tight transfers, luggage and check-in deadlines, with source links."
    )

    with st.form("travel_form"):
        trip = st.text_input("Trip (route and dates)", placeholder="London to Tokyo via Doha, 3-17 March, then Seoul")
        bookings = st.text_area("Or paste bookings / itinerary (optional)", height=160,
                                placeholder="Flight 1: QR 4 LHR -> DOH, 3 Mar 08:35...")
        col1, col2 = st.columns(2)
        passport = col1.text_input("Passport nationality", placeholder="Indian")
        airline = col2.text_input("Airline and fare (optional)", placeholder="Qatar Airways, economy")
        notes = st.text_input("Anything else (optional)", placeholder="travelling with a toddler")
        submitted = st.form_submit_button("Check my trip", type="primary")

    if submitted:
        if not (trip.strip() or bookings.strip()):
            st.warning("Enter a trip or paste your bookings.")
            return
        if not passport.strip():
            st.info("No passport nationality given, so entry rules will be general. Add it for a better check.")
        run_and_show(plan_trip, trip, passport, airline, notes, bookings,
                     spinner="Checking visas, luggage and transfers (this can take a minute or two)...",
                     filename="trip_check.md")
    st.caption("Always confirm visa and entry rules on official government sites before you travel.")
