# Proof of Demand: Build Plan for Member B (Web App + Payments)

**You own:** `web/` (Next.js app, founder dashboard, signup widget, public report and badge, Dodo Payments, viaSocket, launch).
**Teammate (Member A) owns:** `backend/` (Python API, voice and AI scoring, fraud checks, TigerGraph).
**Build window:** Thu 29 Oct and Fri 30 Oct. Sat 31 Oct morning is fixes and final submission only (closes 9:59 AM).

> Sections 0.1 to 0.7 are **identical in both plans**. Your own stages start at section 1.

---

## 0. Shared rules (identical in both plans)

### 0.1 Ownership

| Area | Owner | Notes |
|---|---|---|
| `backend/` | A | Never edited by B |
| `web/` | B | Never edited by A |
| `contracts/` | Shared | Only **add** new files with your prefix (`a_` / `b_`). Never edit a file the other person created without asking first. |
| Root `README.md`, root `CLAUDE.md`, `.claude/settings.json`, `.claude/commands/`, `docs/` | A creates in Stage 0 | After that, edit only after pinging your teammate |
| `.claude/settings.local.json` | Each member, on their own laptop | Personal, never committed |
| Supabase project, Vercel, Dodo, viaSocket | B | B shares keys privately |
| Render (backend hosting), AI Grants, Sarvam, TigerGraph | A | A shares keys privately |

Because each person only touches their own folder, merge conflicts can't happen. This is what makes two people pushing to one repo seamless.

### 0.2 Repo layout

```
proof-of-demand/
├── README.md                  # what it is, how to run, live links (A creates, both update later)
├── CLAUDE.md                  # shared rules for Claude Code (A creates)
├── .gitignore                 # .env, node_modules, __pycache__, .venv, *.wav, *.webm
├── .claude/
│   ├── settings.json          # shared Claude Code permissions (A creates, section 0.7)
│   ├── settings.local.json    # PERSONAL, not committed: blocks editing the other folder
│   └── commands/              # /stage, /sync, /ship (A creates, section 0.7)
├── docs/
│   ├── PLAN_A_backend_ml.md   # this plan, so /stage can read it
│   └── PLAN_B_web_payments.md
├── contracts/
│   ├── api.md                 # backend endpoints (section 0.4) — A
│   ├── scoring.md             # verdicts, flags, funnel definitions (section 0.4) — A
│   ├── events.md              # signup.scored event (section 0.4) — A
│   ├── env.example            # all environment variable names, no values (section 0.5)
│   └── migrations/
│       ├── 001_init.sql       # created together in Stage 0
│       ├── a_002_voice_match.sql
│       ├── b_002_policies.sql
│       └── b_003_funnel_view.sql
├── backend/                   # Member A
│   ├── CLAUDE.md
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app/ ...
│   └── tests/ ...
└── web/                       # Member B
    ├── CLAUDE.md
    └── ... (Next.js app)
```

### 0.3 Git workflow

- **One repo on GitHub, both added as collaborators.** Work directly on `main`. Folder ownership prevents conflicts, so branches and pull requests just slow you down. Use a branch only for a risky experiment.
- **Before every push:**
  ```bash
  git add <your folder or file>
  git commit -m "A: short description"   # B uses "B: ..."
  git pull --rebase origin main
  git push origin main
  ```
- **Commit after every finished stage** at minimum. Small commits are easier to undo.
- **Never `git add .` from the repo root** without checking `git status`. You should only see your own folder and your own `contracts/` files.
- **Never commit secrets.** `.env` files are gitignored. When you add a new variable, add its **name** to `contracts/env.example` and tell your teammate.
- **Database changes** are new migration files only (`a_003_...sql`, `b_003_...sql`). Whoever writes a migration runs it in the Supabase SQL editor and posts "ran a_003" in your team chat.
- **Auto-deploys:** Vercel deploys `web/` on push to `main` (root directory = `web`). Render deploys `backend/` on push to `main` (root directory = `backend`). A push that only changes one folder still triggers both. That's harmless.

**Root `CLAUDE.md` (A creates in Stage 0, copy as-is):**

```markdown
# Proof of Demand: rules for Claude

- Monorepo: backend/ (Member A, Python FastAPI), web/ (Member B, Next.js), contracts/ (shared).
- Only edit the folder that belongs to the person running this session (see the folder's CLAUDE.md).
  Never edit the other member's folder.
- contracts/: only ADD new files with your prefix (a_ or b_). Never edit existing migration files.
- The API, scoring and event definitions in contracts/ are the source of truth. If code and contract
  disagree, stop and ask instead of changing the contract.
- Never commit secrets. Use .env (gitignored). Add new variable NAMES to contracts/env.example.
- Before finishing a task: run the folder's tests, then `git pull --rebase origin main`.
- Commit messages start with "A" or "B" (e.g. "A4: pain scoring").
- Our plans are in docs/. Use /stage, /sync and /ship (in .claude/commands/) for every stage.

## Contracts (always loaded)
@contracts/api.md
@contracts/scoring.md
@contracts/events.md
```

### 0.4 Contracts (agree in Stage 0, then treat as frozen)

#### Database: `contracts/migrations/001_init.sql`

```sql
create extension if not exists vector;
create extension if not exists pgcrypto;

create table waitlists (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null references auth.users(id),
  slug text unique not null,
  product_name text not null,
  product_description text,          -- used by the AI pain scorer as context
  question text not null,            -- the voice question shown to signups
  deposit_enabled boolean not null default false,
  deposit_amount_cents int not null default 100,
  deposit_currency text not null default 'USD',
  created_at timestamptz not null default now()
);

create table signups (
  id uuid primary key default gen_random_uuid(),
  waitlist_id uuid not null references waitlists(id) on delete cascade,
  email text not null,
  consent boolean not null default false,
  audio_path text,                   -- path in Supabase Storage bucket "audio"
  device_id text,                    -- FingerprintJS visitor id from the widget
  ip_hash text,                      -- salted hash, never the raw IP
  user_agent text,
  -- written by A (backend)
  status text not null default 'pending',      -- pending | processing | scored | failed
  transcript text,
  language text,
  pain_score int,                    -- 0-100
  pain_reason text,
  pain_quote text,
  human_verdict text,                -- verified | suspicious | fake | unverified
  flags jsonb not null default '[]'::jsonb,
  trust_score int,                   -- 0-100
  voice_embedding vector(192),
  -- written by B (web, from Dodo webhook)
  deposit_status text not null default 'none',  -- none | pending | paid | refunded
  deposit_payment_id text,
  created_at timestamptz not null default now(),
  unique (waitlist_id, email)
);

create index on signups (waitlist_id, created_at desc);
create index on signups (waitlist_id, device_id);
create index on signups (waitlist_id, ip_hash);
```

Storage: private bucket named `audio`. Row-level security (who can read which rows) is set by B. The backend uses the Supabase service key, which bypasses it.

#### Backend API: `contracts/api.md`

Base URL: `BACKEND_URL` (Render).

**`POST /v1/signups`** (multipart form, called by the widget)

| Field | Type | Required |
|---|---|---|
| `waitlist_slug` | text | yes |
| `email` | text | yes |
| `consent` | `"true"` | yes |
| `device_id` | text (FingerprintJS visitor id) | yes |
| `audio` | file: webm / ogg / mp4 / wav, ≤ 30 s, ≤ 3 MB | no (no audio → `human_verdict = unverified`) |

Responses:
- `201 {"signup_id": "...", "status": "pending"}`, with scoring running in the background (usually under 15 s)
- `400 {"error": "invalid_email" | "no_consent" | "bad_audio"}`
- `404 {"error": "waitlist_not_found"}`
- `409 {"error": "already_signed_up", "signup_id": "..."}`
- `429 {"error": "rate_limited"}` (more than 10 signups per IP per hour per waitlist)

**`GET /v1/signups/{id}/status`** → `{"status", "human_verdict", "pain_score"}`. The widget may poll this to show "You're verified ✓".

**`GET /health`** → `{"ok": true, "models_loaded": true}`

CORS: allow only `WEB_ORIGIN`. The widget runs inside an iframe on B's domain, so founders' sites never call the backend directly.

#### Scoring: `contracts/scoring.md`

- `human_verdict`
  - `verified`: trust_score ≥ 70
  - `suspicious`: 40–69
  - `fake`: < 40
  - `unverified`: no voice answer given, or scoring failed (`processing_error`); `trust_score` is null
- `pain_score` 0–100. Levels: **high** ≥ 70, **medium** 40–69, **low** < 40.
- `flags` is a JSON list of objects `{"code": "...", "detail": "..."}`. Codes:

| Code | Meaning (B shows this text in the UI) |
|---|---|
| `disposable_email` | Uses a throwaway email address |
| `repeat_device` | Same device already signed up to this waitlist |
| `repeat_ip` | Many signups from the same network |
| `same_voice` | Voice matches another signup (`detail` = that signup id) |
| `possible_ai_voice` | Voice may be AI-generated (reserved, **not produced in this build**; see A9) |
| `no_speech` | Recording has no clear speech |
| `too_short` | Answer under 3 seconds |
| `ring_member` | Part of a connected group of suspicious signups |
| `processing_error` | Scoring failed; will show as unverified |

- **Funnel** (dashboard, public report and badge all use these):
  1. **Signups**: all rows
  2. **Real humans**: `human_verdict = 'verified'`
  3. **Specific pain**: real humans with `pain_score >= 70`
  4. **Paid**: `deposit_status = 'paid'`

#### Event: `contracts/events.md`

When a signup reaches `scored`, the backend sends `POST NOTIFY_WEBHOOK_URL` (a viaSocket webhook set up by B), only if the variable is set:

```json
{
  "type": "signup.scored",
  "waitlist_slug": "acme",
  "signup_id": "uuid",
  "email_masked": "ra***@gmail.com",
  "human_verdict": "verified",
  "pain_score": 82,
  "pain_quote": "I lost three hours reconciling invoices last Tuesday",
  "trust_score": 88,
  "created_at": "2026-10-29T12:00:00Z"
}
```

### 0.5 Environment variables: `contracts/env.example`

```bash
# ---- backend (A) ----
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
WEB_ORIGIN=                    # e.g. https://proofofdemand.vercel.app
IP_HASH_SALT=                  # any long random string
STT_PROVIDER=sarvam            # sarvam | openai
SARVAM_API_KEY=
OPENAI_API_KEY=                # AI Grants India credits
LLM_MODEL=                     # a small, fast OpenAI chat model
VOICE_MATCH_THRESHOLD=0.6      # set after calibration in stage A5
NOTIFY_WEBHOOK_URL=            # viaSocket webhook from B (optional)
TG_HOST=                       # TigerGraph Savanna (optional, Day 2)
TG_GRAPH=pod
TG_SECRET=

# ---- web (B) ----
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=     # server-side only (webhooks, public report)
NEXT_PUBLIC_BACKEND_URL=
NEXT_PUBLIC_SITE_URL=
DODO_API_KEY=
DODO_WEBHOOK_SECRET=
DODO_DEPOSIT_PRODUCT_ID=
```

### 0.6 Timeline and sync points

| When | A | B | Together |
|---|---|---|---|
| **Thu 09:00–10:00** | Stage 0 | Stage 0 | Agree contracts, create accounts, share keys |
| Thu 10:00–13:00 | A1–A3 | B1–B3 | |
| **Thu 13:00 Sync 1 (15 min)** | | | Widget sends a real signup to the deployed backend; row appears in Supabase |
| Thu 14:00–18:00 | A4–A6 | B3–B5 | |
| **Thu 18:00 Sync 2 (20 min)** | | | Full flow on live URLs: record → scored → dashboard updates live |
| Thu 18:00–21:00 (open evening) | Help onboard | Lead onboarding | Get the first 3–5 teams' founders to create waitlists |
| Thu 21:00 | | | **Headcount (mandatory)** |
| Thu 21:30–00:30 | A7 | B6 | Prepare launch posts for Friday morning |
| **Fri 08:00 Sync 3** | | | Bug list from overnight real usage; decide what ships |
| Fri 08:00–11:00 | A8 | B7–B8 | |
| **Fri ~11:00** | | | **Phase 1: submit live product + launch on socials** (House of NGMI creators help in the morning) |
| Fri 11:00–21:00 | A10 | B9 | Onboard users, fix what real users hit |
| Fri 21:00 | | | **Headcount** |
| **Fri 23:00** | | | **Code freeze**: only bug fixes after this |
| Sat before 09:59 | | | Final submission (no extensions) |

### 0.7 Claude Code setup (both members, Opus on Claude Pro)

Both of you build with Claude Code. Three layers keep the two sessions from stepping on each other:
1. **`CLAUDE.md`**: tells Claude the rules.
2. **Permission settings**: actually *block* Claude's file-editing tools from touching the other person's folder.
3. **Shared commands**: make every stage start, check and push the same way.

#### Shared files (A commits these in Stage 0)

**`.claude/settings.json`**: shared permissions for both members.

```json
{
  "permissions": {
    "deny": [
      "Read(./**/.env)",
      "Read(./**/.env.*)",
      "Bash(git push --force *)",
      "Bash(git push -f *)",
      "Bash(git reset --hard *)"
    ],
    "allow": [
      "Bash(git status)",
      "Bash(git diff *)",
      "Bash(git log *)",
      "Bash(git add *)",
      "Bash(git commit *)",
      "Bash(git pull --rebase *)",
      "Bash(pytest *)",
      "Bash(npm run *)"
    ]
  }
}
```

Effects:
- Claude can't read your `.env` files, so secrets never land in the chat. Tell it variable names, never values.
- Claude can't force-push or hard-reset.
- Routine git and test commands run without asking.
- `git push` still asks you every time, so you always see what's going out.

**`.claude/commands/stage.md`** → `/stage A4`

```markdown
---
description: Build one stage from our plan, e.g. /stage A4 or /stage B3
---
Build stage $ARGUMENTS.

1. The letter says whose plan: A → docs/PLAN_A_backend_ml.md, B → docs/PLAN_B_web_payments.md.
   Read section 0 and stage "$ARGUMENTS" of that file. Ignore other stages.
2. Only edit that member's folder (A → backend/, B → web/) and NEW contracts/ files with that prefix.
3. First reply with a short plan (files to create or change, how you'll test it) and wait for my OK.
4. Build it. Write tests or a check command that proves the stage's "Output", and run them.
5. Finish with: what was built, how it was checked, anything I must do by hand
   (keys, running SQL in Supabase, dashboard settings, deploy settings), and a suggested commit message.
```

**`.claude/commands/sync.md`** → `/sync`

```markdown
---
description: Safely get my teammate's latest changes
---
1. Run `git status`. If there are uncommitted changes outside my own folder, stop and tell me.
2. Run `git pull --rebase origin main`.
3. Run `git log --oneline -10` and summarize what my teammate changed, especially anything in contracts/.
4. If contracts/ changed, list what in my folder may need updating. Don't change anything yet.
```

**`.claude/commands/ship.md`** → `/ship A4`

```markdown
---
description: Check, commit and push a finished stage, e.g. /ship A4
---
1. Run my folder's checks (backend: `pytest -q`; web: `npm run build && npm run lint`). Stop if they fail.
2. Show `git status` and `git diff --stat`. Stage ONLY my folder and my prefixed contracts/ files. Never stage .env files.
3. Commit with a message starting "$ARGUMENTS: " that says what the stage does.
4. Run `git pull --rebase origin main`. If anything came in, re-run the checks.
5. Run `git push origin main` (I'll approve it).
```

(Files in `.claude/commands/` work as slash commands. Newer Claude Code versions also support "skills" for the same job, but plain command files are simpler and are all you need here.)

#### Personal file (each member creates their own; never committed)

**`.claude/settings.local.json`**: Claude Code keeps this file out of git automatically. It holds the rule that blocks Claude's edit tools from touching your teammate's files. Deny rules always win over allow rules.

Member A:

```json
{
  "permissions": {
    "deny": [
      "Edit(./web/**)",
      "Edit(./contracts/migrations/001_init.sql)",
      "Edit(./contracts/migrations/b_*)"
    ]
  }
}
```

Member B:

```json
{
  "permissions": {
    "deny": [
      "Edit(./backend/**)",
      "Edit(./contracts/migrations/001_init.sql)",
      "Edit(./contracts/migrations/a_*)",
      "Edit(./contracts/api.md)",
      "Edit(./contracts/scoring.md)",
      "Edit(./contracts/events.md)"
    ]
  }
}
```

- These paths are relative to where you start Claude, so **always start `claude` from the repo root**.
- Run `/permissions` once to confirm the rules loaded.
- These rules block Claude's file-editing tools, not shell commands. The `CLAUDE.md` rules cover the rest; if Claude ever proposes a shell command that writes into the other folder, say no.

#### Your loop for every stage

```
cd proof-of-demand && claude
/sync                      # get teammate's latest
Shift+Tab                  # plan mode, for big stages: A1, A4, A5, B3, B4, B6
/stage B3                  # Claude plans → you OK → it builds and tests
                           # do any manual steps it lists (SQL, keys, dashboards)
/ship B3                   # checks → commit → pull --rebase → push
/clear                     # fresh session for the next stage
```

#### Saving Claude Pro usage

- Pro has usage limits, and Opus uses them up faster than Sonnet. Keep Opus for the hard stages (scoring pipeline, voice matching, widget recorder, dashboard, payments).
- Switch with `/model` to Sonnet for small fixes, styling, copy changes and README writing.
- `/usage` shows your plan's usage limits and current status. Check it before starting a big stage.
- **One stage per session** and `/clear` between stages. A long session re-reads all earlier history on every message. Use `/compact` if a single stage runs long.
- Give Claude the error message and the file name directly instead of asking it to "look around". Exploring costs usage.
- If one of you hits the limit at a bad moment, the other can review that person's stage output or test on their phone. Don't edit their folder.

---

## 1. Your job in one paragraph

You build everything people see and pay through. Founders sign in, create a waitlist with their own voice question, and paste a small widget onto their landing page. Visitors use that widget to give their email and record a 20-second answer, which goes to A's backend. Founders watch a live dashboard showing the funnel (signups → real humans → specific pain → paid), with quotes and plain-English warnings. They share a public report and badge. Signups can pay a small refundable deposit through Dodo Payments, and founders can get alerts through viaSocket. You also lead the launch and onboarding of real users.

```
Founder ──▶ /login ──▶ /app (create waitlist) ──▶ copies embed code
Visitor on founder's site ──▶ iframe /w/[slug] ──▶ email + voice + device id
        ──POST──▶ A's backend ──▶ Supabase ──(live updates)──▶ /app/w/[slug] dashboard
Visitor ──▶ optional deposit ──▶ Dodo checkout ──▶ /api/webhooks/dodo ──▶ deposit_status = paid
Anyone ──▶ /r/[slug] public report  ·  /badge/[slug].svg badge
A's backend ──signup.scored──▶ viaSocket ──▶ founder's Slack / Google Sheet / email
```

## 2. Your tools

| Purpose | Tool |
|---|---|
| Web app | Next.js (App Router, TypeScript) + Tailwind CSS |
| Login, database, live updates | Supabase (`@supabase/ssr`, `@supabase/supabase-js`): magic-link email login, Postgres, Realtime (pushes new rows to the dashboard without refreshing) |
| Voice recording in the browser | Built-in `MediaRecorder` browser feature, nothing to install |
| Device id (spots repeat signups from one device) | `@fingerprintjs/fingerprintjs`. **Weak signal:** the free library is 40–60% accurate, and v4's licence allows prototypes only (production needs a paid licence) |
| Payments | Dodo Payments in test mode: `dodopayments` SDK (checkout sessions, refunds) + Standard Webhooks verification, or the `@dodopayments/nextjs` adaptor |
| Alerts to founders | viaSocket (coupon `HHGOA26-VIASOCKET`; extended-plan code is in the builder group) |
| Hosting | Vercel (root directory = `web`) |
| Charts (optional) | Plain Tailwind bars are enough for a 4-step funnel |

All tool details, with sources, are in **TOOLS_VERIFIED.md**.

---

## 3. Stages

Each stage lists **what to build**, **tools**, and the **output** that proves it's done. Don't start the next stage until the output exists and is committed.

### Stage 0: Setup (together, Thu 09:00–10:00)

**Your tasks**
1. Accept A's GitHub invite and clone the repo. Create **your own** `.claude/settings.local.json` (Member B version, section 0.7), start `claude` from the repo root, and run `/permissions` to check the rules loaded.
2. **Supabase:** create the project → run `contracts/migrations/001_init.sql` in the SQL editor → create a **private** storage bucket `audio` → enable Realtime on the `signups` table → turn on email (magic link) login.
3. **Vercel:** create a project from the repo with root directory `web`.
4. **Dodo Payments:** create an account in **test mode**. Create a product called "Early access deposit" (one-time, refundable). Note the product id.
5. **viaSocket:** create an account and apply coupon `HHGOA26-VIASOCKET`.
6. Share the Supabase URL and service key with A privately.
7. `web/CLAUDE.md`:
   ```markdown
   # web/ is owned by Member B
   - Next.js App Router + TypeScript + Tailwind. Run: npm run dev. Check: npm run build && npm run lint
   - Read contracts/api.md, contracts/scoring.md before touching data or labels.
   - Never call the backend from founders' sites directly; the widget is always an iframe of /w/[slug].
   - Server-only secrets (service key, Dodo keys) never go in NEXT_PUBLIC_ variables.
   ```

**Decide together (5 min):** deposits on other teams' waitlists. Recommended: **test mode** for other teams, **live mode** only on your own Proof of Demand waitlist. That avoids holding real money for other people's products before you know Dodo's terms allow it.

**Output:** `001_init.sql` run; bucket and Realtime on; Vercel project linked; Dodo test product created; keys exchanged.

---

### Stage B1: App skeleton + login + deploy (Thu 10:00–11:00)

**Build**
- `npx create-next-app@latest web` (TypeScript, Tailwind, App Router).
- Supabase client helpers for the browser and the server (`@supabase/ssr`).
- `/login`: email magic link. `/app`: protected page (redirect to `/login` if signed out).
- Simple layout: top bar with "Proof of Demand" and a sign-out button.

**Tools:** Next.js, Supabase Auth, Vercel.

**Output:** live Vercel URL; you can sign in with your email and see `/app`. Send A the site URL (A needs it for `WEB_ORIGIN`). **Commit: "B: skeleton + login".**

---

### Stage B2: Founder creates a waitlist (Thu 11:00–12:00)

**Build**
- Migration `contracts/migrations/b_002_policies.sql` (row-level security):
  - founders can create, read and update only their own `waitlists`
  - founders can read `signups` only for waitlists they own
  - nobody can read `signups` with the public (anon) key
  - store audio is never public

  Run it and tell A.
- `/app`: list of the founder's waitlists + "New waitlist" form:
  - **product name**
  - **one-line description**. This helps the AI judge relevance, so explain that in the form hint.
  - **voice question**, pre-filled with *"When did this problem last cost you time or money? Tell us what happened."*
  - **slug**, auto-made from the name and editable
  - **deposit on/off and amount**
- After creating: show the **embed code** with a copy button:
  ```html
  <script src="https://YOUR_SITE/embed.js" data-waitlist="acme" async></script>
  ```
  plus a direct link `https://YOUR_SITE/w/acme` for people without a website.

**Tools:** Next.js server actions, Supabase.

**Output:** create two waitlists while signed in; a second account can't see them. **Commit.**

---

### Stage B3: The signup widget (Thu 12:00–13:00, then 14:00–15:30)

This is the most important screen. Founders' visitors judge the whole product by it.

**Build**
- **`/w/[slug]`** (public page; load the waitlist's name, question and deposit setting on the server using the service key; show only those fields):
  1. Product name + the question.
  2. **Record button**:
     - timer counting to 20 s with auto-stop
     - "Re-record" and "Play back" buttons
     - the mic permission request only appears after the user taps Record
  3. Email field + consent checkbox: *"I agree my voice answer is stored and analysed to verify my signup."*
  4. Submit → `POST {NEXT_PUBLIC_BACKEND_URL}/v1/signups` as multipart form (fields exactly as in `contracts/api.md`, including FingerprintJS `visitorId` as `device_id`).
  5. Success screen: "You're on the list." Then poll `GET /v1/signups/{id}/status` every 2 s for up to 20 s → show "Verified ✓" when the verdict is `verified`.
  6. Handle 409 (already signed up), 429, 400 with friendly messages.
- **Small "skip voice" link** (signup still counts, as `unverified`). Keep it visible but secondary.
- **Browser formats:** use `MediaRecorder.isTypeSupported` to pick the first supported of `audio/webm;codecs=opus`, `audio/mp4`, `audio/ogg;codecs=opus`, and send the matching file extension. Safari before 18.4 records **mp4 only**; Safari 18.4+ also records webm. Never hardcode one format.
- **Recording only works on HTTPS** (`getUserMedia` needs a secure page). Vercel URLs are HTTPS; `localhost` also works for testing.
- **`/embed.js`** (a static file in `web/public/`): finds its own `<script>` tag, reads `data-waitlist`, and inserts an iframe of `/w/[slug]` (width 100%, height ~520 px, `allow="microphone"`). The `allow="microphone"` part is required or recording won't work inside the iframe. Some website builders wrap embeds in their own iframe without this permission (reported for Wix), so always show the direct `/w/[slug]` link under the embed code as a fallback.

**Tools:** MediaRecorder, FingerprintJS, fetch.

**Output**
- Works on **Chrome desktop, Android Chrome and iPhone Safari**. Test all three; Safari is the usual failure.
- A test HTML file `web/public/embed-test.html` that includes the script tag works.
- **→ Sync 1 at 13:00:** a real signup from your widget creates a row in Supabase via A's live backend. **Commit.**

---

### Stage B4: Founder dashboard (Thu 15:30–17:00)

**Build** `/app/w/[slug]`:
- **Funnel cards across the top**, using the exact definitions in `contracts/scoring.md`: Signups → Real humans → Specific pain → Paid. Show the count and the % of signups for each.
- **Signups table**, newest first:

  | Column | Shows |
  |---|---|
  | Email | Masked (`ra***@gmail.com`) |
  | Verdict | Badge (green verified / amber suspicious / red fake / grey unverified) |
  | Pain | Score + level |
  | Quote | `pain_quote` in italics |
  | Warnings | Plain-English text for each flag, from the table in `contracts/scoring.md` |
  | Deposit | Status |
  | Time | When they signed up |

  Rows still processing show a spinner.
- **Filters:** "Real humans only", "High pain only".
- **Live updates:** subscribe to Supabase Realtime (`postgres_changes`, table `signups`, filter `waitlist_id=eq.<id>`) so new and updated rows appear without refresh. This is a great live-demo moment.
  - If nothing arrives, check two things. Is `signups` in the `supabase_realtime` publication? Does row-level security let this founder read the rows? It silently drops events otherwise.
- **"Top quotes" panel:** the 5 highest-pain quotes from verified humans. Founders will screenshot this.
- Put the flag-code → text mapping in one file `web/lib/flags.ts`.

**Output:** record a signup on your phone and watch it appear and update to scored on your laptop's dashboard. **Commit.**

---

### Stage B5: Public report + badge (Thu 17:00–18:00)

**Build**
- Migration `contracts/migrations/b_003_funnel_view.sql`: a view or database function returning, per waitlist slug, only **counts** for the 4 funnel steps + top 3 quotes from verified, high-pain signups. **No emails, ever.** Run it, tell A.
- **`/r/[slug]`**: a clean shareable page.
  - Product name, the funnel with numbers, top quotes, "Last updated" time.
  - A short "How we verify" note: voice check, duplicate-person check, AI scoring of how specific the problem is, deposits.
  - Founder can toggle the report public/private (add a `report_public` column in the same migration, default false).
- **`/badge/[slug].svg`**: a small image like `✓ 214 verified humans · 23 paid | Proof of Demand`, linking to the report. Show the badge embed code in the dashboard.

**Output:** report page and badge work while logged out; private reports return "not public". **Commit.**

**→ Sync 2 at 18:00:** full flow on live URLs, on phone and laptop.

**18:00–21:00 — you lead onboarding.** Walk up to teams in the house and say:

> "Want to know how many of your waitlist signups are real people with a real problem? It takes 2 minutes to add to your landing page, and it's free."

Help them create a waitlist and paste the embed code. Write down every confusion and bug. Target: **3–5 teams live by 21:00.**

---

### Stage B6: Dodo Payments deposits (Thu 21:30–00:30)

**Build** (test mode; exact calls and code are in TOOLS_VERIFIED.md → section 1):
- After a successful signup, if the waitlist has deposits on, show: *"Reserve your spot with a refundable $1 deposit."* → button.
- `POST /api/deposit` (server route): receives `signup_id`, then:
  1. Creates a Dodo **checkout session**: `checkoutSessions.create({ product_cart: [{ product_id: DODO_DEPOSIT_PRODUCT_ID, quantity: 1 }], customer: { email }, return_url, metadata: { signup_id } })`, with the client set to `environment: 'test_mode'`.
  2. Sets `deposit_status = 'pending'`.
  3. Returns `checkout_url`.

  The widget opens it with `window.open(checkout_url, '_blank')`, as in Dodo's own example. Sessions stay valid for 24 hours.
- `POST /api/webhooks/dodo` (register it in the Dodo dashboard under Developer → Webhooks):
  - **Verify the signature first.** Either use the `Webhooks` handler from `@dodopayments/nextjs`, which verifies for you, or the `standardwebhooks` library with `DODO_WEBHOOK_SECRET` on the **raw** request body.
  - On `payment.succeeded`: read `signup_id` from the payment's `metadata`, set `deposit_status = 'paid'`, save `deposit_payment_id`. Dodo's own examples disagree on where `metadata` sits in the body, so log one real test payload first.
  - On `refund.succeeded`: set `refunded`.
  - Ignore other events. Use the service key server-side only.
- Dashboard: "Refund" button per paid signup → `refunds.create({ payment_id })` (no `items` = the whole payment), or refund from the Dodo dashboard if wiring it is slow.
- Write the refund promise clearly on the widget: when and how people get their money back.

**Tools:** Dodo Payments test mode (test card `4242 4242 4242 4242`, expiry `06/32`, CVC `123`), Dodo CLI `dodo wh listen` to forward test webhooks to your laptop, Next.js route handlers.

**Output:** a test payment flips the row to **paid** and the Paid funnel count goes up live. **Commit.**

**Also tonight:** draft Friday's launch posts (X/Twitter, LinkedIn): a 3-line problem, a 20 s screen recording of signup → verified → dashboard, and the link.

---

### Stage B7: Your own landing page + pricing (Fri 08:00–09:30)

**Build** `/` (homepage):
- Headline: *"Waitlists lie. Know which signups are real."*
- 3 short points: real human check, specific-pain score, refundable deposits.
- **Your own waitlist embedded using your own widget.** This is your product proving itself, and these are your real users.
- **Pricing:** Free (1 waitlist, 100 signups) and Pro (e.g. $9/month: unlimited signups, public badge, alerts) with a Dodo checkout for Pro. Dodo asks teams to "put a price on what you built." Even if no one buys this week, it has to be real and working.
- Link to a "Add to your site in 2 minutes" guide (3 steps with screenshots).

**Output:** homepage live; your own waitlist collecting real signups; Pro checkout works in test mode. **Commit.**

---

### Stage B8: viaSocket alerts (Fri 09:30–10:30)

**Build**
- In viaSocket, create a flow: **trigger** = webhook (copy its URL) → **actions** = send a Slack or email message ("New verified signup: pain 82, '...quote...'") and add a row to a Google Sheet.
- Give A the webhook URL for `NOTIFY_WEBHOOK_URL` (A adds it on Render).
- Dashboard "Alerts" section: explain what the alerts send. Optional: let founders paste their own viaSocket webhook URL per waitlist (new column via migration `b_004_...`) if time allows.

**Output:** a new signup → a message arrives in Slack or email and a row appears in the Sheet within seconds. Screenshot it for the viaSocket track. **Commit.**

---

### Stage B9: Launch, users and submission (Fri ~11:00 → code freeze 23:00)

- **~11:00 Phase 1:** submit the live product, post the launch on socials, and get help from House of NGMI creators.
- Keep onboarding teams and online founders (Indie Hackers, X build-in-public). Track: teams using it, total signups, fakes caught, deposits.
- Fix UI bugs real users hit, mobile first.
- Prepare the **final submission**:
  - live links
  - 2-minute demo video (use A's clips)
  - screenshots (dashboard, public report, TigerGraph graph, viaSocket alert, Dodo payment)
  - **real usage numbers**
  - which partner tools you used and how
- Update the "Live links" and "Usage" sections of the root `README.md` (ping A first).

**Output:** submission ready before Friday night; Saturday morning is just a final check before 09:59.

---

## 4. Definition of done (your side)

- [ ] Live site; magic-link login works
- [ ] Founders can create a waitlist and copy embed code
- [ ] Widget works on Chrome, Android and iPhone Safari, including inside an iframe
- [ ] Dashboard funnel + table update live
- [ ] Public report + badge work while logged out, no emails exposed
- [ ] Dodo deposit (test) marks signups paid; Pro plan checkout exists
- [ ] viaSocket alert arrives on a new scored signup
- [ ] Homepage with your own waitlist live and collecting real users
- [ ] Submission: links, video, screenshots, real usage numbers
