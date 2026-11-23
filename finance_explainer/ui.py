"""Test page for the personal finance explainer."""
from pathlib import Path

import streamlit as st

from common.ui import run_and_show
from finance_explainer.main import explain_export

TITLE = "Personal finance explainer"
ORDER = 13

EXAMPLE = Path(__file__).parent / "examples" / "sample_bank_export.csv"


def render() -> None:
    st.header(TITLE)
    st.write("Upload a CSV export of your bank or card transactions. Your spending is added up exactly on your "
             "computer, and Claude explains it in plain English: where it goes, what changed, regular payments "
             "you might have forgotten, and a few practical ideas.")
    use_example = st.checkbox("Use the sample export (3 months, made-up data)")
    with st.form("fe_form"):
        upload = st.file_uploader("Bank or card export (CSV)", type=["csv", "txt"], disabled=use_example)
        c1, c2 = st.columns(2)
        currency = c1.text_input("Currency symbol", value="$")
        day_first = c2.checkbox("Dates are day/month (UK, India, Europe)")
        context = st.text_input("Anything that helps (optional)",
                                placeholder="Rent is paid from another account; family of 3")
        submitted = st.form_submit_button("Explain my spending", type="primary")
    if submitted:
        if use_example:
            text = EXAMPLE.read_text(encoding="utf-8")
        elif upload is not None:
            text = upload.getvalue().decode("utf-8-sig", errors="replace")
        else:
            st.warning("Upload a CSV export, or tick the sample export.")
            return
        run_and_show(explain_export, text, currency or "$", day_first, context,
                     spinner="Reading transactions and explaining your spending (this can take a minute)...",
                     filename="spending_explained.md")
    st.caption("Card and account numbers (6+ digits) and email addresses are masked. Transaction descriptions "
               "and totals are sent to Claude; the full file isn't. Not financial advice.")
