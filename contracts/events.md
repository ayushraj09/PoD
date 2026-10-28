# Events (owner: A)

## `signup.scored`

When a signup reaches `scored`, the backend sends `POST NOTIFY_WEBHOOK_URL` (a viaSocket webhook set up by B), only if the variable is set. 5 s timeout; failures are logged and never block scoring.

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
