# Share the agent with friends (a link + password)

This puts a chat-only version online, free, on Streamlit Community Cloud. Friends open
a link, type a password, and chat. No installing anything.

**What friends can use:** notes into actions, gift ideas, inbox clean-up, trip checks,
resume vs job matching, weekly planning, meeting costs, reading-list briefing, bank-export
explainer, content ideas, and the team-FAQ / ask-your-notes demos (on the example files).

**What stays on your own computer only:** Downloads and photo tidy-ups, your job tracker,
saved library, decision journal, dashboard and idea bank. The shared version can't see
anyone's computer, and it doesn't keep anyone's data. Friends attach files with the 📎 button.

## 1. Protect your API key (2 minutes)

Friends' messages use your Claude API key, so set a monthly limit first:

1. Go to https://console.anthropic.com → **Settings → Limits** (or **Billing**).
2. Set a monthly spend limit you're happy with, e.g. $10.
3. Optional but tidy: under **API Keys**, create a new key just for this, named
   "friends demo". You can delete it any time to switch the demo off instantly.

Each visitor can send 25 messages per visit (change with `AGENT_MAX_MESSAGES`).

## 2. Deploy (about 5 minutes)

1. Make sure the agent is merged into `main` on GitHub.
2. Go to https://share.streamlit.io and **sign in with GitHub**. Allow it to see the
   `ai-diy-projects` repository (it may ask about private repositories: say yes).
3. Click **Create app** → **Deploy a public app from GitHub** (the *app* is public, it is
   the password that keeps strangers out; your code stays private).
4. Fill in:
   - Repository: `nehakul2/ai-diy-projects`
   - Branch: `main`
   - Main file path: `agent_app.py`
   - App URL: pick something, e.g. `neha-assistant`
5. Open **Advanced settings**. Choose Python **3.12**, and paste this into **Secrets**,
   with your own key and a password you choose:

   ```toml
   ANTHROPIC_API_KEY = "sk-ant-..."
   AGENT_HOSTED = "1"
   AGENT_PASSWORD = "pick-a-password"
   AGENT_NAME = "Neha"
   ```

6. Click **Deploy**. The first start takes a few minutes. When the chat appears, try it.
7. Send friends the link (e.g. `https://neha-assistant.streamlit.app`) and the password.

## Changing things later

- **Update the app:** merge changes into `main`; it redeploys by itself.
- **Change the password or key:** share.streamlit.io → your app → ⋮ → **Settings → Secrets**.
- **Switch it off:** ⋮ → **Delete**, or delete the "friends demo" key in the Console.
- **See usage/cost:** https://console.anthropic.com → **Usage**.
- If nobody uses it for a while, it goes to sleep; the next visitor clicks
  "wake up" and waits about a minute.

## Getting feedback

The app doesn't collect feedback itself (it forgets each chat when the tab closes).
Ask friends to message you, or share a short Google Form link alongside the app link.
