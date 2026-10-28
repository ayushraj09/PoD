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
| `possible_ai_voice` | Voice may be AI-generated (reserved, **not produced in this build**) |
| `no_speech` | Recording has no clear speech |
| `too_short` | Answer under 3 seconds |
| `ring_member` | Part of a connected group of suspicious signups |
| `processing_error` | Scoring failed; will show as unverified |

## Funnel

Dashboard, public report and badge all use these:

1. **Signups**: all rows
2. **Real humans**: `human_verdict = 'verified'`
3. **Specific pain**: real humans with `pain_score >= 70`
4. **Paid**: `deposit_status = 'paid'`
