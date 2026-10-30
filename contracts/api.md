# Backend API (owner: A)

Base URL: `BACKEND_URL` (Render).

## `POST /v1/signups` (multipart form, called by the widget)

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
- `409 {"error": "already_signed_up", "signup_id": "..."}`, also when the email is an alias of an
  earlier signup's inbox (`+tags`, and dots for Gmail/Googlemail)
- `429 {"error": "rate_limited"}` (more than 10 signups per IP per hour per waitlist)

## `GET /v1/signups/{id}/status`

→ `{"status", "human_verdict", "pain_score"}`. The widget may poll this to show "You're verified ✓".

## `GET /health`

→ `{"ok": true, "models_loaded": true}`

## CORS

Allow only `WEB_ORIGIN`. The widget runs inside an iframe on B's domain, so founders' sites never call the backend directly.
