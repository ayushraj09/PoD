# Why we don't flag AI-generated voices

We planned to use AASIST, the best-known open-source detector for synthetic speech. It was trained on the 2019 ASVspoof dataset and does very well there (0.83% error), but on the public Speech Anti-Spoofing Arena's **In-the-Wild** set of real-world deepfakes its error rate is **43.01%** (AASIST-L: **44.45%**), close to a coin flip ([AASIST arena scores](https://huggingface.co/SpeechAntiSpoofingBenchmarks/AASIST), [AASIST-L](https://huggingface.co/SpeechAntiSpoofingBenchmarks/AASIST-L), [official repo](https://github.com/clovaai/aasist)). Labelling real people as fake would hurt founders and their users more than missing a few fakes, so the `possible_ai_voice` flag stays reserved and nothing produces it. Instead, same-voice matching (one person behind many emails), device and network checks, fake-ring detection and refundable deposits carry the weight: a cloned voice reused across signups still matches itself, and a deposit costs a faker real money.

## Update (30 Oct 2026): a cheap signal that does work

A model-free check now produces `possible_ai_voice`: a real microphone always records some room
noise (about −60 dBFS on the laptops and phones we tested), while synthesized or injected audio
(TTS, a voice clone played into a virtual mic) has stretches of **exact digital silence**. The flag
fires when at least 0.6 s and 15 % of the clip is below −100 dBFS. On our recordings: an AI voice
27 %, two humans 0 %, all reference samples 0–2 %. It costs 30 trust points: on its own a signup
stays verified (70), combined with any other signal it drops to suspicious or fake. Details and
data: `voice_calibration.md`.
