import subprocess

import pytest

from app.config import get_settings
from app.pipeline import pain, run, stt, voice


def recording(tmp_path, seconds=5, source="tone"):
    path = tmp_path / "rec.webm"
    src = {"tone": f"sine=frequency=220:duration={seconds}",
           "silence": f"anullsrc=r=48000:cl=mono:d={seconds}"}[source]
    subprocess.run([get_settings().ffmpeg_bin, "-y", "-loglevel", "error", "-f", "lavfi",
                    "-i", src, str(path)], check=True)
    return path.read_bytes()


@pytest.fixture
def stubs(monkeypatch):
    calls = {"notify": []}
    monkeypatch.setattr(stt, "transcribe", lambda wav: ("I lost three hours last Tuesday", "en-IN"))
    monkeypatch.setattr(pain, "_call_llm", lambda msgs: {
        "pain_score": 82, "pain_reason": "Specific moment and cost.",
        "pain_quote": "I lost three hours last Tuesday"})
    monkeypatch.setattr(voice, "embed", lambda wav: [1.0] + [0.0] * 191)
    monkeypatch.setattr(run, "send_scored", lambda s, slug: calls["notify"].append((s, slug)))
    return calls


def signup_with_audio(fake_db, data, **kw):
    wl = fake_db.add_waitlist("acme", product_description="Invoice tool")
    s = fake_db.add_signup(waitlist_id=wl["id"], audio_path=f"{wl['id']}/x.webm", **kw)
    fake_db.files[s["audio_path"]] = (data, "audio/webm")
    return s


def test_happy_path(fake_db, stubs, tmp_path):
    s = signup_with_audio(fake_db, recording(tmp_path), email="ravi@gmail.com")
    run.process_signup(s["id"])
    row = fake_db.signups[s["id"]]
    assert row["status"] == "scored"
    assert row["human_verdict"] == "verified" and row["trust_score"] == 100
    assert row["pain_score"] == 82 and row["pain_quote"] == "I lost three hours last Tuesday"
    assert row["transcript"] and row["language"] == "en-IN"
    assert len(row["voice_embedding"]) == 192
    assert row["flags"] == []
    assert stubs["notify"][0][1] == "acme"


def test_same_voice_and_disposable_is_fake(fake_db, stubs, tmp_path):
    s = signup_with_audio(fake_db, recording(tmp_path), email="x@mailinator.com")
    fake_db.voice_matches = [{"id": "earlier", "similarity": 0.9}]
    run.process_signup(s["id"])
    row = fake_db.signups[s["id"]]
    assert {f["code"] for f in row["flags"]} == {"disposable_email", "same_voice"}
    assert row["human_verdict"] == "fake"


def test_silence_skips_stt_and_voice(fake_db, stubs, tmp_path, monkeypatch):
    monkeypatch.setattr(stt, "transcribe", lambda wav: pytest.fail("stt called"))
    monkeypatch.setattr(voice, "embed", lambda wav: pytest.fail("embed called"))
    s = signup_with_audio(fake_db, recording(tmp_path, source="silence"))
    run.process_signup(s["id"])
    row = fake_db.signups[s["id"]]
    assert [f["code"] for f in row["flags"]] == ["no_speech"]
    assert row["pain_score"] == 0 and row["human_verdict"] == "suspicious"


def test_no_audio_is_unverified(fake_db, stubs):
    wl = fake_db.add_waitlist("acme")
    s = fake_db.add_signup(waitlist_id=wl["id"])
    run.process_signup(s["id"])
    row = fake_db.signups[s["id"]]
    assert row["status"] == "scored" and row["human_verdict"] == "unverified"
    assert row["trust_score"] is None


def test_crash_never_leaves_row_processing(fake_db, stubs, tmp_path, monkeypatch):
    def down(wav):
        raise RuntimeError("stt down")
    monkeypatch.setattr(stt, "transcribe", down)
    s = signup_with_audio(fake_db, recording(tmp_path), email="x@mailinator.com")
    run.process_signup(s["id"])
    row = fake_db.signups[s["id"]]
    assert row["status"] == "scored" and row["human_verdict"] == "unverified"
    assert [f["code"] for f in row["flags"]] == ["disposable_email", "processing_error"]


def test_requeue_finishes_stuck_rows(fake_db, stubs):
    wl = fake_db.add_waitlist("acme")
    a = fake_db.add_signup(waitlist_id=wl["id"], status="processing")
    b = fake_db.add_signup(waitlist_id=wl["id"], status="pending")
    run.requeue_stuck()
    assert fake_db.signups[a["id"]]["status"] == fake_db.signups[b["id"]]["status"] == "scored"
