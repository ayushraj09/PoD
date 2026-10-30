# Proof of Demand: a waitlist that can't be faked

**Hacker House Goa 2026 · Open track · Team of 2**

> **One-line pitch:** Waitlists lie: bots, click farms, and curious people who never pay. Proof of Demand verifies that every signup is a real human with a real, specific problem, and lets them put down a refundable deposit, so founders and investors can trust early traction numbers.

---

## 1. Problem statement

When someone builds a new product, they usually put up a "join the waitlist" page before it's ready. People type in their email, and the founder says *"500 people signed up, so people want this."* That number is then used as proof of demand with investors, accelerators, and the founder's own decision on whether to keep building.

That number is unreliable in three ways:

1. **Some signups aren't real people.** They are bots, click farms, or one person using many emails. Referral waitlists ("invite friends to move up the line") make this worse, because people create fake signups to climb the leaderboard. Waitlist vendors themselves acknowledge this.
2. **Most real signups don't care much.** Signing up costs nothing, so it mostly measures curiosity. Only about **3%** of waitlist signups become paying customers.
3. **Nobody can tell the difference from outside.** An investor sees "500 signups" with no way of knowing whether it's 500 people with a painful problem or 15 real ones plus noise.

The same issue is hurting market research more broadly. Fraud in market research surveys is estimated at **15–30%**, reaching **45%** on some platforms, and **82%** of fraudulent respondents pass standard attention checks.

**What we solve:** a believable answer to *"How many real humans actually have this problem, and how many will pay?"* before the product has any revenue.

---

## 2. What exists in the market today

| Product | Who uses it | What it does | What it doesn't do |
|---|---|---|---|
| **Waitlist tools**: Prefinery, LaunchList, Waitlister, GetWaitlist, Viral Loops | Startup founders before launch | Collect emails, run referral leaderboards, send launch emails. Prefinery alone has handled 41.7M+ signups. | Fraud protection is thin. Prefinery relies on a standard "I'm not a robot" checkbox, and Waitlister has no confirmed fraud detection. **None measure how much a signup actually needs the product.** |
| **Survey fraud tools**: Research Defender, CleanID, RelevantID | Large market research firms | Catch fake survey takers using device and network details. CleanID checks 800+ details per respondent. Research Defender reports blocking ~295M fraudulent responses in 12 months. | Built for big research firms buying paid survey panels, not founders. They check whether a device looks fake, not whether a person has a real problem or would pay. |
| **TrustMRR** | Indie founders, investors, startup buyers | Proves a startup's revenue by reading it directly from the payment provider (Stripe, Paddle, Dodo Payments and others), so numbers can't be self-reported. | **Only works after revenue exists.** A pre-revenue founder has nothing to verify. |
| **World ID** (Sam Altman's World) | Tinder, Zoom, DocuSign, Shopify and others | Proves a user is a unique human. | Strong verification needs an in-person eye scan at a special device (the "Orb"), and there are only about 1,000 across 35+ countries. It also proves only that you're human, not that you want a product. |

---

## 3. The gap we fill

There is a hole between **waitlists** (cheap, but anyone can fake them) and **TrustMRR** (trustworthy, but only after revenue). Nothing verifies **demand before revenue**, which is exactly when founders most need proof: when raising money, applying to accelerators, or deciding whether to build at all.

Proof of Demand checks three things for every signup:

| Question | How we check it | Do existing tools do this? |
|---|---|---|
| **Is this a real, unique human?** | A 20-second voice answer, checked for the same voice signing up under different emails, plus device and network checks | Waitlist tools: email checks only |
| **Do they actually have this problem?** | AI scores how specific the answer is. *"I lost 3 hours on this last Tuesday"* scores high; *"sounds cool"* scores low. | Nobody does this for waitlists |
| **Will they pay?** | An optional small refundable deposit (₹50 / $1) to reserve early access | Nobody combines this with the above |

**Output:** a shareable **"Verified Demand" report and badge**, for example:

> 312 signups → 214 verified real humans → 88 with specific pain → 23 paid deposits

Think of it as TrustMRR for founders who don't have revenue yet.

---

## 4. Approach: how it works

1. **Founder creates a waitlist** and writes one question, e.g. *"When did this problem last cost you time or money?"*
2. **Founder pastes our widget** onto their landing page.
3. **A visitor signs up** with an email plus a 20-second voice answer. Voice is optional, but verified signups get a badge and priority access.
4. **We check each signup:**
   - throwaway email and repeat-device checks
   - voice fingerprint, to catch the same person behind several emails
   - AI score for how specific and real the described problem is
5. **Optional deposit:** the signup can pay a small refundable amount to reserve their spot.
6. **Fake-ring detection:** signups are stored as a web of connections (shared devices, networks, near-identical voices or answers) to expose organised fake signups that one-by-one checks miss.
7. **Founder dashboard:** a funnel from signups to real humans to specific pain to paid, plus the strongest quotes and a public report link and badge.

---

## 5. Impact: who benefits and how

- **Founders:** find out early whether an idea has real demand, before spending months building. They get a credible number instead of a vanity count, plus real quotes describing the problem in customers' own words.
- **Investors and accelerators:** can trust early traction claims without spending time digging into every applicant's list.
- **Genuine early users:** early access goes to people who actually need the product, not to bots or people who gamed a referral leaderboard.

### Why this fits the finale judge (Davin Dong, Founder & CEO, Cookiy AI)

- Cookiy AI uses voice AI to talk to customers at scale and turn those conversations into insights a business can act on. The quality of that work depends on the people being real. Proof of Demand works on the layer underneath his business: is the person real, and is the need real?
- He led growth science at Instagram (one of its first ~100 engineers) and grew six consumer products past 100M users. Measuring what's real versus noise is central to growth work.
- It uses voice AI for something current tools don't do, not as a copy of AI interview platforms, which is already a crowded category.

---

## 6. Getting real users in 4 days

- **First users:** other teams building products here who are collecting early users. Offer it free so they can put it on their own landing pages.
- **Next:** indie founders online (Indie Hackers, Product Hunt makers, X/Twitter build-in-public founders) who already care about credible traction; that community is why TrustMRR caught on.
- **Traction to show at submission:** number of founders using it, number of signups processed, fakes caught, deposits taken.

---

## 7. Risks and how we answer them

| Risk | Our answer |
|---|---|
| **Founders may prefer a big fake number** | Our users are founders who want to stand out as credible, the same group that voluntarily lists revenue on TrustMRR. |
| **Who pays?** | Start with founders (small monthly fee via Dodo Payments). Bigger later buyers: accelerators, investors, and event organisers who want every applicant's traction verified. |
| **A voice step reduces signups** | Intended trade: fewer but believable signups. Voice is optional, and verified signups get a badge and priority. |
| **AI-generated voices** | Open-source detectors are close to a coin flip on real-world deepfakes (~43% error), so we don't use them. Same-voice matching, network and device checks, and deposits carry the weight instead. |
| **Privacy of voice recordings** | Ask clear consent, store only what's needed, and let founders delete data. |

---

## 8. Tools

### Hackathon partner tools

| Tool | Role in the product | Priority |
|---|---|---|
| **AI Grants India** ($10,000 credits) | Pays for speech-to-text and the AI that scores answers. Apply at aigrants.in early. | **Core** |
| **Dodo Payments** ($15,000 credits) | Takes the optional refundable deposit and later the founder subscription. Also one of the payment providers TrustMRR verifies. Check refund support in the docs. | **Core** |
| **TigerGraph Savanna** ($500 prize) | Graph of signups linked by shared devices, networks, voices and answers, to catch fake rings. | Strong add (TigerGraph track) |
| **Wispr Flow** | Not in the product. Use it to dictate the pitch script and docs faster. | Team use only |

### Build stack

| Part | Tool | Plain explanation |
|---|---|---|
| Signup widget | React / Next.js + browser audio recorder | The box founders paste on their page: email + 20-second voice answer |
| Backend | FastAPI (Python) | Easy to plug in the voice models |
| Speech to text | Sarvam (`saaras:v3`, max 30 s per request), or OpenAI transcription via AI Grants credits | Turns voice into text, including Indian languages |
| Same-person check | SpeechBrain speaker model (`spkrec-ecapa-voxceleb`) | Turns each voice into a "voice fingerprint"; near-identical fingerprints suggest the same person |
| Pain score | Large language model via AI Grants credits | Scores answers for specifics (a time, a cost, an existing workaround) with a one-line reason |
| Basic fake checks | `disposable-email-domains` list + FingerprintJS (free version: 40–60% accurate; licence allows prototypes only) | Blocks throwaway emails; records browser and device details to spot repeat signups |
| Database | Supabase (hosted Postgres) | Stores founders, waitlists, signups, scores |
| Dashboard and public report | Next.js | Funnel view, quotes, shareable link and badge |
| Hosting | Vercel (frontend) + Render (backend, Docker; 2 GB Standard instance if the voice model needs it) | Must be live for judging |

---

## 9. Build plan (cut order if short on time)

1. **Must have by Day 3 launch:** widget, speech to text, pain score, Dodo deposit, founder dashboard.
2. **Add on Day 3:** voice-fingerprint duplicate check, throwaway email check.
3. **If time allows:** TigerGraph fake-ring graph.

The first set alone is a working, sellable product.

---

Full tool details, verified against official docs, are in **TOOLS_VERIFIED.md**.

## Sources

- Waitlist conversion (~3%): [Preuve](https://preuve.ai/blog/is-my-startup-idea-actually-validated)
- Waitlists measure curiosity: [eChai Ventures](https://echai.ventures/startingup/validate-idea/is-a-waitlist-with-a-lot-of-signups-actual-proof-of-demand)
- Fake signups gaming referral leaderboards: [LaunchList FAQ](https://feedback.getlaunchlist.com/help/faq/spam-protection)
- Survey fraud rates: [NORC research brief, April 2026](https://www.norc.org/content/dam/norc-org/pdf2026/cpss-research-brief-fraud-lit-review.pdf); attention checks: [Zamplia](https://zamplia.com/?p=18074)
- Waitlist tools and fraud protection: [LaunchList comparison](https://app.getlaunchlist.com/blog/best-prefinery-alternatives-2026), [Prefinery](https://www.prefinery.com/blog/pre-launch-email-signup-tools-a-comprehensive-comparison-for-2025/), [Waitlister review](https://zplatform.ai/lifetime-deals/waitlister-lifetime-deal/)
- Survey fraud tools: [Research Defender](https://repdata.com/solutions/research-defender/), [Emporia buyer's guide](https://www.emporiaresearch.com/blog/a-buyers-guide-to-anti-fraud-tools-in-market-research-sampling)
- TrustMRR: [ExitBid review](https://exitbid.io/blog/trustmrr-review-2026), [supported providers](https://browse.sh/skills/trustmrr.com/search-analytics-metrics-ooeinc)
- World ID: [Axios via Pulse](https://www.pulse.bot/ai/news/sam-altmans-proof-of-human-company-pushes-into-mainstream-services-6ce40a33-1a79-4a29-adf4-c07ee1c3baf8/), [Yellow explainer](https://yellow.com/learn/worldcoin-human-verification-future-identity)
- Judge background: [Cookiy AI press release](https://stocks.observer-reporter.com/observerreporter/article/marketersmedia-2025-10-7-cookiy-ai-secures-7m-to-transform-consumer-insights-with-agentic-voice-ai)
