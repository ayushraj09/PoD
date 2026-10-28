"""Speech to text: Sarvam saaras:v3 (Indian languages) with OpenAI as fallback.

Check command: python -m app.pipeline.stt tests/samples/
"""

import logging
import sys
import tempfile
from pathlib import Path

from app.config import get_settings

log = logging.getLogger("pod.stt")
TIMEOUT_S = 20


class STTError(Exception):
    pass


def _sarvam(wav_path: Path) -> tuple[str, str | None]:
    from sarvamai import SarvamAI

    key = get_settings().sarvam_api_key
    if not key:
        raise STTError("SARVAM_API_KEY not set")
    client = SarvamAI(api_subscription_key=key)
    with open(wav_path, "rb") as f:
        r = client.speech_to_text.transcribe(
            file=f, model="saaras:v3", mode="transcribe",
            request_options={"timeout_in_seconds": TIMEOUT_S, "max_retries": 1},
        )
    return (r.transcript or "").strip(), r.language_code


def _openai(wav_path: Path) -> tuple[str, str | None]:
    from openai import OpenAI

    s = get_settings()
    if not s.openai_api_key:
        raise STTError("OPENAI_API_KEY not set")
    client = OpenAI(api_key=s.openai_api_key, max_retries=1)
    with open(wav_path, "rb") as f:
        r = client.audio.transcriptions.create(model=s.openai_transcribe_model, file=f,
                                               timeout=TIMEOUT_S)
    return (r.text or "").strip(), None


PROVIDERS = {"sarvam": _sarvam, "openai": _openai}


def transcribe(wav_path: Path) -> tuple[str, str | None]:
    """Returns (text, language_code). Tries STT_PROVIDER first, then the other one."""
    first = get_settings().stt_provider if get_settings().stt_provider in PROVIDERS else "sarvam"
    order = [first] + [p for p in PROVIDERS if p != first]
    errors = []
    for name in order:
        try:
            return PROVIDERS[name](wav_path)
        except Exception as e:
            log.warning("stt %s failed: %s", name, e)
            errors.append(f"{name}: {e}")
    raise STTError("; ".join(errors))


if __name__ == "__main__":
    from app.pipeline.audio import clean

    folder = Path(sys.argv[1] if len(sys.argv) > 1 else "tests/samples")
    for src in sorted(p for p in folder.iterdir() if p.suffix.lower() in
                      {".webm", ".mp4", ".m4a", ".ogg", ".wav", ".mp3"}):
        with tempfile.TemporaryDirectory() as tmp:
            audio = clean(src, Path(tmp))
            text, lang = transcribe(audio.wav_path)
            flags = ",".join(f["code"] for f in audio.flags) or "-"
            print(f"{src.name} [{audio.duration:.1f}s, {lang}, flags={flags}]\n  {text}\n")
