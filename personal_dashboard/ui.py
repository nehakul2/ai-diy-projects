"""Test page for the self-updating personal dashboard."""
import streamlit as st

from common.ui import pasted_key_for_call
from personal_dashboard.cards import LOCAL_CARDS, data_dir, load_config, save_config
from personal_dashboard.dashboard import build, html_file, load_latest, save, to_markdown

TITLE = "Personal dashboard"
ORDER = 15


def _settings(cfg: dict) -> None:
    with st.expander("Settings", expanded=not (data_dir() / "dashboard.json").exists()):
        with st.form("pd_settings"):
            name = st.text_input("Your name (for the greeting)", cfg["name"])
            location = st.text_input("Location (for the weather)", cfg["location"])
            topics = st.text_area("Topics to follow, one per line (up to 6)", "\n".join(cfg["topics"]))
            questions = st.text_area("Questions to check each time, one per line (up to 5)",
                                     "\n".join(cfg["questions"]))
            calendar = st.text_input("Calendar export (.ics) file path (optional)", cfg["calendar"])
            include = st.multiselect("Cards from your other projects", LOCAL_CARDS,
                                     [c for c in cfg["include"] if c in LOCAL_CARDS])
            if st.form_submit_button("Save settings"):
                new = {"name": name.strip(), "location": location.strip(),
                       "topics": [t.strip() for t in topics.splitlines() if t.strip()],
                       "questions": [q.strip() for q in questions.splitlines() if q.strip()],
                       "calendar": calendar.strip(), "include": include}
                if len(new["topics"]) > 6 or len(new["questions"]) > 5:
                    st.warning("Keep it to 6 topics and 5 questions at most.")
                else:
                    st.success(f"Saved to {save_config(new)}")
                    st.rerun()


def render() -> None:
    st.header(TITLE)
    st.write("Weather, news on your topics and answers to your questions (found by Claude with web search), "
             "next to your calendar, job follow-ups, decisions to review and reading list from your other "
             "projects. It's saved as a web page that keeps itself up to date while the command runs.")
    try:
        cfg = load_config()
    except ValueError as e:
        st.error(str(e))
        return
    _settings(cfg)
    c1, c2 = st.columns(2)
    full = c1.button("Update now", type="primary")
    local = c2.button("Update my own data only (no API call)")
    if full or local:
        try:
            with st.spinner("Checking the weather and news (this can take a minute)..." if full else "Updating..."), \
                    pasted_key_for_call():
                save(build(cfg, use_web=full))
        except SystemExit as e:
            st.error(str(e.code))
        except ValueError as e:
            st.warning(str(e))
    data = load_latest()
    if not data:
        st.info("No dashboard yet. Press Update now.")
        return
    st.markdown(to_markdown(data))
    if html_file().exists():
        st.download_button("Download the dashboard page", html_file().read_bytes(), file_name="dashboard.html",
                           mime="text/html")
        st.caption(f"Saved at {html_file()}. To keep it updated, run "
                   "`python -m personal_dashboard.main --watch 60 --open` (see the README).")
