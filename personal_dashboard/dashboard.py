"""Build the dashboard, save it as a web page and JSON, and render it as Markdown."""
import json
from datetime import datetime
from html import escape
from pathlib import Path

from personal_dashboard.cards import data_dir, local_cards, web_briefing

TITLES = {"calendar": "📅 Calendar", "jobs": "💼 Job search", "decisions": "🧭 Decisions to review",
          "reading": "📚 Reading"}


def build(cfg: dict, use_web: bool = True) -> dict:
    local = local_cards(cfg)
    web = web_briefing(cfg, local) if use_web else None
    return {"generated": datetime.now().isoformat(timespec="minutes"), "name": cfg.get("name", ""),
            "location": cfg.get("location", ""), "local": local, "web": web}


def latest_file() -> Path:
    return data_dir() / "dashboard-latest.json"


def html_file() -> Path:
    return data_dir() / "dashboard.html"


def load_latest() -> dict | None:
    p = latest_file()
    try:
        return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else None
    except json.JSONDecodeError:
        return None


def save(data: dict, refresh_minutes: int = 30) -> Path:
    """Write dashboard-latest.json and dashboard.html. The page reloads itself in an open browser tab."""
    d = data_dir()
    d.mkdir(parents=True, exist_ok=True)
    if data["web"] is None and (old := load_latest()) and old.get("web"):
        data = dict(data, web=old["web"], web_generated=old.get("web_generated", old["generated"]))
    elif data["web"] is not None:
        data = dict(data, web_generated=data["generated"])
    for path, text in ((latest_file(), json.dumps(data, indent=2)), (html_file(), to_html(data, refresh_minutes))):
        tmp = path.with_suffix(".tmp")
        tmp.write_text(text, encoding="utf-8")
        tmp.replace(path)
    return html_file()


def _when(data: dict) -> str:
    t = datetime.fromisoformat(data["generated"])
    s = f"Updated {t:%a %d %b, %H:%M}"
    if data.get("web_generated") and data["web_generated"] != data["generated"]:
        s += f" (web part from {datetime.fromisoformat(data['web_generated']):%a %H:%M})"
    return s


def greeting(data: dict) -> str:
    h = datetime.fromisoformat(data["generated"]).hour
    part = "morning" if h < 12 else "afternoon" if h < 18 else "evening"
    return f"Good {part}" + (f", {data['name']}" if data.get("name") else "")


def to_markdown(data: dict) -> str:
    lines = [f"## {greeting(data)}", f"_{_when(data)}_", ""]
    web = data.get("web")
    if web:
        lines += [f"**Focus:** {web['focus']}", ""]
        w = web["weather"]
        lines += [f"### ☀️ Weather{' in ' + data['location'] if data.get('location') else ''}",
                  f"{w['summary']} High {w['high']}, low {w['low']}." + (f" {w['tip']}" if w["tip"] else ""), ""]
    for name, items in data["local"].items():
        lines += [f"### {TITLES.get(name, name)}"] + [f"- {i}" for i in items] + [""]
    if web:
        for t in web["topics"]:
            lines.append(f"### 📰 {t['topic']}")
            lines += [f"- {_md_link(i['url'], i['headline'])}: {i['why']}" for i in t["items"]] or ["- Nothing new."]
            lines.append("")
        if web["answers"]:
            lines.append("### ❓ Your questions")
            lines += [f"- **{a['question']}** {a['answer']} ({_md_link(a['url'], 'source')})" for a in web["answers"]]
    return "\n".join(lines).strip()


def _md_link(url: str, text: str) -> str:
    return f"[{text}]({url})" if url.startswith(("https://", "http://")) else text


def _link(url: str, text: str) -> str:
    if url.startswith(("https://", "http://")):
        return f'<a href="{escape(url)}" target="_blank" rel="noopener">{escape(text)}</a>'
    return escape(text)


def to_html(data: dict, refresh_minutes: int = 30) -> str:
    cards = []
    web = data.get("web")
    if web:
        w = web["weather"]
        cards.append(("☀️ Weather", [f"<b>{escape(w['high'])} / {escape(w['low'])}</b> · {escape(w['summary'])}"]
                      + ([escape(w["tip"])] if w["tip"] else [])))
    for name, items in data["local"].items():
        cards.append((TITLES.get(name, name), [escape(i) for i in items]))
    if web:
        for t in web["topics"]:
            cards.append((f"📰 {t['topic']}", [f"{_link(i['url'], i['headline'])}<br><small>{escape(i['why'])}</small>"
                                              for i in t["items"]] or ["Nothing new."]))
        if web["answers"]:
            cards.append(("❓ Your questions", [f"<b>{escape(a['question'])}</b><br>{escape(a['answer'])} "
                                               f"{_link(a['url'], '(source)')}" for a in web["answers"]]))
    body = "\n".join(f'<section><h2>{escape(title)}</h2><ul>{"".join(f"<li>{i}</li>" for i in items)}</ul></section>'
                     for title, items in cards)
    focus = f'<p class="focus">{escape(web["focus"])}</p>' if web else ""
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="refresh" content="{refresh_minutes * 60}"><title>My dashboard</title>
<style>
:root {{ --bg:#f6f5f2; --card:#fff; --text:#1d1d1f; --muted:#6b6b70; --accent:#2f6fdf; }}
@media (prefers-color-scheme: dark) {{ :root {{ --bg:#141416; --card:#1f1f23; --text:#ececef; --muted:#9a9aa2;
  --accent:#7aa7ff; }} }}
body {{ margin:0; padding:24px 16px; background:var(--bg); color:var(--text);
  font:15px/1.5 -apple-system, "Segoe UI", Roboto, sans-serif; }}
main {{ max-width:1100px; margin:0 auto; }}
h1 {{ margin:0; font-size:26px; }} .when {{ color:var(--muted); margin:4px 0 16px; }}
.focus {{ background:var(--card); border-left:4px solid var(--accent); padding:12px 16px; border-radius:8px; }}
.grid {{ display:grid; gap:16px; grid-template-columns:repeat(auto-fill, minmax(300px, 1fr)); }}
section {{ background:var(--card); border-radius:12px; padding:16px; box-shadow:0 1px 3px rgba(0,0,0,.08); }}
h2 {{ font-size:16px; margin:0 0 8px; }} ul {{ margin:0; padding-left:18px; }} li {{ margin:6px 0; }}
a {{ color:var(--accent); }} small {{ color:var(--muted); }}
</style></head>
<body><main><h1>{escape(greeting(data))}</h1><p class="when">{escape(_when(data))}</p>{focus}
<div class="grid">{body}</div></main></body></html>
"""
