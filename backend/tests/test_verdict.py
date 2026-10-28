import pytest

from app.pipeline.notify import build_event, mask_email
from app.pipeline.verdict import decide


def f(*codes):
    return [{"code": c, "detail": ""} for c in codes]


@pytest.mark.parametrize("codes,trust,verdict", [
    ((), 100, "verified"),
    (("repeat_ip",), 85, "verified"),
    (("repeat_device",), 80, "verified"),
    (("repeat_device", "repeat_ip"), 65, "suspicious"),
    (("disposable_email",), 65, "suspicious"),
    (("same_voice",), 50, "suspicious"),
    (("too_short",), 60, "suspicious"),
    (("too_short", "no_speech"), 60, "suspicious"),  # one bad recording, counted once
    (("same_voice", "disposable_email"), 15, "fake"),
    (("same_voice", "ring_member", "disposable_email"), 0, "fake"),
])
def test_trust_and_verdict(codes, trust, verdict):
    assert decide(f(*codes), has_audio=True) == (trust, verdict)


def test_no_audio_is_unverified():
    assert decide(f("disposable_email"), has_audio=False) == (None, "unverified")


def test_processing_error_is_unverified():
    assert decide(f("processing_error"), has_audio=True) == (None, "unverified")


def test_event_shape():
    assert mask_email("ravi@gmail.com") == "ra***@gmail.com"
    ev = build_event({"id": "s1", "email": "ravi@gmail.com", "human_verdict": "verified",
                      "pain_score": 82, "pain_quote": "q", "trust_score": 88,
                      "created_at": "2026-10-29T12:00:00Z"}, "acme")
    assert set(ev) == {"type", "waitlist_slug", "signup_id", "email_masked", "human_verdict",
                       "pain_score", "pain_quote", "trust_score", "created_at"}
    assert ev["type"] == "signup.scored" and ev["email_masked"] == "ra***@gmail.com"
