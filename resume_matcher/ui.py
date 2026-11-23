"""Test page for the resume vs job description matcher."""
from pathlib import Path

import streamlit as st

from common.ui import run_and_show
from resume_matcher.main import match_resume, resume_block

TITLE = "Resume vs job matcher"
ORDER = 6

EXAMPLES = Path(__file__).parent / "examples"


def render() -> None:
    st.header(TITLE)
    st.write(
        "Upload your resume and paste a job description. Claude shows your three strongest matches "
        "with quotes from your resume as evidence, the gaps, and specific tweaks. It never invents experience."
    )

    if st.button("Load the example resume and job"):
        st.session_state["rm_resume_text"] = (EXAMPLES / "resume.txt").read_text(encoding="utf-8")
        st.session_state["rm_job"] = (EXAMPLES / "job.txt").read_text(encoding="utf-8")

    with st.form("resume_form"):
        upload = st.file_uploader("Resume (PDF or text)", type=["pdf", "txt", "md"])
        resume_text = st.text_area("Or paste your resume", key="rm_resume_text", height=180)
        job = st.text_area("Job description", key="rm_job", height=220)
        submitted = st.form_submit_button("Compare", type="primary")

    if submitted:
        try:
            if upload is not None:
                block = resume_block(upload.getvalue(), upload.name)
            else:
                block = resume_block(resume_text.encode(), "resume.txt")
        except ValueError as e:
            st.warning(str(e))
            return
        if not job.strip():
            st.warning("Paste the job description.")
            return
        run_and_show(match_resume, block, job,
                     spinner="Comparing your resume with the job (this can take a minute)...",
                     filename="resume_match.md")
    st.caption("Your resume is sent to the Claude API to be compared.")
