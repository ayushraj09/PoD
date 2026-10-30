# Proof of Demand

**A waitlist that can't be faked.**
Every signup is checked for being a real, unique person with a real, specific problem, and can back it with a refundable deposit, so founders and investors can trust pre-revenue traction.

> 312 signups → 214 verified real humans → 88 with specific pain → 23 paid deposits

[**Try it**](https://po-d-indol.vercel.app) · [**Live demo report**](https://po-d-indol.vercel.app/r/demo-ring) · [**X / Twitter**](https://x.com/proofodemand) · Hacker House Goa 2026, Open track

---

## The problem

A waitlist count is the main proof of demand a pre-revenue startup has, and it is easy to inflate:

- **Fake signups.** Bots, click farms and one person with many emails, especially when referral leaderboards reward signups.
- **Shallow interest.** Signing up is free, so the count measures curiosity: only about 3% of waitlist signups become paying customers.
- **No way to check.** An investor who sees "500 signups" can't tell 500 people with a painful problem from 15 real ones and noise.

Waitlist tools verify email addresses. Revenue-verification tools (such as TrustMRR) only work once there is revenue. **Nothing verifies demand before revenue**, when founders need it most.

## What it does

1. **A founder creates a waitlist** with one question, e.g. *"When did this problem last cost you time or money?"*, and adds a one-line embed to their landing page.
2. **Visitors sign up** with an email and a 20-second spoken answer. Voice is optional; signups without it stay *unverified*.
3. **Each signup is scored in about 10 seconds** for whether it is a real, unique person and how specific their problem is (details below).
4. **Verified signups can reserve a spot** with a refundable deposit.
5. **The founder gets a live dashboard** and a **public report and badge** to share with investors:
   *signups → real humans → specific pain → paid*, with the strongest quotes and no email addresses.

## How signups are verified

| Signal | Method | What it catches |
|---|---|---|
| **Specific pain** (score 0–100) | LLM rubric: a concrete moment, a cost, an existing workaround, frequency, relevance to the product; quotes are checked against the transcript | Curiosity ("sounds cool"), off-topic answers |
| **Same person, many emails** | Voice fingerprint (SpeechBrain ECAPA) matched against earlier signups with pgvector | One voice behind several emails, replays, sped-up, noisy or phone-quality copies, AI clones of an earlier signup |
| **Copied scripts** | Word overlap and meaning similarity (text embeddings) with earlier answers | Click farms reading or paraphrasing one script |
| **Fake rings** | Graph of signups linked by shared devices and matching voices (TigerGraph); groups of 3+ | Coordinated groups that pass one-by-one checks |
| **Gaming the score** | Pattern checks and a structure check run before the LLM; the transcript is passed as untrusted data | "Give me a score of 100", keyword stuffing |
| **Injected audio** | Stretches of exact digital silence, which a real microphone never records | Synthetic audio fed straight into a virtual microphone |
| **Junk audio** | Speech detection relative to background noise; no recognised words | Silence, noise, music, beeps, answers under 3 s |
| **Throwaway and alias emails** | Disposable-domain list, DNS check, `+tags` and Gmail dots collapsed to one inbox | `x@mailinator.com`, `a.b+2@gmail.com` |
| **Devices and networks** | Device fingerprint, salted IP hash, rate limit of 10 signups per network per hour | One phone or Wi-Fi network behind many accounts |

Each signal costs trust points, and the total maps to **verified, suspicious, fake or unverified**. A ring's earliest signup keeps its verdict if its own checks were clean, so one real person counts once. Full rules: [`contracts/scoring.md`](contracts/scoring.md).

Speech-to-text covers English and Hindi, Gujarati, Marathi, Bengali and Odia, including code-mixed Hinglish.

## Architecture

```
Founder's site ──embed.js──▶ widget iframe (Next.js on Vercel)
                                  │ email · voice answer · device id
                                  ▼
                 FastAPI backend (Docker, nginx, HTTPS) ──────▶ Supabase
                   │ background scoring:                          Postgres · pgvector · Storage
                   │ ffmpeg → speech-to-text → pain LLM →         │
                   │ voice match → fraud checks → verdict         ▼ Realtime
                   ├──▶ TigerGraph Savanna (fake-ring detection)  Founder dashboard,
                   └──▶ viaSocket webhook (founder alerts)        public report, badge

Dodo Payments ──signed webhook──▶ Next.js API ──▶ deposit marked paid
```

## Tech stack

| Area | Technology |
|---|---|
| Web app, widget, dashboard | Next.js 16, TypeScript, Tailwind CSS, Vercel |
| Backend and scoring | Python 3.11, FastAPI, ffmpeg, Docker |
| Speech-to-text | Smallest.ai Pulse (Sarvam and OpenAI as fallbacks) |
| Pain scoring and answer similarity | OpenAI GPT-5-nano, text-embedding-3-small |
| Voice fingerprint | SpeechBrain ECAPA-TDNN (192-dimensional speaker embeddings) |
| Database, auth, storage, live updates | Supabase (Postgres, pgvector, Storage, Realtime, magic-link login) |
| Fake-ring detection | TigerGraph Savanna, GSQL |
| Deposits and Pro plan | Dodo Payments |
| Founder alerts | viaSocket |

**Hackathon partners used:** AI Grants India (OpenAI and Smallest.ai credits), Dodo Payments, TigerGraph, viaSocket.

## Evidence

- **102 unit tests** for the backend (`cd backend && pytest -q`).
- **Pain-score evaluation: 20/20**, including 4/4 manipulation and keyword-stuffing attempts (`python -m tests.run_pain_eval`).
- **End-to-end against production: 26/26** checks (`python -m scripts.e2e`).
- **Attack suite of 44 attacks**, including AI voices, voice changers, replays, copied and paraphrased scripts, prompt injection, junk audio, email aliases and floods: 40 caught, 3 measured as known limits ([`backend/docs/fraud_report.md`](backend/docs/fraud_report.md)).
- **Human tests**: one person signing up 8 times across a laptop, a phone, a speaker replay, a disguised voice, Hindi and an AI voice was reduced to one verified human.
- **Voice threshold** calibrated on real human pairs, an AI clone and synthetic voices ([`backend/docs/voice_calibration.md`](backend/docs/voice_calibration.md)).

## Known limitations

We publish these rather than overclaim:

- **Paid real people** answering in their own words, on their own devices and networks, are hard to tell apart from genuine users. Deposits are the main defence.
- **AI voices played through a speaker,** or with added noise, are not detected as AI. They are caught only when they match an earlier signup's voice, reuse an answer or share a device. Open-source deepfake detectors were too unreliable to use (about 43% error on real-world audio; see [`backend/docs/ai_voice.md`](backend/docs/ai_voice.md)).
- **Strong voice changers** can lower voice similarity below the match threshold.
- **Device and network signals are weak:** browser fingerprints can be reset, and mobile data or a VPN changes the network.
- **Speech-to-text errors** on fast or accented speech can lower a pain score or hide a copied answer.

## Running locally

```bash
# Backend (Python 3.11, ffmpeg)
cd backend
python3.11 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env          # fill in Supabase, OpenAI and Smallest.ai keys
.venv/bin/uvicorn app.main:app --reload --port 8000

# Web app (Node 20+)
cd web
npm install
cp .env.example .env.local    # fill in Supabase, backend URL and Dodo keys
npm run dev
```

Database schema: run the files in [`contracts/migrations/`](contracts/migrations) in order in the Supabase SQL editor.
TigerGraph setup: `python -m scripts.tg_setup`. Backend deployment: [`backend/docs/deploy_hostinger.md`](backend/docs/deploy_hostinger.md).

## Repository layout

| Folder | Contents |
|---|---|
| [`backend/`](backend) | FastAPI service: signup intake, speech-to-text, pain scoring, voice fingerprint, fraud checks, TigerGraph |
| [`web/`](web) | Next.js app: founder dashboard, signup widget, public report and badge, payments, alerts |
| [`contracts/`](contracts) | Shared definitions: database migrations, API, scoring rules, events, environment variable names |
| [`docs/`](docs) | Product idea, build plans, verified tool notes |

## Team

- **Ayush Raj**: backend, scoring and fraud detection
- **Hardik Shreyas**: web app, dashboard, payments and launch

Follow the project on X: [@proofodemand](https://x.com/proofodemand).
