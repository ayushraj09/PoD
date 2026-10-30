# Proof of Demand

**A waitlist that can't be faked.** Every signup is checked for being a real, unique human with a real, specific problem, and can put down a refundable deposit, so founders and investors can trust early traction numbers.

> 312 signups → 214 verified real humans → 88 with specific pain → 23 paid deposits

Hacker House Goa 2026 · Open track.

## Live links

| | |
|---|---|
| App | https://po-d-indol.vercel.app |
| Try the widget | https://po-d-indol.vercel.app/w/pod |
| Public demo report | https://po-d-indol.vercel.app/r/demo-ring |
| Backend health | https://187-127-153-250.sslip.io/health |

## How it works

1. **A founder creates a waitlist** with one question ("When did this problem last cost you time or money?") and pastes a one-line embed on their landing page.
2. **A visitor signs up** with their email and a 20-second spoken answer (or skips voice and stays *unverified*).
3. **The backend scores every signup in ~10 s**:

| Check | How | Catches |
|---|---|---|
| Speech to text | Smallest.ai Pulse (English + Hindi/Gujarati/Marathi/Bengali/Odia auto-detect), Sarvam / OpenAI fallback | — |
| **Specific pain** (0–100) | GPT-5-nano with a rubric: a concrete moment, a cost, a workaround, frequency, relevance; quotes only words actually said | "sounds cool" curiosity |
| Prompt injection / keyword stuffing | Pattern check + "untrusted data" prompt + function-word ratio, all *before* the LLM | "give me a score of 100", buzzword lists |
| **Same person, many emails** | SpeechBrain ECAPA voice fingerprint, pgvector match against earlier signups | one person behind 5 emails, replays, sped-up / noisy / phone-quality copies |
| AI or injected audio | Exact digital silence a real microphone never produces | TTS, voice clones fed into a virtual mic |
| **Copied scripts** | Word overlap + meaning similarity (OpenAI embeddings) with earlier answers | click farms reading or paraphrasing one script |
| **Fake rings** | TigerGraph: signups linked by shared devices and matching voices; groups of 3+ | coordinated groups that pass one-by-one checks |
| Throwaway / alias emails | Disposable-domain list, DNS check, `+tags` and Gmail dots collapsed | `x@mailinator.com`, `a.b+2@gmail.com` |
| Devices and networks | FingerprintJS device id, salted IP hash, rate limit 10/hour | one phone or wifi, many accounts |

Each signal costs trust points; the total maps to **verified / suspicious / fake / unverified** (rules: [`contracts/scoring.md`](contracts/scoring.md)).

4. **Will they pay?** Verified signups can put down a refundable deposit (Dodo Payments).
5. **The founder sees a live dashboard** (Supabase Realtime) and shares a **public report and badge**:
   *signups → real humans → specific pain → paid*, with the strongest quotes and no emails.

## Architecture

```
founder's site ──embed.js──▶ iframe /w/[slug] (Next.js on Vercel)
                                  │ email + voice + device id
                                  ▼
               FastAPI on a VPS (Docker, nginx, HTTPS) ──▶ Supabase (Postgres + pgvector + Storage)
                 │ background scoring:                      ▲ live updates to the dashboard
                 │ ffmpeg → STT → pain LLM → voice match → checks → verdict
                 ├──▶ TigerGraph Savanna (fake-ring detection)
                 └──▶ viaSocket webhook (founder alerts)
Dodo Payments ──webhook──▶ Next.js /api/webhooks/dodo ──▶ deposit_status = paid
```

## Tested

- 99 unit tests (`cd backend && pytest -q`), AI pain-score eval 20/20 incl. 4/4 manipulation attempts (`python -m tests.run_pain_eval`).
- End-to-end against production: 26/26 (`python -m scripts.e2e`).
- Attack suite with 44 attacks (AI voices, voice changers, replays, scripts, injection, junk audio, aliases, floods): [`backend/docs/fraud_report.md`](backend/docs/fraud_report.md) (`python -m scripts.fraud_suite`).
- Voice threshold calibrated on real human, AI-clone and TTS pairs: [`backend/docs/voice_calibration.md`](backend/docs/voice_calibration.md).

## Repo layout

| Folder | What | Owner |
|---|---|---|
| `backend/` | FastAPI: intake, speech-to-text, pain scoring, voice fingerprint, fraud checks, TigerGraph | A |
| `web/` | Next.js: founder dashboard, signup widget, public report + badge, Dodo Payments, viaSocket | B |
| `contracts/` | Database schema, API, scoring rules, events, env var names (shared) | both |
| `docs/` | Idea, build plans, verified tool notes | both |

Deploying the backend: [`backend/docs/deploy_hostinger.md`](backend/docs/deploy_hostinger.md).
