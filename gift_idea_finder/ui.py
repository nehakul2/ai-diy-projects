"""Test page for Gift idea finder."""
import streamlit as st

from common.ui import run_and_show
from gift_idea_finder.main import find_gifts

TITLE = "Gift idea finder"
ORDER = 2


def render() -> None:
    st.header(TITLE)
    st.write("Describe the person and a budget. Claude searches the web for five ideas with links.")

    with st.form("gift_form"):
        who = st.text_input("Who is the gift for?", placeholder="my sister, 30, just moved to Denver")
        budget = st.text_input("Budget (with currency)", placeholder="50 USD")
        likes = st.text_input("Things they like", placeholder="hiking, coffee, crime podcasts")
        col1, col2 = st.columns(2)
        occasion = col1.text_input("Occasion (optional)", placeholder="birthday")
        country = col2.text_input("Where to shop (optional)", placeholder="US")
        submitted = st.form_submit_button("Find gift ideas", type="primary")

    if submitted:
        if not (who.strip() and budget.strip() and likes.strip()):
            st.warning("Fill in who it's for, a budget and a few things they like.")
        else:
            run_and_show(find_gifts, who, budget, likes, occasion, country,
                         spinner="Searching the web for ideas (this can take a minute)...",
                         filename="gift_ideas.md")
