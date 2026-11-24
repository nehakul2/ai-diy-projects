# Put the Personal Helper online for friends

This puts your agent online as its own app: a link friends open on their phone or computer.
They sign in with a name and PIN, can ask **10 questions each** (you choose the number), and
their job tracker, saved library, decision journal and idea bank are kept just for them.
It runs on **your** Claude API key, so friends need nothing.

On a phone, friends can add it to the home screen (Share → Add to Home Screen on iPhone,
⋮ → Add to Home screen / Install app on Android) and it opens like an app.

Two free accounts, about 15 minutes, no Terminal.

## 1. Protect your API key (2 minutes)

1. Go to https://console.anthropic.com → **API Keys** → **Create key**. Name it "helper app".
   (Deleting this key later switches the app off instantly, without touching your own key.)
2. **Settings → Limits**: set a monthly spend limit you're comfortable with, e.g. $10.

Roughly: one question costs a few cents; ones that search the web (gifts, trips) cost more.
10 friends × 10 questions is usually a few dollars.

## 2. Database: Supabase (5 minutes)

1. Go to https://supabase.com and sign up (GitHub sign-in is fine).
2. **New project**. Name `personal-helper`, make up a **database password** (save it), pick the
   region nearest you, Free plan. Wait a minute while it's created.
3. Click **Connect** at the top. Under **Session pooler**, copy the **URI**. It looks like
   `postgresql://postgres.abcd:[YOUR-PASSWORD]@aws-0-eu-west-2.pooler.supabase.com:5432/postgres`
4. Replace `[YOUR-PASSWORD]` with your database password. That's your **DATABASE_URL**.

The app creates its tables by itself. (Free Supabase projects pause after a week with no use;
Supabase emails you and one click wakes it up.)

## 3. App: Render (5 minutes)

1. Go to https://render.com and **sign up with GitHub**. Let it see `ai-diy-projects`.
2. **New → Blueprint** → pick `nehakul2/ai-diy-projects`, branch `main`. Render reads `render.yaml`.
3. Fill in the values it asks for:
   - `ANTHROPIC_API_KEY`: the "helper app" key from step 1
   - `DATABASE_URL`: from step 2
   - `INVITE_CODE`: a word friends need to get in, e.g. `sunflower42` (no spaces)
   - `AGENT_NAME`: `Neha` (the app is called "Neha's Helper")
   - `UNLIMITED_USERS`: the name you'll sign in with yourself, e.g. `neha`, so your own questions
     aren't limited (leave empty if you don't mind the limit)
4. Click **Apply**. The first build takes a few minutes. When it says **Live**, copy the address,
   e.g. `https://personal-helper-ab12.onrender.com`, and open it to try it.

**Free plan note:** the free server sleeps after 15 minutes unused, so the first visit after a
break takes about a minute to load. To avoid that, switch to **Starter** ($7/month) in the
service's **Settings → Instance type**.

## 4. Invite friends

Send the address with the invite code on the end, so it's filled in for them:

> I built an AI helper and I'd love your feedback! Open
> https://personal-helper-ab12.onrender.com/?invite=sunflower42
> pick a name and a PIN, and try things like gift ideas, checking a trip, turning notes into a
> to-do list, or pasting a job ad to track it. You get 10 questions. Tell me what worked and what didn't!

## Looking after it

- **Change the limit, invite code or key:** Render → your service → **Environment**. It restarts by itself.
- **Give someone more questions:** Supabase → **Table Editor** → `agent_data` → delete their row
  named `usage` (resets them to 0 used).
- **Someone forgot their PIN:** Supabase → `agent_users` → delete their row. They sign in again with
  a new PIN; their saved data is still there.
- **See costs:** console.anthropic.com → **Usage**.
- **Updates:** merge into `main` and Render redeploys by itself.
- **Switch it off:** Render → your service → **Settings → Suspend**, or delete the "helper app" key.

## What friends can and can't do

They can: notes into actions, gift ideas, inbox clean-up (paste or attach emails), trip checks,
resume vs job (attach a resume), weekly planning (attach a calendar .ics), meeting costs, reading-list
briefings, bank-statement explainer (attach a CSV), content ideas, and their own job tracker,
library, decision journal and idea bank.

They can't: tidy folders or sort photos (the app can't see their computer), or use your dashboard.
Attached files are kept only on the server's temporary disk and are cleared when it restarts.

## Later: a phone app

The web page only talks to the app's API (`/api/login`, `/api/me`, `/api/chat`, `/api/new`;
see the top of `personal_agent/web.py`). A phone app can use exactly the same API and accounts.
