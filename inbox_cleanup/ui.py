"""Test page for the inbox clean-up helper."""
from pathlib import Path

import streamlit as st

from common.ui import run_and_show
from inbox_cleanup.emails import MAX_BODY_CHARS, from_eml_bytes, from_text
from inbox_cleanup.main import MAX_EMAILS, sort_emails

TITLE = "Inbox clean-up helper"
ORDER = 3

SAMPLE = Path(__file__).parent / "examples" / "sample_inbox.txt"


def render() -> None:
    st.header(TITLE)
    st.write(
        "Paste a few emails (put a line with only `---` between them) or upload saved `.eml` files. "
        "Claude suggests reply, keep, archive or unsubscribe for each. Nothing in your mailbox changes."
    )

    if st.button("Load the sample inbox"):
        st.session_state["inbox_text"] = SAMPLE.read_text(encoding="utf-8")

    with st.form("inbox_form"):
        text = st.text_area("Pasted emails", key="inbox_text", height=260,
                            placeholder="From: ...\nSubject: ...\nBody...\n---\nFrom: ...")
        files = st.file_uploader("Or upload .eml files", type=["eml"], accept_multiple_files=True)
        submitted = st.form_submit_button("Sort my emails", type="primary")

    if submitted:
        emails = from_text(text) if text.strip() else []
        emails += [from_eml_bytes(f.getvalue())[:MAX_BODY_CHARS] for f in files or []]
        if not emails:
            st.warning("Paste some emails or upload .eml files first.")
            return
        if len(emails) > MAX_EMAILS:
            st.info(f"Found {len(emails)} emails; sorting the first {MAX_EMAILS}.")
        run_and_show(sort_emails, emails, spinner=f"Sorting {min(len(emails), MAX_EMAILS)} emails...",
                     filename="inbox_plan.md")
    st.caption("Your emails are sent to the Claude API. Leave out anything you wouldn't want to share.")
