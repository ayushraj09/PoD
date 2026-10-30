import subprocess

import pytest

from app.config import get_settings
from app.pipeline import stt
from app.pipeline.audio import BadAudio, clean


def make(tmp_path, name, source, seconds):
    """Generate a test recording with ffmpeg (sine = 'speech', anullsrc = silence)."""
    path = tmp_path / name
    src = {"tone": f"sine=frequency=220:duration={seconds}",
           "silence": f"anullsrc=r=48000:cl=stereo:d={seconds}"}[source]
    subprocess.run([get_settings().ffmpeg_bin, "-y", "-loglevel", "error", "-f", "lavfi", "-i", src, str(path)],
                   check=True)
    return path


@pytest.mark.parametrize("name", ["a.webm", "a.m4a", "a.ogg", "a.wav"])
def test_formats_convert_to_16k_mono(tmp_path, name):
    audio = clean(make(tmp_path, name, "tone", 5), tmp_path)
    assert 4.9 < audio.duration < 5.2
    assert audio.flags == []


def test_too_short(tmp_path):
    audio = clean(make(tmp_path, "a.webm", "tone", 2), tmp_path)
    assert [f["code"] for f in audio.flags] == ["too_short"]


def test_silence_is_no_speech(tmp_path):
    audio = clean(make(tmp_path, "a.webm", "silence", 5), tmp_path)
    assert [f["code"] for f in audio.flags] == ["no_speech"]


def test_capped_at_30s(tmp_path):
    audio = clean(make(tmp_path, "a.wav", "tone", 35), tmp_path)
    assert audio.duration == pytest.approx(30, abs=0.1)


def test_garbage_is_bad_audio(tmp_path):
    bad = tmp_path / "a.webm"
    bad.write_bytes(b"not audio at all")
    with pytest.raises(BadAudio):
        clean(bad, tmp_path)


def test_stt_falls_back_to_other_provider(monkeypatch, tmp_path):
    def broken(_):
        raise RuntimeError("down")
    monkeypatch.setitem(stt.PROVIDERS, "sarvam", broken)
    monkeypatch.setitem(stt.PROVIDERS, "openai", lambda _: ("hello", None))
    assert stt.transcribe(tmp_path / "x.wav") == ("hello", None)


def test_stt_raises_when_all_fail(monkeypatch, tmp_path):
    def broken(_):
        raise RuntimeError("down")
    monkeypatch.setitem(stt.PROVIDERS, "sarvam", broken)
    monkeypatch.setitem(stt.PROVIDERS, "openai", broken)
    with pytest.raises(stt.STTError):
        stt.transcribe(tmp_path / "x.wav")


def test_smallest_retries_with_english(monkeypatch, tmp_path):
    import httpx

    wav = tmp_path / "x.wav"
    wav.write_bytes(b"RIFF")
    seen = []

    def fake_post(url, params, headers, content, timeout):
        seen.append(params["language"])
        req = httpx.Request("POST", url)
        if params["language"] == "multi-indic":
            return httpx.Response(400, text="language not available in region", request=req)
        return httpx.Response(200, json={"status": "success", "transcription": " hello "},
                              request=req)

    monkeypatch.setattr(httpx, "post", fake_post)
    monkeypatch.setattr(get_settings(), "smallest_api_key", "test")
    assert stt._smallest(wav) == ("hello", "en")
    assert seen == ["multi-indic", "en"]
