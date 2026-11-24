// Personal Helper web app. Talks only to the JSON API in personal_agent/web.py,
// the same API a phone app can use later.
(function () {
  const $ = (id) => document.getElementById(id);
  const TOKEN_KEY = "helper-token";
  const store = {
    get() { try { return localStorage.getItem(TOKEN_KEY) || ""; } catch { return ""; } },
    set(v) { try { v ? localStorage.setItem(TOKEN_KEY, v) : localStorage.removeItem(TOKEN_KEY); } catch {} },
  };
  let token = store.get();
  let busy = false;

  async function api(path, options = {}) {
    const headers = options.headers || {};
    if (token) headers.Authorization = `Bearer ${token}`;
    let body = options.body;
    if (body && !(body instanceof FormData)) { headers["Content-Type"] = "application/json"; body = JSON.stringify(body); }
    const res = await fetch(path, { method: options.method || (body ? "POST" : "GET"), headers, body });
    let data = {};
    try { data = await res.json(); } catch {}
    if (!res.ok) { const err = new Error(data.error || `Something went wrong (${res.status}).`); err.status = res.status; throw err; }
    return data;
  }

  // ---------- sign in ----------
  function showLogin(message) {
    $("app").hidden = true;
    $("login").hidden = false;
    const invite = new URLSearchParams(location.search).get("invite");
    if (invite) $("invite").value = invite;
    $("login-error").textContent = message || "";
    ($("invite").value ? $("name") : $("invite")).focus();
  }

  $("login-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const button = e.target.querySelector("button");
    button.disabled = true;
    $("login-error").textContent = "";
    try {
      const data = await api("/api/login", { body: { invite: $("invite").value.trim(), name: $("name").value, pin: $("pin").value } });
      token = data.token;
      store.set(token);
      $("pin").value = "";
      await start();
    } catch (err) {
      $("login-error").textContent = err.message;
    } finally {
      button.disabled = false;
    }
  });

  $("sign-out").addEventListener("click", () => { token = ""; store.set(""); location.reload(); });

  // ---------- chat ----------
  function setLeft(left, limit) {
    const pill = $("left");
    if (left === null || left === undefined) { pill.hidden = true; return; }
    pill.hidden = false;
    pill.textContent = `${left}/${limit} left`;
    pill.title = `${left} of ${limit} questions left`;
    if (left <= 0) {
      $("input").disabled = true;
      $("input").placeholder = "That's all the questions for this demo. Thank you!";
      $("send").disabled = true;
    }
  }

  function scrollDown() { $("messages").scrollTop = $("messages").scrollHeight; }

  function addMessage(kind, text, results) {
    $("welcome").hidden = true;
    const div = document.createElement("div");
    div.className = `msg ${kind}`;
    if (kind === "mine") {
      div.textContent = text;
    } else {
      div.innerHTML = window.renderMarkdown(text);
      for (const r of results || []) {
        const d = document.createElement("details");
        d.className = "result";
        const s = document.createElement("summary");
        s.textContent = `${r.ok ? "📎" : "⚠️"} ${r.label}`;
        const body = document.createElement("div");
        body.innerHTML = window.renderMarkdown(r.output);
        d.append(s, body);
        div.append(d);
      }
    }
    $("messages").append(div);
    scrollDown();
    return div;
  }

  function showConfirm(question) {
    $("confirm").hidden = !question;
    $("confirm-text").textContent = question || "";
  }

  async function answerConfirm(yes) {
    showConfirm(null);
    try {
      const data = await api("/api/confirm", { body: { yes } });
      addMessage("theirs", (yes ? "✅ " : "") + data.outcome);
    } catch (err) {
      addMessage("theirs problem", err.message);
    }
  }
  $("confirm-yes").addEventListener("click", () => answerConfirm(true));
  $("confirm-no").addEventListener("click", () => answerConfirm(false));

  async function send(text) {
    text = text.trim();
    const file = $("file").files[0];
    if (!text && !file) return;
    if (busy) return;
    if (!text) text = "Please look at this file.";
    busy = true;
    $("send").disabled = true;
    addMessage("mine", file ? `${text}\n📎 ${file.name}` : text);
    $("input").value = "";
    autosize();
    const waiting = addMessage("theirs", "");
    waiting.innerHTML = '<span class="typing">Working on it (this can take up to a minute)</span>';
    let body;
    if (file) { body = new FormData(); body.append("message", text); body.append("file", file); }
    else body = { message: text };
    clearFile();
    try {
      const data = await api("/api/chat", { body });
      waiting.remove();
      addMessage("theirs", data.reply || "(No reply.)", data.results);
      showConfirm(data.pending);
      if (data.left !== undefined) setLeft(data.left, window.__limit);
    } catch (err) {
      waiting.remove();
      if (err.status === 401) { showLogin("Please sign in again."); return; }
      addMessage("theirs problem", err.message);
    } finally {
      busy = false;
      $("send").disabled = $("input").disabled;
      $("input").focus();
    }
  }

  $("composer").addEventListener("submit", (e) => { e.preventDefault(); send($("input").value); });
  $("input").addEventListener("keydown", (e) => {
    // Enter sends on a computer; on phones the keyboard's return adds a new line.
    if (e.key === "Enter" && !e.shiftKey && !("ontouchstart" in window)) { e.preventDefault(); send($("input").value); }
  });
  function autosize() { const t = $("input"); t.style.height = "auto"; t.style.height = Math.min(t.scrollHeight, 160) + "px"; }
  $("input").addEventListener("input", autosize);

  function clearFile() { $("file").value = ""; $("attachment").hidden = true; }
  $("file").addEventListener("change", () => {
    const f = $("file").files[0];
    $("attachment").hidden = !f;
    $("attachment-name").textContent = f ? `📎 ${f.name}` : "";
  });
  $("attachment-clear").addEventListener("click", clearFile);

  $("new-chat").addEventListener("click", async () => {
    try { await api("/api/new", { body: {} }); } catch {}
    document.querySelectorAll(".msg").forEach((m) => m.remove());
    showConfirm(null);
    $("welcome").hidden = false;
  });

  async function start() {
    let me;
    try {
      me = await api("/api/me");
    } catch (err) {
      if (err.status === 401) return showLogin();
      return showLogin(err.message);
    }
    $("login").hidden = true;
    $("app").hidden = false;
    $("sign-out").hidden = !me.hosted;
    const title = me.owner ? `${me.owner}'s Helper` : "Personal Helper";
    $("app-title").textContent = title;
    document.title = title;
    $("hello").textContent = me.hosted ? `Hi ${me.name}! What can I help with?` : "Hi! What can I help with?";
    window.__limit = me.limit;
    setLeft(me.left, me.limit);
    const chips = $("examples");
    chips.innerHTML = "";
    for (const ex of me.examples || []) {
      const b = document.createElement("button");
      b.className = "chip";
      b.type = "button";
      b.textContent = ex;
      b.addEventListener("click", () => send(ex));
      chips.append(b);
    }
    $("input").focus();
  }

  if ("serviceWorker" in navigator) navigator.serviceWorker.register("/sw.js").catch(() => {});
  start();
})();
