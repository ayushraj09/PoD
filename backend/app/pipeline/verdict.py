"""Flags -> trust score (0-100) -> human_verdict, per contracts/scoring.md."""

PENALTIES = {
    "same_voice": 50,
    "disposable_email": 35,
    "ring_member": 40,
    "repeat_device": 20,  # weak: open-source FingerprintJS is only 40-60% accurate
    "repeat_ip": 15,
    "bad_recording": 40,  # too_short and/or no_speech, counted once
}
BAD_RECORDING = {"too_short", "no_speech"}


def verdict_for(trust: int | None) -> str:
    if trust is None:
        return "unverified"
    if trust >= 70:
        return "verified"
    if trust >= 40:
        return "suspicious"
    return "fake"


def decide(flags: list[dict], has_audio: bool) -> tuple[int | None, str]:
    """Returns (trust_score, human_verdict). No audio or a processing error -> unverified."""
    codes = {f["code"] for f in flags}
    if not has_audio or "processing_error" in codes:
        return None, "unverified"
    if codes & BAD_RECORDING:
        codes = (codes - BAD_RECORDING) | {"bad_recording"}
    trust = 100 - sum(PENALTIES.get(c, 0) for c in codes)
    trust = max(0, min(100, trust))
    return trust, verdict_for(trust)
