import subprocess

import pytest

from app.config import get_settings
from app.pipeline.audio import clean
from app.pipeline.checks import canonical_email, same_answer_flags
from app.pipeline.verdict import decide

SCRIPT = "Product is cheap and very useful and very effective, that's why I'm considering it"


@pytest.mark.parametrize("email,canon", [
    ("Ravi.Kumar+waitlist@gmail.com", "ravikumar@gmail.com"),
    ("ravikumar@googlemail.com", "ravikumar@gmail.com"),
    ("ravi.kumar+x@company.in", "ravi.kumar@company.in"),   # dots matter outside Gmail
    ("ravi@company.in", "ravi@company.in"),
])
def test_canonical_email(email, canon):
    assert canonical_email(email) == canon


def test_gmail_alias_is_already_signed_up(fake_db, monkeypatch):
    from fastapi.testclient import TestClient
    from app.main import app
    from app.routes import signups as route
    monkeypatch.setattr(route, "process_signup", lambda sid: None)
    fake_db.add_waitlist("demo")
    with TestClient(app) as c:
        form = {"waitlist_slug": "demo", "consent": "true", "device_id": "d"}
        first = c.post("/v1/signups", data={**form, "email": "ravikumar@gmail.com"}).json()["signup_id"]
        for alias in ("ravi.kumar@gmail.com", "ravikumar+2@gmail.com", "RaviKumar@googlemail.com"):
            r = c.post("/v1/signups", data={**form, "email": alias})
            assert r.status_code == 409 and r.json()["signup_id"] == first, alias
        assert c.post("/v1/signups", data={**form, "email": "ravi.kumar@outlook.com"}).status_code == 201


def test_copied_script_is_flagged(fake_db):
    first = fake_db.add_signup(waitlist_id="wl", transcript=SCRIPT)
    copy = fake_db.add_signup(waitlist_id="wl")
    assert same_answer_flags(copy, SCRIPT.replace("I'm", "I am")) == [
        {"code": "same_answer", "detail": first["id"]}]


def test_own_words_and_short_answers_are_not_flagged(fake_db):
    fake_db.add_signup(waitlist_id="wl", transcript=SCRIPT)
    fake_db.add_signup(waitlist_id="wl", transcript="Sounds cool, I'd use it.")
    s = fake_db.add_signup(waitlist_id="wl")
    assert same_answer_flags(s, "Last week my skin broke out before an interview and the cream I "
                                "bought for 900 rupees did nothing") == []
    assert same_answer_flags(s, "Sounds cool, I'd use it.") == []   # under 8 words
    other = fake_db.add_signup(waitlist_id="other-wl")
    assert same_answer_flags(other, SCRIPT) == []                   # different waitlist


def _make(tmp_path, name, filtergraph):
    path = tmp_path / name
    subprocess.run([get_settings().ffmpeg_bin, "-y", "-loglevel", "error", "-filter_complex",
                    filtergraph, str(path)], check=True)
    return path


def test_digital_silence_is_possible_ai_voice(tmp_path):
    # 4 s of syllable-like speech with 2 s of exact silence: TTS / injected audio
    speech = "sine=frequency=220:duration=4,tremolo=f=3:d=0.95[a];anullsrc=r=48000:cl=mono:d=2[b];[a][b]concat=n=2:v=0:a=1"
    audio = clean(_make(tmp_path, "tts.wav", speech), tmp_path)
    assert [f["code"] for f in audio.flags] == ["possible_ai_voice"]


def test_room_noise_between_words_is_human(tmp_path):
    speech = ("sine=frequency=220:duration=4,tremolo=f=3:d=0.95[a];"
              "anoisesrc=color=pink:amplitude=0.002:duration=2[b];[a][b]concat=n=2:v=0:a=1")
    assert clean(_make(tmp_path, "mic.wav", speech), tmp_path).flags == []


def test_pure_silence_is_no_speech_not_ai(tmp_path):
    audio = clean(_make(tmp_path, "s.wav", "anullsrc=r=48000:cl=mono:d=5"), tmp_path)
    assert [f["code"] for f in audio.flags] == ["no_speech"]


@pytest.mark.parametrize("codes,trust,verdict", [
    (("possible_ai_voice",), 70, "verified"),          # alone: a hint, not a conviction
    (("possible_ai_voice", "repeat_ip"), 55, "suspicious"),
    (("same_answer",), 65, "suspicious"),
    (("same_answer", "possible_ai_voice"), 35, "fake"),
    (("same_voice", "possible_ai_voice"), 20, "fake"),  # the facewash AI clone
])
def test_new_penalties(codes, trust, verdict):
    assert decide([{"code": c} for c in codes], has_audio=True) == (trust, verdict)
