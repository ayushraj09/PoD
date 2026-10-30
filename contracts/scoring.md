# Scoring (owner: A)

## `human_verdict`

- `verified`: trust_score ≥ 70
- `suspicious`: 40–69
- `fake`: < 40
- `unverified`: no voice answer given, or scoring failed (`processing_error`); `trust_score` is null

## `pain_score`

0–100. Levels: **high** ≥ 70, **medium** 40–69, **low** < 40.

## `status`

`pending` → `processing` → `scored`. A signup whose scoring crashed still ends as `scored`, with the
`processing_error` flag and `human_verdict = unverified`. `failed` is reserved and not written in this build.

## `flags`

A JSON list of objects `{"code": "...", "detail": "..."}`. Codes:

| Code | Meaning (B shows this text in the UI) |
|---|---|
| `disposable_email` | Uses a throwaway email address |
| `repeat_device` | Same device already signed up to this waitlist |
| `repeat_ip` | Many signups from the same network |
| `same_voice` | Voice matches another signup (`detail` = that signup id) |
| `possible_ai_voice` | Voice may be AI-generated (recording has stretches of exact digital silence; `detail` = share of the clip) |
| `no_speech` | Recording has no clear speech |
| `too_short` | Answer under 3 seconds |
| `same_answer` | Answer is word-for-word the same as another signup (`detail` = that signup id) |
| `ring_member` | Part of a connected group of suspicious signups |
| `processing_error` | Scoring failed; will show as unverified |

## Trust score

Starts at 100 for a signup with a voice answer; each flag code counts once:

| Flag | Points |
|---|---|
| `same_voice` | −50 |
| `ring_member` | −40 |
| `too_short` / `no_speech` (together count once) | −40 |
| `disposable_email` | −35 |
| `same_answer` | −35 |
| `possible_ai_voice` | −30 |
| `repeat_device` | −20 |
| `repeat_ip` | −15 |

Clamped to 0–100, then mapped to `human_verdict` above.

## Funnel

Dashboard, public report and badge all use these:

1. **Signups**: all rows
2. **Real humans**: `human_verdict = 'verified'`
3. **Specific pain**: real humans with `pain_score >= 70`
4. **Paid**: `deposit_status = 'paid'`
