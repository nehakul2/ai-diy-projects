"""Test UI for every project in this repo.

Run from the repo root:
    streamlit run app.py

Each project adds a ui.py in its own folder with:
    TITLE = "Notes into actions"   # name shown in the sidebar
    ORDER = 1                      # position in the list
    def render() -> None: ...      # draws the page with streamlit
The app finds those files by itself, so nothing here needs editing.
"""
import importlib
from pathlib import Path

import streamlit as st

from common.ui import api_key_box

ROOT = Path(__file__).parent

st.set_page_config(page_title="AI DIY projects", page_icon="🛠️", layout="wide")


def find_projects() -> list:
    pages, broken = [], []
    for ui_file in sorted(ROOT.glob("*/ui.py")):
        name = ui_file.parent.name
        if name == "common":
            continue
        try:
            module = importlib.import_module(f"{name}.ui")
            pages.append(module)
        except Exception as e:  # one broken project shouldn't hide the others
            broken.append((name, e))
    pages.sort(key=lambda m: (getattr(m, "ORDER", 999), m.TITLE))
    return pages, broken


projects, broken = find_projects()

with st.sidebar:
    st.title("AI DIY projects")
    if not projects:
        st.warning("No projects with a ui.py found yet.")
        st.stop()
    by_label = {f"{getattr(m, 'ORDER', '')}. {m.TITLE}".lstrip(". "): m for m in projects}
    choice = by_label[st.radio("Project", list(by_label))]
    st.divider()
    api_key_box()
    for name, e in broken:
        st.error(f"Couldn't load {name}: {e}")

choice.render()
