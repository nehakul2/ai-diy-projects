"""Small helpers shared by every project's ui.py page."""
import os
from contextlib import contextmanager

import streamlit as st

_KEY = "pasted_api_key"


def api_key_box() -> None:
    """Sidebar box for the API key. A pasted key lives only in this browser tab's memory."""
    if os.environ.get("ANTHROPIC_API_KEY"):
        st.success("Using ANTHROPIC_API_KEY from your Terminal.")
        label = "Or paste a different key (optional)"
    else:
        st.info("No ANTHROPIC_API_KEY found. Paste a key below, or run `export ANTHROPIC_API_KEY=...` before launching.")
        label = "Claude API key"
    st.text_input(label, type="password", key=_KEY, placeholder="sk-ant-...",
                  help="Kept in memory for this tab only. Never written to disk.")
    model = os.environ.get("CLAUDE_MODEL", "claude-opus-5-5")
    st.caption(f"Model: `{model}`")


@contextmanager
def _pasted_key():
    """Use the pasted key (if any) for one call, then put the old value back."""
    pasted = (st.session_state.get(_KEY) or "").strip()
    if not pasted:
        yield
        return
    old = os.environ.get("ANTHROPIC_API_KEY")
    os.environ["ANTHROPIC_API_KEY"] = pasted
    try:
        yield
    finally:
        if old is None:
            os.environ.pop("ANTHROPIC_API_KEY", None)
        else:
            os.environ["ANTHROPIC_API_KEY"] = old


# Public name for pages that need the pasted key around their own call
# (for example, a page that keeps a plan in session state instead of using run_and_show).
pasted_key_for_call = _pasted_key


def run_and_show(fn, *args, spinner: str = "Asking Claude...", filename: str = "result.md", **kwargs) -> None:
    """Call a project function, show its Markdown result, and offer a download.

    The projects stop with a friendly message (sys.exit) on API errors; show that
    message on the page instead of crashing.
    """
    try:
        with st.spinner(spinner), _pasted_key():
            result = fn(*args, **kwargs)
    except SystemExit as e:
        st.error(str(e.code) if e.code else "The project stopped without a message.")
        return
    except Exception as e:
        st.error(f"Something went wrong: {type(e).__name__}: {e}")
        return
    st.markdown(result)
    st.download_button("Download as Markdown", result + "\n", file_name=filename, mime="text/markdown")
