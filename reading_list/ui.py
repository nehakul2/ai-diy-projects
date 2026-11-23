"""Test page for the reading list with a spoken summary."""
import json
import tempfile
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from common.ui import pasted_key_for_call
from reading_list.briefing import from_library, make_briefing, to_markdown

TITLE = "Reading list briefing"
ORDER = 12

EXAMPLE = Path(__file__).parent / "examples" / "links.txt"


def _browser_player(script: str) -> None:
    """Play / pause / stop buttons that use the browser's own voice (works in Chrome, Safari, Edge)."""
    page = f"""
<div style="font-family:sans-serif;display:flex;gap:8px;align-items:center">
  <button id="p">▶ Play</button><button id="z">⏸ Pause</button><button id="s">⏹ Stop</button>
  <label>Speed <select id="r"><option>0.9</option><option selected>1</option><option>1.2</option>
  <option>1.5</option></select></label><span id="m" style="color:#888"></span>
</div>
<script>
const text = {json.dumps(script).replace("</", "<\\/")};
const synth = window.speechSynthesis;
const m = document.getElementById('m');
if (!synth) {{ m.textContent = 'This browser has no built-in voice.'; }}
document.getElementById('p').onclick = () => {{
  if (synth.paused) {{ synth.resume(); return; }}
  synth.cancel();
  const u = new SpeechSynthesisUtterance(text);
  u.rate = parseFloat(document.getElementById('r').value);
  u.onend = () => m.textContent = '';
  m.textContent = 'Playing...';
  synth.speak(u);
}};
document.getElementById('z').onclick = () => synth.pause();
document.getElementById('s').onclick = () => {{ synth.cancel(); m.textContent = ''; }};
</script>"""
    if hasattr(st, "iframe"):
        st.iframe(page, height=50)
    else:  # older Streamlit
        components.html(page, height=50)


def _audio_file(script: str) -> None:
    try:
        from reading_list.speech import audio_suffix, speak
        out = Path(tempfile.gettempdir()) / f"reading-briefing{audio_suffix()}"
        with st.spinner("Making the audio file..."):
            speak(script, out)
    except ValueError as e:
        st.warning(str(e))
        return
    data = out.read_bytes()
    st.audio(data, format="audio/mp4" if out.suffix == ".m4a" else "audio/wav")
    st.download_button("Download audio", data, file_name=out.name)


def render() -> None:
    st.header(TITLE)
    st.write("Paste the links you've been meaning to read. Claude reads them, gives the key points and whether "
             "each is worth reading in full, and writes a short briefing you can listen to.")
    col1, col2 = st.columns(2)
    if col1.button("Load example links"):
        st.session_state["rl_text"] = EXAMPLE.read_text(encoding="utf-8")
    if col2.button("Use unread articles from my saved-content library"):
        try:
            st.session_state["rl_text"] = from_library()
        except ValueError as e:
            st.warning(str(e))
    with st.form("rl_form"):
        text = st.text_area("Links, one per line (or paste article text)", key="rl_text", height=180)
        minutes = st.slider("Briefing length (minutes)", 1, 10, 3)
        submitted = st.form_submit_button("Make my briefing", type="primary")
    if submitted:
        try:
            with st.spinner("Reading your list (this can take a minute or two)..."), pasted_key_for_call():
                st.session_state["rl_briefing"] = make_briefing(text, minutes)
        except SystemExit as e:
            st.error(str(e.code))
            return
        except ValueError as e:
            st.warning(str(e))
            return
    briefing = st.session_state.get("rl_briefing")
    if not briefing:
        return
    st.subheader("Listen")
    _browser_player(briefing["script"])
    if st.button("Make an audio file instead (uses this computer's voice)"):
        _audio_file(briefing["script"])
    md = to_markdown(briefing)
    st.markdown(md)
    st.download_button("Download as Markdown", md + "\n", file_name="reading_briefing.md")
