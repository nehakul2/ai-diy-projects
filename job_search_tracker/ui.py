"""Test page for the job-search tracker."""
from pathlib import Path

import streamlit as st

from common.ui import pasted_key_for_call
from job_search_tracker import store
from job_search_tracker.tracker import add_role, details, table

TITLE = "Job-search tracker"
ORDER = 8

EXAMPLE = Path(__file__).parent / "examples" / "posting.txt"


def _add_tab() -> None:
    if st.button("Load the example posting"):
        st.session_state["jst_posting"] = EXAMPLE.read_text(encoding="utf-8")
    with st.form("jst_add"):
        posting = st.text_area("Job posting", key="jst_posting", height=220)
        col1, col2 = st.columns(2)
        url = col1.text_input("Link (optional)")
        deadline = col2.text_input("Deadline YYYY-MM-DD (optional, if not in the posting)")
        submitted = st.form_submit_button("Save role", type="primary")
    if submitted:
        if not posting.strip():
            st.warning("Paste a job posting first.")
            return
        try:
            with st.spinner("Reading the posting..."), pasted_key_for_call():
                job = add_role(posting, url.strip(), deadline.strip())
        except SystemExit as e:
            st.error(str(e.code))
            return
        except ValueError as e:
            st.warning(str(e))
            return
        st.success(f"Saved as id {job['id']}.")
        st.markdown(details(job))


def _role_tab(jobs: list[dict]) -> None:
    if not jobs:
        st.info("No roles yet.")
        return
    labels = {f"{j['id']}: {j['role']} at {j['company']}": j["id"] for j in jobs}
    job = store.get(labels[st.selectbox("Role", list(labels))])
    st.markdown(details(job))
    st.subheader("Update")
    for i, step in enumerate(job.get("checklist", [])):
        if st.checkbox(step["step"], value=step["done"], key=f"jst_step_{job['id']}_{i}") != step["done"]:
            store.toggle_step(job["id"], i)
            st.rerun()
    with st.form(f"jst_update_{job['id']}"):
        status = st.selectbox("Status", store.STATUSES, index=store.STATUSES.index(job["status"]))
        nxt = st.text_input("Next action", value=job.get("next_action", ""))
        nxt_date = st.text_input("Next action date (YYYY-MM-DD)", value=job.get("next_action_date", ""))
        notes = st.text_area("Notes", value=job.get("notes", ""))
        if st.form_submit_button("Save changes"):
            try:
                store.update(job["id"], status=status, next_action=nxt, next_action_date=nxt_date.strip(), notes=notes)
                st.success("Saved.")
                st.rerun()
            except ValueError as e:
                st.warning(str(e))


def render() -> None:
    st.header(TITLE)
    st.write("Save roles from job postings. Claude pulls out the key skills, deadline and an application "
             "checklist for each. You track status and next actions here.")
    jobs = store.load()
    tab_list, tab_add, tab_role = st.tabs(["My roles", "Add a role", "Role details"])
    with tab_list:
        show_all = st.checkbox("Include closed roles")
        st.markdown(table(jobs, show_all))
        st.caption(f"Saved on this computer in {store.jobs_file()}")
    with tab_add:
        _add_tab()
    with tab_role:
        _role_tab(jobs)
    st.caption("Tip: the Resume vs job matcher page can compare any saved posting with your resume.")
