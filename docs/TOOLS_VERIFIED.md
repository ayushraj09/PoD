# Proof of Demand: Tool Guide (verified)

Checked on **29 Oct 2026** against each tool's official docs, plus a few clearly labelled secondary sources.

- **Verified**: confirmed in a source linked in that section.
- **Unverified**: I could not confirm it. Test it yourself before relying on it.
- Nothing in this file is from memory alone.

---

## 0. What changed in the plans after checking

| Change | Why |
|---|---|
| **AI-voice detector (AASIST) removed** | On real-world deepfake audio it is wrong ~43% of the time, close to a coin flip (section 9). |
| **Sarvam model changed to `saaras:v3`** | Sarvam's docs carry a deprecation notice for `saarika:v2.5`. Their REST endpoint also accepts **max 30 s** of audio. |
| **Device check weight lowered (−30 → −20)** | Open-source FingerprintJS is only 40–60% accurate, and v4's licence allows prototypes only (section 16). |
| **Client IP read from `True-Client-IP` first** | Render appends to `X-Forwarded-For` without clearing it, so visitors can fake it (section 12). |
| **Render RAM made explicit** | Free and Starter have 512 MB; Standard has 2 GB. Measure before choosing. |
| **TigerGraph free tier behaviour added** | Free workspaces always auto-stop; the first request after idle is not queued, so retry. |
| **Dodo calls made exact** | Checkout sessions, metadata, Standard Webhooks, refunds, test cards (section 1). |

---

## Quick verdict

| Tool | Our use | Verdict |
|---|---|---|
| Dodo Payments | Refundable deposits, Pro plan | ✅ Everything we need exists |
| viaSocket | Alerts to Slack / Sheets / email | ✅ Webhook trigger + actions exist |
| TigerGraph Savanna | Fake-ring detection | ✅ Works; free tier auto-stops |
| AI Grants India | Model and voice credits | ✅ Apply today; most decisions in ~48 h |
| Wispr Flow | Team dictation only | ➖ Not in the product |
| Sarvam speech-to-text | Voice → text | ✅ 30 s limit per request |
| OpenAI transcription | Fallback voice → text | ✅ 25 MB limit |
| OpenAI structured output | Pain score as JSON | ✅ `json_schema` format |
| SpeechBrain ECAPA | Voice fingerprint | ✅ 192 numbers per voice |
| AASIST | AI-voice detection | ❌ **Dropped** |
| email-validator | Email syntax + domain check | ✅ |
| disposable-email-domains | Throwaway email list | ✅ |
| FastAPI BackgroundTasks | Scoring after response | ✅ Lost if the server restarts |
| Render | Backend hosting | ✅ Watch RAM and cold starts |
| Hugging Face Spaces | Alternative host | ❌ Docker Spaces need a paid plan |
| Supabase | Database, login, files, live updates | ✅ Two common gotchas noted |
| Vercel | Frontend hosting | ✅ |
| MediaRecorder | Recording in browser | ✅ Check format per browser |
| iframe `allow="microphone"` | Mic inside embed | ✅ Some site builders strip it |
| FingerprintJS | Device id | ⚠️ Prototype licence, 40–60% accurate |
| Claude Code | Building | ✅ All features used in the plans exist |

---

## 1. Dodo Payments (deposits + Pro plan): owner B

**Verified facts**
- **Checkout sessions:** created with a product cart, optional prefilled customer, `return_url` and custom `metadata`. The response gives `checkout_url` and `session_id`. Products must be created in the Dodo dashboard first.
- **Session lifetime:** 24 hours by default.
- **Test mode:** the client takes `environment: 'test_mode'` (default is live). Test-mode API base is `test.dodopayments.com`.
- **Metadata:**
  - Supported on payments.
  - Included in webhook events.
  - Limits: keys up to 40 characters, values up to 500 characters, up to 50 pairs per object.
- **Webhooks:**
  - Follow the Standard Webhooks spec (HMAC SHA256 signatures).
  - Create the endpoint in the dashboard under **Developer → Webhooks**.
  - Events include `payment.succeeded`, `payment.failed`, `refund.succeeded`.
  - Dodo retries failed deliveries.
- **Refunds:** `POST /refunds` with `payment_id` (required), plus optional `items` (for refunding single items), `reason`, `metadata`.
- **Test card:** `4242 4242 4242 4242`, expiry `06/32`, CVC `123`. Works in test mode only.
- **Dodo CLI:** `dodo wh listen` forwards live test webhooks to your local server; `dodo wh trigger` sends mock events.
- **Next.js adaptor:** `@dodopayments/nextjs` provides ready `Checkout` and `Webhooks` route handlers. The framework adaptors expose handlers such as `onPaymentSucceeded` and `onRefundSucceeded`, and the webhook handler verifies the signature for you (returns 401 if invalid).

**How to use (Next.js server code)**
```ts
import DodoPayments from 'dodopayments';

const dodo = new DodoPayments({
  bearerToken: process.env.DODO_API_KEY!,
  environment: 'test_mode',
});

// POST /api/deposit
const session = await dodo.checkoutSessions.create({
  product_cart: [{ product_id: process.env.DODO_DEPOSIT_PRODUCT_ID!, quantity: 1 }],
  customer: { email },                                   // prefill
  return_url: `${process.env.NEXT_PUBLIC_SITE_URL}/w/${slug}?deposit=done`,
  metadata: { signup_id },                               // comes back in the webhook
});
return Response.json({ checkout_url: session.checkout_url });
// Widget: window.open(checkout_url, '_blank')  (Dodo's own example opens a new window)

// Refund button
await dodo.refunds.create({ payment_id, reason: 'Waitlist deposit refund' });
```

Webhook route without the adaptor (Dodo's docs point to the `standardwebhooks` library):
```ts
import { Webhook } from 'standardwebhooks';
const wh = new Webhook(process.env.DODO_WEBHOOK_SECRET!);

export async function POST(req: Request) {
  const raw = await req.text();                       // raw body is needed for the signature
  const headers = Object.fromEntries(req.headers);
  let event;
  try { event = wh.verify(raw, headers) as any; }
  catch { return new Response('bad signature', { status: 401 }); }
  if (event.type === 'payment.succeeded') { /* set deposit_status = 'paid' */ }
  if (event.type === 'refund.succeeded')  { /* set deposit_status = 'refunded' */ }
  return new Response('ok');
}
```

**Watch out**
- **Where `metadata` sits in the webhook body differs between Dodo's own examples.** One reads `event.data.object.metadata`, Dodo's Supabase starter reads `event.data.metadata`. Log one real test payload and read it from where it actually is.
- **Unverified:** refund time window and whether refunds need a positive Dodo balance (only a third-party SDK wiki says so). Check the dashboard or ask Dodo's team at the event.
- **Unverified:** whether Dodo's terms allow you to collect deposits for *other* founders' products. That's why the plans keep other teams in test mode.

Sources: [Checkout sessions](https://docs.dodopayments.com/developer-resources/checkout-session.md) · [Webhooks](https://docs.dodopayments.com/developer-resources/webhooks) · [Metadata](https://docs.dodopayments.com/api-reference/metadata.md) · [Create refund](https://docs.dodopayments.com/api-reference/refunds/post-refunds.md) · [Testing](https://docs.dodopayments.com/miscellaneous/testing-process) · [Next.js adaptor](https://docs.dodopayments.com/developer-resources/nextjs-adaptor.md) · [Express adaptor](https://docs.dodopayments.com/developer-resources/express-adaptor) · [FastAPI boilerplate](https://docs.dodopayments.com/developer-resources/fastapi-boilerplate.md) · [Dodo Supabase starter schema](https://www.mintlify.com/dodopayments/dodo-supabase-subscription-starter/api/schema-payments)

---

## 2. viaSocket (alerts to founders): owner B

**Verified facts**
- **Flow structure:** every flow (workflow) has exactly one trigger. A trigger can be a **Webhook** (an outside system sends data to your viaSocket URL), a schedule, or an event in a connected app.
- **Conditions:** inside the trigger, **"Run flow if"** runs the flow only when the data meets conditions. Use it to alert only on `human_verdict = verified`.
- **Actions:** e.g. Slack **Send Channel Message**, Google Sheets **Add a Row**. You map fields from the trigger data into them.
- **Usage counting:** each action counts as one invocation; the trigger doesn't.
- **Hackathon perks (from the event deck):** coupon `HHGOA26-VIASOCKET` at viasocket.com; an extended-plan code is in the builder group; the top 3 on the viaSocket track get 12 months free.

**How to use**
1. Create New Flow → Trigger: **Webhook** → copy the URL → give it to A as `NOTIFY_WEBHOOK_URL`.
2. Send one test event from the backend so viaSocket learns the fields (`human_verdict`, `pain_score`, `pain_quote`, …).
3. Add "Run flow if" `human_verdict` equals `verified`.
4. Add actions: Slack → Send Channel Message; Google Sheets → Add a Row.
5. Set the flow live.

Sources: [Trigger help](https://viasocket.com/help/workflow/trigger) · [Basics + invocations](https://viasocket.com/faq/basic-of-viasocket) · [Quickstart](https://viasocket.com/faq/quickstart) · [First flow walkthrough](https://app.productlift.dev/f/knowledgebase/viasocket-integration)

---

## 3. TigerGraph Savanna (fake-ring detection): owner A

**Verified facts**
- **Free plan limits:**
  - max size TG-4
  - 1 read-write workspace
  - suspend grace 0 days, terminate grace 7 days
  - auto-stop is **enforced** for free-tier workspaces
  - free credits exist, and Savanna shows their expiry date
- **Auto-resume:** if on, the first request to an idle workspace starts it but **is not queued**, so keep retrying until it succeeds.
- **GSQL editor:** Savanna has a GSQL query editor (GraphStudio-style).
- **Connecting from Python (cloud):** host, graph name and a **secret**. Create the secret in the Admin Portal (My Profile → +). Then call `getToken(secret)`.
- **pyTigerGraph write and query calls:**
  - `upsertVertex(vertexType, vertexId, attributes)` creates or updates one point
  - `upsertEdge(sourceVertexType, sourceVertexId, edgeType, targetVertexType, targetVertexId, attributes)` creates or updates one link
  - `runInstalledQuery(name, params)` runs an installed query
- **Algorithm library:** TigerGraph's open-source graph algorithm library includes `tg_wcc` (weakly connected components: groups everything that's linked together).

**How to use**
```python
from pyTigerGraph import TigerGraphConnection
conn = TigerGraphConnection(host=TG_HOST, graphname=TG_GRAPH, gsqlSecret=TG_SECRET)
conn.getToken(TG_SECRET)

conn.upsertVertex("Signup", signup_id, {"waitlist": slug, "verdict": verdict})
conn.upsertVertex("Device", device_id, {})
conn.upsertEdge("Signup", signup_id, "USED_DEVICE", "Device", device_id, {})
groups = conn.runInstalledQuery("tg_wcc", {...})   # params depend on the query version you install
```

**Watch out**
- **Unverified:** the exact steps to install `tg_wcc` on Savanna, and its parameter names for the version you get. Open the query file from the library first and read its parameters.
- Wrap every call in try/except with retries. The free workspace will be asleep sometimes.

Sources: [Savanna quota policy](https://www.tigergraph.com/docs/savanna/main/resources/quota_policy) · [Savanna release notes](https://www.tigergraph.com/docs/savanna/main/overview/release-notes) · [Workspace auto-suspend/resume](https://docs.tigergraph.com/cloud4/main/workgroup-workspace/workspaces/settings) · [pyTigerGraph connection](https://docs.tigergraph.com/pytigergraph/current/getting-started/connection) · [pyTigerGraph vertex functions](https://docs.tigergraph.com/pytigergraph/1/core-functions/vertex) · [pyTigerGraph (PyPI, upsertEdge)](https://pypi.org/project/pyTigerGraph/0.0.5.4/) · [Graph algorithm library](https://docs.tigergraph.com/graph-algorithm-library) · [Library on GitHub (tg_wcc list)](https://github.com/billshitg/gsql-graph-algorithms)

---

## 4. AI Grants India (credits): owner A applies

**Verified facts**
- **Who can apply:** anyone in India seriously building with AI, including students and hackathon teams. No registered company needed.
- **Process:** one short form; most decisions in about 48 hours.
- **Credits (from the event deck):** $10,000 across GPU and voice credits, NVIDIA open-weight models and OpenAI API credits; apply at aigrants.in.

**Watch out**
- **Unverified:** which exact models and voice providers are included. Until approved, use any free trial credits from Sarvam or OpenAI so you're not blocked.

Source: [AI Grants India summary page](https://grantedai.com/grants/ai-grants-india-ai-grants-india-6a4edf9c) · event deck slide 14

---

## 5. Wispr Flow: team use only

- Voice dictation in any app (from the event deck). The deck offers 1 month of Pro free.
- It has no part in the product. Use it to dictate prompts, docs and the pitch script.

---

## 6. Sarvam speech-to-text: owner A

**Verified facts**
- **Endpoint:** `POST https://api.sarvam.ai/speech-to-text`, header `api-subscription-key`, multipart form with `file` and `model`.
- **30-second cap:** the real-time REST endpoint accepts **max 30 s** of audio. Longer audio needs the Batch API.
- **Formats:** WAV, MP3, AAC, AIFF, OGG, OPUS, FLAC, MP4, AMR, WMA, WebM (auto-detected). PCM only at 16 kHz.
- **Models:** `saarika:v2.5` has a **deprecation notice**. For automatic language detection, the docs point to `saaras:v3` with `mode="transcribe"`.
- **Python SDK:** `sarvamai`. The response includes `transcript` and `language_code`.
- **Rate limits:** Starter plan 60 requests/min.
- **Keys:** Sarvam's docs say not to ship the API key in browser code. Call it from your backend, which the plan already does.

**How to use**
```python
from sarvamai import SarvamAI
client = SarvamAI(api_subscription_key=SARVAM_API_KEY)
with open(wav_path, "rb") as f:
    r = client.speech_to_text.transcribe(file=f, model="saaras:v3", mode="transcribe")
text, lang = r.transcript, r.language_code
```

**Watch out**
- **Unverified:** the exact fields on the `saaras:v3` response object in your SDK version. Print one response before relying on field names.

Sources: [Saarika model page](https://docs.sarvam.ai/api/models/saarika) · [STT FAQ (limits, formats)](https://docs.sarvam.ai/api/speech-to-text/faq) · [Saarika (deprecation, examples)](https://docs.sarvam.ai/api-reference-docs/getting-started/models/saarika.md) · [REST API guide](https://docs.sarvam.ai/api-reference-docs/api-guides-tutorials/speech-to-text/rest-api)

---

## 7. OpenAI transcription + structured output: owner A

**Verified facts**
- **Transcription endpoint:** `/v1/audio/transcriptions`.
  - Files up to 25 MB; formats mp3, mp4, mpeg, mpga, m4a, wav, webm.
  - Recommended model is `gpt-transcribe`; `gpt-4o-transcribe` and `gpt-4o-mini-transcribe` still work.
- **Structured output:** `response_format = {"type": "json_schema", "json_schema": {"name": ..., "strict": true, "schema": {...}}}` makes the reply follow your JSON schema. (Described as the OpenAI standard format in Vercel's gateway docs.)

**How to use**
```python
tr = client.audio.transcriptions.create(model="gpt-4o-transcribe", file=open(wav_path, "rb"))
text = tr.text

resp = client.chat.completions.create(
    model=LLM_MODEL, temperature=0,
    messages=[{"role": "system", "content": RUBRIC},
              {"role": "user", "content": f"<transcript>{text}</transcript>"}],
    response_format={"type": "json_schema", "json_schema": {
        "name": "pain_score", "strict": True,
        "schema": {"type": "object", "additionalProperties": False,
                   "required": ["pain_score", "pain_reason", "pain_quote"],
                   "properties": {"pain_score": {"type": "integer"},
                                  "pain_reason": {"type": "string"},
                                  "pain_quote": {"type": "string"}}}}})
```

Sources: [OpenAI speech-to-text guide](https://developers.openai.com/api/docs/guides/speech-to-text) · [OpenAI speech-to-text (models, limits)](https://developers.openai.com/docs/guides/speech-to-text) · [Vercel: structured outputs (OpenAI format)](https://vercel.com/docs/ai-gateway/sdks-and-apis/openai-chat-completions/structured-outputs)

---

## 8. SpeechBrain ECAPA voice fingerprint: owner A

**Verified facts**
- **Model:** `speechbrain/spkrec-ecapa-voxceleb` produces **192-number** speaker embeddings ("voice fingerprints").
- **Loading:** `EncoderClassifier.from_hparams(source=..., savedir=...)`, then `encode_batch(signal)`.
- **Import path:** newer versions use `speechbrain.inference.speaker` (or `speechbrain.inference.classifiers`); older ones use `speechbrain.pretrained`.
- **Audio:** expects 16 kHz audio. Common practice is to normalise the vector to length 1 before comparing.

**How to use**
```python
from speechbrain.inference.speaker import EncoderClassifier
import torchaudio, torch.nn.functional as F
enc = EncoderClassifier.from_hparams(source="speechbrain/spkrec-ecapa-voxceleb",
                                     savedir="models/ecapa", run_opts={"device": "cpu"})
sig, sr = torchaudio.load(wav16k_path)            # must be 16000
emb = F.normalize(enc.encode_batch(sig), dim=-1).squeeze().tolist()   # 192 floats
```

**Watch out**
- **Unverified:** the right "same person" cutoff for your microphones and rooms. That's why stage A5 calibrates it on real recordings.

Sources: [HF example: 192-dim ECAPA](https://huggingface.co/spaces/NicolasDenier/speech-to-speech-translation/blame/main/xvector-generator.py) · [HF handler example (CPU, encode_batch)](https://huggingface.co/sanoramyun8/speaker-embedding-endpoint/blob/main/handler.py) · [HF embedder (import paths)](https://huggingface.co/spaces/ConvxO2/Who-Spoke-When/blob/main/models/embedder.py)

---

## 9. AASIST (AI-voice detection): **dropped**

**Verified facts**
- **Origin:** official repo `clovaai/aasist` (MIT licence), trained on ASVspoof 2019 LA. In-domain error rate is 0.83%.
- **Real-world performance:** on the public Speech Anti-Spoofing Arena, AASIST's error rate on **In-the-Wild** deepfake audio is **43.01%**, and AASIST-L is **44.45%**. That's close to guessing.
- **Second opinion:** another model mirror notes it "generalises poorly to modern in-the-wild deepfake audio".

**Decision:** don't ship it. A wrong "fake" label on a real person is worse than missing a fake.

Sources: [AASIST official repo](https://github.com/clovaai/aasist) · [AASIST arena scores](https://huggingface.co/SpeechAntiSpoofingBenchmarks/AASIST) · [AASIST-L arena scores](https://huggingface.co/SpeechAntiSpoofingBenchmarks/AASIST-L) · [Verity checkpoint note](https://huggingface.co/ADPer/verity-weights)

---

## 10. email-validator + disposable-email-domains: owner A

**Verified facts**
- **email-validator:**
  - `pip install email-validator`
  - `validate_email(email, check_deliverability=True)` raises `EmailNotValidError` with a readable message, or returns an object with `.normalized`
  - Deliverability checks (DNS) are recommended for first-time signups
  - `caching_resolver(timeout=10)` caches DNS lookups
- **disposable-email-domains:**
  - `pip install disposable-email-domains` → `from disposable_email_domains import blocklist` → `'domain.com' in blocklist`
  - The list holds **second-level domains only**, so `user@mail.xyz.com` must be checked as `xyz.com`

**How to use**
```python
from email_validator import validate_email, EmailNotValidError, caching_resolver
from disposable_email_domains import blocklist
resolver = caching_resolver(timeout=5)
info = validate_email(email, check_deliverability=True, dns_resolver=resolver)
email = info.normalized
domain2 = ".".join(email.split("@")[1].lower().split(".")[-2:])
is_disposable = domain2 in blocklist
```

Sources: [email-validator (PyPI)](https://pypi.org/project/email-validator) · [email-validator README](https://github.com/JoshData/python-email-validator) · [disposable-email-domains README](https://github.com/mattyatea/disposable-email-domains)

---

## 11. FastAPI BackgroundTasks: owner A

**Verified facts**
- Add a `BackgroundTasks` parameter to a route and call `background_tasks.add_task(fn, args...)`. The function runs **after the response is sent**.
- It runs inside the web process, so **the task is lost if the instance restarts**.

**What this means for us:** on startup, re-queue any signup still in `pending` or `processing`. Never leave a row stuck.

Sources: [FastAPI docs](https://fastapi.tiangolo.com/tutorial/background-tasks/) · [Sevalla FastAPI background tasks (restart caveat)](https://docs.sevalla.com/guides/python/fastapi/background-tasks.md)

---

## 12. Render (backend hosting): owner A

**Verified facts**
- **Docker:** Render builds from your `Dockerfile` (Docker runtime). Needed for ffmpeg.
- **Root Directory:** for a monorepo, set it to `backend`; build and start commands run from there. Render redeploys on every push to the chosen branch.
- **Instance sizes:**
  - Free: 512 MB RAM / 0.1 CPU
  - Starter: 512 MB / 0.5 CPU
  - Standard: 2 GB / 1 CPU
- **Free cold starts:** free web services spin down after 15 minutes idle; the next request waits while it starts.
- **Client IP:** Render sits behind Cloudflare. Its proxy **appends** to `X-Forwarded-For` without clearing it, so that header can be faked. Read `True-Client-IP` / `CF-Connecting-IP` first.
- **Price (third-party listing):** Standard is $25/month. Check render.com/pricing.

**How to use**
- After the voice model loads, run the container locally and check `docker stats`. If memory is over ~450 MB, choose Standard.
- Keep a free uptime ping on `/health` during demo hours if you stay on Free.

Sources: [Render docs (llms-full)](https://render.com/llms-full.txt) · [Your first deploy (Root Directory)](https://render-web.app.render.com/docs/your-first-deploy) · [Render feedback: X-Forwarded-For](https://feedback.render.com/features/p/send-the-correct-xforwardedfor) · [True-Client-IP on Render](https://hn.jakechampion.name/reader/https://rohitpaulk.com/articles/render-rails-remote-ip) · [Price listing (third-party)](https://kuberns.com/blogs/how-to-deploy-on-render/)

**Considered and rejected: Hugging Face Spaces.** Free CPU Basic hardware is 2 vCPU / 16 GB, but **creating a Docker Space needs a paid plan** (PRO). Use it only if one of you already has PRO. ([HF Spaces overview](https://huggingface.co/docs/hub/en/spaces-overview))

---

## 13. Supabase (database, login, files, live updates): owners A + B

**Verified facts**
- **Live updates (Realtime):**
  - Realtime is off by default. Add the table to the `supabase_realtime` publication (Dashboard → Database → Publications, or `alter publication supabase_realtime add table signups;`).
  - **Row-level security silently drops events** the viewer isn't allowed to read. No error, just nothing arrives.
  - Supabase notes Postgres Changes is simpler but scales less well than Broadcast. Fine for us.
- **Vectors (pgvector):**
  - `<=>` is cosine **distance** (similarity = 1 − distance).
  - The client library can't use vector operators directly, so wrap the query in a SQL function and call it with `.rpc()`.
- **Storage:**
  - Private buckets deny unauthenticated access.
  - The **service role key bypasses RLS** and must stay on the server.
  - Use `createSignedUrl` for temporary access to a private file.
- **Magic-link login:** enable the Email provider (Authentication → Providers → Email), call `signInWithOtp({ email, options: { emailRedirectTo } })`, and add a `/auth/callback` route that exchanges the code for a session. Use `@supabase/ssr` (`createServerClient` / `createBrowserClient`) in Next.js App Router.

**How to use (dashboard live updates)**
```ts
supabase.channel(`signups-${waitlistId}`)
  .on('postgres_changes',
      { event: '*', schema: 'public', table: 'signups', filter: `waitlist_id=eq.${waitlistId}` },
      (payload) => upsertRow(payload.new))
  .subscribe();
```

**Watch out**
- **Unverified:** Supabase's built-in email sender has a low hourly limit. If magic links stop arriving during onboarding, set up custom SMTP (Authentication → SMTP Settings) or sign founders in yourselves during the demo.

Sources: [Realtime: Postgres changes](https://supabase.com/docs/guides/realtime/postgres-changes.md) · [Realtime troubleshooting](https://supabase.com/kb/troubleshooting/realtime-postgres-changes-troubleshooting) · [Vector columns](https://supabase.com/docs/guides/ai/vector-columns) · [Semantic search operators](https://supabase.com/docs/guides/ai/semantic-search.md) · [Securing storage (tutorial)](https://www.rapidevelopers.com/md/supabase-tutorial/how-to-secure-supabase-storage-files) · [Magic link (tutorial)](https://www.rapidevelopers.com/supabase-tutorial/how-to-enable-magic-link-login-in-supabase)

---

## 14. Vercel (frontend hosting): owner B

**Verified facts**
- **Root Directory:** set it to `web` per project.
- **Skipping unchanged projects:** "Skip unaffected projects" relies on a JavaScript workspaces monorepo. Our repo isn't one, so Vercel will rebuild `web/` on every push. Harmless.

Sources: [Vercel monorepos](https://vercel.com/docs/monorepos) · [Changelog: skip unaffected](https://vercel.com/changelog/automatically-skip-unnecessary-deployments-in-monorepos)

---

## 15. Browser recording (MediaRecorder) + microphone in an iframe: owner B

**Verified facts**
- **Pick a format per browser:** use `MediaRecorder.isTypeSupported()` and never hardcode.
  - Chrome / Edge / Firefox: `audio/webm;codecs=opus`
  - Safari 14.1–18.3: **mp4 only**
  - Safari 18.4+: also webm
- **HTTPS only:** `getUserMedia()` works only on secure (HTTPS) pages.
- **Mic inside an iframe:** a cross-origin iframe can use the mic **only if** the embedding page grants it: `<iframe ... allow="microphone">`.
- **Site builders:** some builders put embeds inside their own iframe without that permission. This was reported for Wix in 2020, so recording fails there. Always show the direct `/w/[slug]` link as a fallback.

**How to use**
```js
const types = ['audio/webm;codecs=opus', 'audio/mp4', 'audio/ogg;codecs=opus'];
const mimeType = types.find(t => MediaRecorder.isTypeSupported(t)) || '';
const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
const rec = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
```

Sources: [MDN getUserMedia (Permissions Policy, iframes, HTTPS)](https://developer.mozilla.org/en-US/docs/Web/API/MediaStreamConstraints) · [Chromium: permissions in cross-origin iframes](https://chromium.org/Home/chromium-security/deprecating-permissions-in-cross-origin-iframes) · [MediaRecorder Safari formats](https://www.testmuai.com/web-technologies/mediarecorder/) · [Wix iframe note (2020)](https://blog.addpipe.com/camera-and-microphone-access-in-cross-oirigin-iframes-with-feature-policy/)

---

## 16. FingerprintJS (device id): owner B, **weak signal only**

**Verified facts**
- **Licence:** from **v4.0.0, FingerprintJS uses the Business Source License**. Proof-of-concept use is allowed; revenue-generating apps and SaaS need a commercial licence.
- **Accuracy:** only **40–60%**, because it runs entirely in the browser. Fingerprints can be spoofed.
- **Usage:** `npm i @fingerprintjs/fingerprintjs` → `const fp = await FingerprintJS.load(); const { visitorId } = await fp.get();`. Ad blockers may block the CDN version; the npm package avoids that.

**What this means for us:** fine for the hackathon prototype. It's only a small penalty in the score. Before charging money, buy a licence, switch provider, or drop it.

Sources: [FingerprintJS README (BSL table)](https://github.com/alexandrethsilva/fingerprintjs) · [Accuracy 40–60%](https://github.com/xbl-tech/fingerprintjs) · [npm package](https://npmjs.com/package/@fingerprintjs/fingerprintjs)

---

## 17. Claude Code (how you both build): both

**Verified facts**
- **Settings files:** `.claude/settings.json` (shared, committed) and `.claude/settings.local.json` (personal; Claude Code configures git to ignore it).
- **Rule order:** deny rules beat ask and allow rules. `/permissions` lists every rule and which file it came from.
- **Edit rules:** `Edit(...)` covers **all** file-editing tools, including Write. Path rules on `Write(...)` are ignored with a warning, so the plans use only `Edit(...)`.
- **Path patterns** (gitignore style):

  | Pattern | Means |
  |---|---|
  | `//path` | absolute path |
  | `~/path` | from your home folder |
  | `/path` | relative to the settings file / project root |
  | `path` or `./path` | relative to the folder you started Claude in |

  The plans use `./web/**` and `./backend/**`, so **always start `claude` from the repo root**.
- **Deny rules don't stop shell commands:** rules on Edit don't block shell commands. The CLAUDE.md rule covers that.
- **Custom commands:** Markdown files in `.claude/commands/` become `/name` commands. Frontmatter `description` is shown in help. `$ARGUMENTS` receives everything typed after the command. (Custom commands are now part of "skills"; both locations work.)
- **CLAUDE.md:**
  - The root `CLAUDE.md` loads every session.
  - A folder's `CLAUDE.md` loads when Claude reads files in that folder.
  - `@path` imports load other files.
  - **Imports inside code blocks are ignored.** When you copy the root CLAUDE.md template from the plan, don't keep the ``` fences around it.
- **Session controls:**
  - `Shift+Tab` cycles permission modes, including plan mode (read-only: explores and proposes, no edits). `/plan` enters it directly.
  - `/clear` starts fresh (project memory stays); `/compact` summarises the conversation; `/model` switches model.
  - `/usage` shows your plan's limits and current status.

Sources: [Permissions (IAM)](https://docs.claude.com/en/docs/claude-code/iam) · [Permissions (current docs)](https://code.claude.com/docs/ja/permissions) · [Settings](https://docs.claude.com/en/docs/claude-code/settings) · [Memory / CLAUDE.md](https://code.claude.com/docs/en/memory) · [Glossary (permission modes, commands)](https://code.claude.com/docs/en/glossary) · [Claude Code cheatsheet (support)](https://support.claude.com/en/articles/14553413-claude-code-cheatsheet) · [Edit vs Write rules](https://dev.to/rulestack/claude-code-permission-rules-how-allow-deny-and-ask-actually-match-1bj7)
