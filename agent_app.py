"""The personal agent on its own: a single chat page, for sharing a link with friends.

Run locally (the full version, with every project):
    streamlit run agent_app.py

On a server that friends use, set AGENT_HOSTED=1 (see personal_agent/DEPLOY.md). That
switches off the tools that touch the server's folders or your personal data, asks for
AGENT_PASSWORD if you set one, and limits messages per visitor.
"""
import streamlit as st

st.set_page_config(page_title="AI assistant", page_icon="💬", layout="centered")

from common.ui import api_key_box  # noqa: E402 (set_page_config must come first)
from personal_agent.tools import HOSTED  # noqa: E402
from personal_agent.ui import render  # noqa: E402

if not HOSTED:  # on your own computer, allow pasting a key; a server uses its own secret
    with st.sidebar:
        api_key_box()
render()
