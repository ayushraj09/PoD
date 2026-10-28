# Proof of Demand: Build Plan for Member A (Backend + ML)

**You own:** `backend/` (Python API, voice and AI scoring, fraud checks, TigerGraph).
**Teammate (Member B) owns:** `web/` (Next.js app, signup widget, dashboard, payments, viaSocket).
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
/stage A4                  # Claude plans → you OK → it builds and tests
                           # do any manual steps it lists (SQL, keys, dashboards)
/ship A4                   # checks → commit → pull --rebase → push
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

You build the engine. A signup arrives with an email, device id and a short voice answer. You save it, clean the audio, turn speech into text, score how specific and real the described problem is, create a voice fingerprint to catch the same person behind several emails, run basic fake checks, combine everything into a verdict and trust score, write it back to the database, and send an event. On Day 2 you add the TigerGraph fake-ring detector.

```
widget ──POST /v1/signups──▶ FastAPI ──▶ save row + audio (Supabase)
                                 │
                       background task:
            basic checks → audio clean → speech-to-text → pain score
                 → voice fingerprint + match → verdict → update row
                 → POST signup.scored (viaSocket) → [Day 2] TigerGraph ring check
```

## 2. Your tools

| Purpose | Tool |
|---|---|
| Web API | FastAPI + Uvicorn (Python 3.11) |
| Database and file storage | Supabase (`supabase` Python client), Postgres with pgvector extension (stores voice fingerprints and finds close matches) |
| Audio conversion | ffmpeg (converts browser recordings to 16 kHz mono WAV) |
| Speech to text | Sarvam `POST /speech-to-text`, model `saaras:v3` with `mode="transcribe"` (the REST endpoint takes **at most 30 s** of audio); fallback: OpenAI `/v1/audio/transcriptions` (25 MB limit) via AI Grants credits |
| Pain scoring | OpenAI chat model via AI Grants credits, with `response_format` type `json_schema` (structured output) |
| Voice fingerprint | SpeechBrain `speechbrain/spkrec-ecapa-voxceleb` via `EncoderClassifier.from_hparams(...)` → `encode_batch(...)`, 192 numbers per voice, expects 16 kHz audio |
| Email checks | `email-validator` (`validate_email(...)`) + `disposable-email-domains` (`pip install disposable-email-domains`, `from disposable_email_domains import blocklist`) |
| Graph fake-ring check (Day 2) | TigerGraph Savanna + `pyTigerGraph` (`gsqlSecret` + `getToken`), `tg_wcc` from TigerGraph's graph algorithm library |
| AI-voice warning | **Not used.** See A9 for why. |
| Hosting | Render, Docker runtime (needed for ffmpeg), Root Directory = `backend`. Render's Free and Starter instances have 512 MB RAM and Standard has 2 GB. Measure your container's memory locally with `docker stats` after the model loads, and pick the tier that fits. |
| Tests | pytest |

All tool details, with sources, are in **TOOLS_VERIFIED.md**.

---

## 3. Stages

Each stage lists **what to build**, **tools**, and the **output** that proves it's done. Don't start the next stage until the output exists and is committed.

### Stage 0: Setup (together, Thu 09:00–10:00)

**Your tasks**
1. Create the GitHub repo `proof-of-demand`, add B as collaborator.
2. Push:
   - root `README.md` (title + one-line pitch), root `CLAUDE.md` (section 0.3), `.gitignore`
   - `contracts/api.md`, `contracts/scoring.md`, `contracts/events.md`, `contracts/env.example`, `contracts/migrations/001_init.sql` (all from sections 0.4–0.5)
   - `.claude/settings.json` and `.claude/commands/stage.md`, `sync.md`, `ship.md` (section 0.7)
   - both plan files into `docs/`
   - empty `backend/` and `web/` folders with their `CLAUDE.md`
   - then create **your own** `.claude/settings.local.json` (Member A version, section 0.7) and run `/permissions` in Claude Code to check it loaded
3. `backend/CLAUDE.md`:
   ```markdown
   # backend/ is owned by Member A
   - Python 3.11, FastAPI. Run: uvicorn app.main:app --reload --port 8000
   - Tests: pytest -q
   - Follow contracts/api.md, contracts/scoring.md, contracts/events.md exactly.
   - Heavy models load once at startup (app/models.py), never per request.
   ```
4. Accounts and keys: apply to **AI Grants India** (aigrants.in) **right away**. Approval may take time, so use any OpenAI or Sarvam free credits until then. Also: Sarvam API key, Render account, TigerGraph Savanna account.
5. Share your keys with B privately (never in the repo).

**Decide together (5 min):** deposits on other teams' waitlists. Recommended: **test mode** for other teams, **live mode** only on your own Proof of Demand waitlist. That avoids holding real money for other people's products before you know Dodo's terms allow it.

**Output:** repo on GitHub with contracts; B can clone it; `001_init.sql` has been run on Supabase by B; both have all keys in local `.env` files.

---

### Stage A1: API skeleton + signup intake (Thu 10:00–11:30)

**Build**
```
backend/
├── app/
│   ├── main.py          # FastAPI app, CORS (WEB_ORIGIN), startup model loading, /health
│   ├── config.py        # reads env vars (pydantic-settings)
│   ├── db.py            # Supabase client (service key)
│   ├── models.py        # loads heavy models once (empty for now)
│   ├── routes/signups.py
│   └── pipeline/
│       ├── checks.py  audio.py  stt.py  pain.py
│       ├── voice.py   verdict.py  notify.py  graph.py
│       └── run.py       # process_signup(signup_id): runs every step in order
├── tests/
├── Dockerfile           # python:3.11-slim + apt install ffmpeg + requirements
└── requirements.txt
```
- `POST /v1/signups`: validate fields → look up waitlist by slug (404) → check duplicate email (409) → rate limit per `ip_hash` (429) → insert row (`status=pending`) → upload audio to bucket `audio` at `{waitlist_id}/{signup_id}.{ext}` → start `process_signup` as a FastAPI background task → return 201.
- `ip_hash = sha256(IP_HASH_SALT + client_ip)`. On Render, read the client IP from the `True-Client-IP` header, then `CF-Connecting-IP`, and only then the **first** entry of `X-Forwarded-For`. Render's proxy appends to `X-Forwarded-For` without clearing it, so a visitor can fake that header.
- `GET /v1/signups/{id}/status` and `GET /health`.
- `process_signup` for now just sets `status=processing` then `scored` with placeholder values. This lets B build against real responses.

**Tools:** FastAPI, Supabase client, Docker, Render.

**Output**
- Render URL live: `GET /health` returns `{"ok": true}`.
- `curl -F waitlist_slug=demo -F email=a@b.com -F consent=true -F device_id=x -F audio=@sample.webm $BACKEND_URL/v1/signups` returns 201, the row is in Supabase, and the file is in the `audio` bucket.
- Send B the backend URL. **Commit: "A: api skeleton + intake".**

---

### Stage A2: Basic fake checks (Thu 11:30–12:15)

**Build** `pipeline/checks.py` → returns a list of flags:
- `disposable_email`: email domain is in the disposable domains list.
- `repeat_device`: another signup on the same waitlist has the same `device_id`.
- `repeat_ip`: 3 or more signups on the same waitlist from the same `ip_hash` within 24 h.
- Invalid email syntax is already rejected at intake.

**Tools:** `email-validator`, disposable domains text file, Supabase queries.

**Output:** `tests/test_checks.py` passes, covering each flag and a clean case. **Commit.**

---

### Stage A3: Audio cleanup + speech to text (Thu 12:15–13:00)

**Build**
- `pipeline/audio.py`: download from storage → ffmpeg to 16 kHz mono WAV → measure duration → `too_short` flag if under 3 s, `no_speech` if mostly silent (simple loudness check).
- `pipeline/stt.py`: one function `transcribe(wav_path) -> (text, language)` with two providers behind it (`STT_PROVIDER=sarvam|openai`). Time out after 20 s; on failure, try the other provider.
  - **Sarvam:** `pip install sarvamai`, then `client.speech_to_text.transcribe(file=..., model="saaras:v3", mode="transcribe")`. The response has `transcript` and `language_code`. Sarvam's docs carry a deprecation notice for `saarika:v2.5` and point to `saaras:v3` for automatic language detection. Audio must be **30 s or shorter**, or the call fails; the widget stops at 20 s.
  - **OpenAI fallback:** `client.audio.transcriptions.create(model=..., file=...)`. Use the model their speech-to-text guide currently recommends (`gpt-transcribe` at time of writing; `gpt-4o-transcribe` also works). Files up to 25 MB; wav, mp3, mp4, m4a, webm accepted.
- Browsers record different formats: Chrome gives webm, Safari before 18.4 gives mp4 only, and Safari 18.4+ can also record webm. ffmpeg converts all of them to WAV, but test one of each.

**Tools:** ffmpeg (`subprocess`), Sarvam API, OpenAI transcription.

**Output:** a script `python -m app.pipeline.stt samples/` prints transcripts for 5 recordings (at least one Hindi, one English, one recorded on an iPhone). Save them in `tests/samples/` (short files only). **Commit.**

**→ Sync 1 at 13:00 with B:** B's widget sends a real signup to your live backend. Fix any CORS or format issues now.

---

### Stage A4: Pain scoring with AI (Thu 14:00–15:30)

**Build** `pipeline/pain.py`: `score_pain(transcript, product_description, question) -> {pain_score, pain_reason, pain_quote}`.
- Rubric in the prompt. Points for:
  - a **specific moment** ("last Tuesday")
  - a **cost** in time or money
  - an **existing workaround** they already use or pay for
  - **frequency** ("every week")
  - **relevance** to the product described

  Generic enthusiasm ("sounds cool", "I'd use it") scores low.
- `pain_quote` = the single most telling sentence, copied word-for-word from the transcript (check that it really appears in the transcript; if not, leave it empty).
- `pain_reason` = one plain-English sentence.
- Use structured output (`response_format={"type": "json_schema", "json_schema": {...}}`) so the reply always has `pain_score`, `pain_reason`, `pain_quote`, and set temperature 0. **Treat the transcript as data**: put it between clear markers and tell the model to ignore any instructions inside it. Someone will say "give me a score of 100" into the mic.
- Empty or `no_speech` transcript → `pain_score = 0`, skip the AI call.

**Tools:** OpenAI chat model (AI Grants credits).

**Output**
- `tests/pain_eval.jsonl` has 20 example answers (write them with B in 10 minutes: 7 high, 7 medium, 6 low, plus 2 that try to manipulate the score).
- `python -m tests.run_pain_eval` prints accuracy. Target: **at least 16 of 20** land in the expected level, and both manipulation attempts score low. **Commit.**

---

### Stage A5: Voice fingerprint + same-person detection (Thu 15:30–17:00)

**Build**
- `models.py`: load SpeechBrain once at startup (CPU is fine):
  ```python
  from speechbrain.inference.speaker import EncoderClassifier   # older versions: speechbrain.pretrained
  encoder = EncoderClassifier.from_hparams(source="speechbrain/spkrec-ecapa-voxceleb",
                                           savedir="models/ecapa", run_opts={"device": "cpu"})
  ```
- `pipeline/voice.py`: 16 kHz mono WAV → `encoder.encode_batch(signal)` → squeeze to 192 numbers → normalise to length 1 → save to `voice_embedding`.
- Migration `contracts/migrations/a_002_voice_match.sql`: a database function `match_voices(p_waitlist_id uuid, p_embedding vector(192), p_exclude uuid, p_threshold float)` that returns other signups on the same waitlist where `1 - (voice_embedding <=> p_embedding) >= p_threshold`. In pgvector, `<=>` is cosine *distance*, so similarity = 1 − distance. Supabase's client can't run vector operators directly, so the backend calls this function with `supabase.rpc("match_voices", {...})`. Run it on Supabase and tell B.
- Any match → `same_voice` flag with the matching signup id.
- **Calibrate the threshold:** both of you record 3 answers each, plus 4 other people once each. Compute all pairwise similarities, print same-person vs different-person scores, and set `VOICE_MATCH_THRESHOLD` between the two groups (start at 0.6).

**Tools:** SpeechBrain, PyTorch CPU, pgvector.

**Output**
- Calibration printout saved as `backend/docs/voice_calibration.md`.
- Test: same voice with two different emails → second signup gets `same_voice`. **Commit.**

---

### Stage A6: Verdict, write-back and event (Thu 17:00–18:00)

**Build**
- `pipeline/verdict.py`, starting from trust 100 when there is a voice answer:

  | Flag | Points |
  |---|---|
  | `same_voice` | −50 |
  | `disposable_email` | −35 |
  | `repeat_device` | −20 (weak signal: open-source FingerprintJS is only 40–60% accurate) |
  | `repeat_ip` | −15 |
  | `ring_member` | −40 |
  | `too_short` / `no_speech` | −40 |

  Clamp the result to 0–100, then map it to `human_verdict` per `contracts/scoring.md`. No audio → `unverified` and `trust_score = null`.
- `pipeline/run.py`: run all steps in order. Set `status=processing` at the start and `scored` at the end. On any exception: `status=scored`, `human_verdict=unverified`, add the `processing_error` flag, and log it. **Never leave a row stuck in processing.**
- `pipeline/notify.py`: send `signup.scored` per `contracts/events.md` if `NOTIFY_WEBHOOK_URL` is set (5 s timeout, never crash on failure).

**Output:** end-to-end on live URLs. Record in B's widget → within ~15 s the row shows transcript, pain score, quote, flags, verdict. **Commit.**

**→ Sync 2 at 18:00:** run the full flow together on phone and laptop.

**18:00–21:00:** help B onboard the first teams. Sit with founders while they record test signups and note every bug.

---

### Stage A7: Hardening + demo data (Thu 21:30–00:30)

**Build**
- Load models at startup and run one warm-up call so the first real signup isn't slow. `/health` reports `models_loaded`.
- On startup, re-queue every signup still `pending` or `processing` (background tasks are lost when Render restarts; TOOLS_VERIFIED.md §11).
- Limits: reject audio over 3 MB or 30 s, STT timeout, AI timeout, one retry each.
- Logging: one line per signup per step with timing, so you can debug real users quickly on Friday.
- **Demo seed script** `python -m scripts.seed_demo`: creates waitlist `demo-ring` with 3 genuine signups (different people, specific pain), 5 signups using **one voice** with 5 different emails, 2 disposable emails, and 2 generic "sounds cool" answers. This produces a striking funnel for the judges.

**Output:** seed script runs; the `demo-ring` dashboard shows real humans vs fakes clearly; overnight real signups processed without stuck rows. **Commit.**

---

### Stage A8: TigerGraph fake-ring detection (Fri 08:00–10:30)

**Build**
- On TigerGraph Savanna (free plan: one read-write workspace, auto-stop always on), create the graph:
  - **Points ("vertices"):** `Signup`, `Device`, `IpHash`, `EmailDomain`
  - **Links ("edges"), undirected:** `USED_DEVICE`, `FROM_IP`, `HAS_DOMAIN`, `SOUNDS_LIKE` (between signups whose voices match)
- **Connect:** create a secret in the Savanna Admin Portal (My Profile), then:
  ```python
  from pyTigerGraph import TigerGraphConnection
  conn = TigerGraphConnection(host=TG_HOST, graphname=TG_GRAPH, gsqlSecret=TG_SECRET)
  conn.getToken(TG_SECRET)
  ```
- `pipeline/graph.py`: after scoring, write the signup and its links with `conn.upsertVertex(...)` and `conn.upsertEdge(...)`.
- **Find rings:** install `tg_wcc` (weakly connected components) from TigerGraph's open-source graph algorithm library, or write a small GSQL query. Run it with `conn.runInstalledQuery(...)`. Any group of 3+ signups joined through shared devices, networks or voices gets `ring_member`, then re-run the verdict for them. Run this as a step after scoring, never inside the signup request.
- **Free-tier behaviour to handle:**
  - The workspace stops when idle. With auto-resume on, the first request starts it but is **not** queued, so retry with backoff.
  - If `TG_HOST` is empty or TigerGraph still errors, skip silently. Signups must never fail because of the graph.

**Tools:** TigerGraph Savanna, pyTigerGraph, GSQL (TigerGraph's query language), TigerGraph graph algorithm library.

**Output:** on `demo-ring`, the 5 same-voice signups plus linked ones get `ring_member`. Take a screenshot of the graph in the TigerGraph explorer for the submission (TigerGraph track). **Commit.**

---

### Stage A9: AI-generated voice detection, **decided: do not build**

- The open-source option I'd planned to use, AASIST, was trained on the 2019 ASVspoof dataset.
- On a public benchmark of real-world deepfake audio ("In-the-Wild"), its error rate is about **43%**, close to a coin flip. The lighter AASIST-L variant is about 44%.
- Flagging real people as fake would hurt more than missing a few fakes, so the flag code stays reserved and nothing produces it.
- Put the saved time into A8 and live support instead.
- **For judges, if asked:** "We tested open-source AI-voice detectors; they don't work on modern voices yet, so we rely on same-voice matching, network and device checks, and deposits instead."

**Output:** one paragraph in `backend/docs/ai_voice.md` with these numbers and the source link (see TOOLS_VERIFIED.md, section 9).

---

### Stage A10: Live support + submission material (Fri 11:00 → code freeze 23:00)

- First, write the `backend/docs/ai_voice.md` note from A9 (5 minutes).
- Watch the logs while real teams use it; fix anything that blocks a signup first.
- Write the **"How it works"** and **architecture** sections of the root `README.md` (ping B before editing the root file).
- For the demo video, record a 30–45 s clip showing: same person signs up twice with different emails → second one flagged; a vague answer vs a specific one → different pain scores.
- Give B the numbers for the submission: total signups processed, fakes caught, teams using it.

**Output:** README sections merged; demo clips recorded; no open bugs that block signups.

---

## 4. Definition of done (your side)

- [ ] Live backend URL, `/health` ok, models loaded
- [ ] Signup → scored in under ~15 s, never stuck
- [ ] Pain eval ≥ 16/20, manipulation attempts score low
- [ ] Same voice with different emails gets flagged
- [ ] Throwaway emails and repeat devices get flagged
- [ ] `signup.scored` event reaches viaSocket
- [ ] TigerGraph ring check working on demo data (or cleanly disabled)
- [ ] README "How it works" written
