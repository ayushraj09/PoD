# Voice match calibration (VOICE_MATCH_THRESHOLD)

Similarity = cosine similarity of SpeechBrain ECAPA voice fingerprints (1.0 = identical).
A signup gets `same_voice` when its similarity to an earlier signup on the same waitlist is
≥ `VOICE_MATCH_THRESHOLD`.

## Evidence (30 Oct 2026)

| Pair | Source | Similarity | Should match? |
|---|---|---|---|
| two different humans, same sentence | `facewash` waitlist, real phones/laptops | 0.014, 0.053 | no |
| two different humans (alphabet test) | `pod` waitlist, real widget | 0.236 | no |
| different synthetic voices | macOS TTS, 3 voices × 2 sentences | 0.007 – 0.467 | no |
| **AI voice imitating a human vs that human** | `facewash`, same sentence, same network | **0.743** | **yes** (one person, two emails) |
| same synthetic voice, different sentences | macOS TTS | 0.812 – 0.882 | yes |

Highest "different" score: 0.467. Lowest "same / clone" score: 0.743.

**Decision: keep 0.6.** It sits in the middle of the gap. Above ~0.7 the AI clone would pass;
below ~0.5 different people would start to collide. Re-run `python -m scripts.calibrate_voices`
with more real voices (target: 6+ people, 3 clips each) before changing it.

## How the AI voice was identified

The three `facewash` recordings were separate takes (loudness envelopes correlate only 0.19–0.32;
a replay would be ~1.0). The AI one (`a62edfd8`) had a **digital-silence noise floor of
−200 dBFS with 29 % of frames exactly zero**; both human recordings had a normal room-noise floor
(about −61 dBFS) and no exact-zero frames. Its pitch (108 Hz) matched the human it imitated
(107 Hz); the other human was 140 Hz.

Exact digital silence is a cheap, strong hint of synthetic or injected audio (a real microphone
always records some noise). It is not used for scoring yet; see `ai_voice.md` for why model-based
AI-voice detection is off.
