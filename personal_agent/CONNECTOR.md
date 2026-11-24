# Your agent inside Claude (a connector friends add)

Friends add your agent to **their own Claude app** (web, desktop or phone). They chat with
Claude as usual, and Claude uses your projects as tools: their own job tracker, reading
library, decision journal and idea bank, exact meeting-cost and calendar maths, and the
step-by-step "playbooks" from your projects (notes into actions, gift ideas, travel checks...).

**Nobody needs an API key.** Friends just need a Claude account. Claude's thinking happens on
their own Claude plan, and the server and database below are free.

**Optional: full project runs on your key, 10 per friend.** If you also give the server your
Claude API key, Claude can run a project exactly as you built it (with its own prompts and web
search) and show the full report. Each friend gets 10 of these runs (change `FRIEND_RUN_LIMIT`);
after that Claude does the job itself using the project's playbook, at no cost to you. A failed
run doesn't count. Set a monthly spend limit at console.anthropic.com (Settings → Limits) too.

**What it can't do:** tidy anyone's Downloads or photos (it can't see their computer).

You set up two free accounts once: **Supabase** (the database) and **Render** (runs the server).
About 15 minutes, no Terminal needed.

## 1. Database: Supabase (5 minutes)

1. Go to https://supabase.com and sign up (GitHub sign-in is fine).
2. **New project**. Name it `personal-agent`, make up a **database password** and save it somewhere,
   pick the region nearest you, Free plan. Wait a minute while it's created.
3. Click **Connect** (top of the project page). Under **Session pooler**, copy the **URI**. It looks like
   `postgresql://postgres.abcd:[YOUR-PASSWORD]@aws-0-eu-west-2.pooler.supabase.com:5432/postgres`
4. Replace `[YOUR-PASSWORD]` with your database password. That's your **DATABASE_URL**. Keep it private.

The server creates its two tables by itself the first time it runs.

## 2. Server: Render (5 minutes)

1. Go to https://render.com and **sign up with GitHub**. Allow it to see `ai-diy-projects`.
2. Click **New → Blueprint**, pick `nehakul2/ai-diy-projects`, branch `main`. Render reads
   `render.yaml` from the repo and sets everything up.
3. It asks for these values:
   - `DATABASE_URL`: the link from step 1.
   - `INVITE_CODE`: a secret word friends need in their link, e.g. `sunflower-42`. No spaces or slashes.
   - `ANTHROPIC_API_KEY`: your Claude API key, for the 10 full project runs per friend. Leave it empty
     to switch those runs off (everything else still works). Tip: make a separate key named
     "friends connector" in the Console, so you can delete it any time.
4. Click **Apply**. The first build takes a few minutes. When it says **Live**, open the service and
   copy its address, e.g. `https://personal-agent-ab12.onrender.com`. Opening it in a browser should say
   "Personal agent connector is running".

**Free plan note:** Render's free server sleeps after 15 minutes without use and takes about a minute to
wake. The first message after a break may fail; trying again works. For no sleeping, switch the service
to the **Starter** plan ($7/month) under Settings → Instance type.

## 3. Send friends their link

Each friend's link is your address + `/mcp/` + invite code + their name + a PIN **they choose**:

```
https://personal-agent-ab12.onrender.com/mcp/sunflower-42/asha/4821
```

- Name: lowercase letters, numbers or dashes (e.g. `asha` or `asha-k`).
- PIN: at least 4 characters. The first time a name is used, that PIN becomes theirs. Nobody else can
  use that name with a different PIN, so their data stays private.

Message to send friends (fill in the address and invite code):

> I built an AI assistant and I'd love your feedback! In Claude, go to **Settings → Connectors →
> Add custom connector**. Name it "Neha's agent" and paste this link, with your own name and a PIN
> you'll remember: `https://personal-agent-ab12.onrender.com/mcp/sunflower-42/YOURNAME/YOURPIN`
> Then start a new chat and try: "Save this job: (paste a posting)", "Gift ideas for my mum, £40,
> loves gardening", "Turn these notes into a to-do list: ...", "What do my meetings cost? (list them)".

(Custom connectors are in Claude's settings on the web and desktop apps. Some Claude plans limit how
many custom connectors you can add; if the option is missing, that's why.)

## Use it yourself

- Add your own link the same way (any name and PIN). It's separate from your Mac's files.
- Or in **Claude Desktop** on your Mac, using your normal local files: Claude menu → Settings →
  Developer → Edit Config, and add (with your own path to the repo):

  ```json
  {
    "mcpServers": {
      "personal-agent": {
        "command": "/Users/YOU/ai-diy-projects/.venv/bin/python",
        "args": ["-m", "personal_agent.mcp_server"],
        "env": {"PYTHONPATH": "/Users/YOU/ai-diy-projects"}
      }
    }
  }
  ```
  Tip: in Terminal, `cd ai-diy-projects && pwd` prints the path to use. Restart Claude Desktop after saving.

## Looking after it

- **See friends' data or reset a PIN:** Supabase → Table Editor. `agent_users` has one row per friend
  (delete a row to free the name so they can pick a new PIN; their data stays in `agent_data`).
- **Change the invite code, the run limit or the key:** Render → your service → Environment.
  Changing the invite code stops old links working.
- **See runs used:** Supabase → Table Editor → `agent_data`, rows named `usage`. Delete a row to give
  that friend their runs back.
- **Updates:** merge into `main` and Render redeploys by itself.
- **Switch it off:** Render → your service → Settings → Suspend.
