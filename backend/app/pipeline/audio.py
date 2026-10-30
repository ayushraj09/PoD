import subprocess
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import soundfile as sf

from app.config import get_settings
from app.pipeline.checks import flag

SAMPLE_RATE = 16000
MAX_SECONDS = 30            # Sarvam's REST endpoint rejects longer audio
MIN_SECONDS = 3.0           # under this -> too_short
FRAME_MS = 30
SILENCE_DBFS = -65.0        # frames quieter than this are silence, whatever the mic
ABOVE_NOISE_DB = 12.0       # speech frames stand this far above the clip's own background
MIN_SPEECH_SECONDS = 0.8    # less speech than this -> no_speech
# A real microphone always records some room noise (about -60 dBFS on laptops and phones).
# Stretches of exact digital silence mean the audio was synthesized or injected (TTS, voice
# clone, virtual mic). Measured: humans 0 %, an AI voice 29 % of frames.
DIGITAL_SILENCE_DBFS = -100.0
AI_SILENCE_MIN_FRACTION = 0.15
AI_SILENCE_MIN_SECONDS = 0.6


class BadAudio(Exception):
    pass


@dataclass
class CleanAudio:
    wav_path: Path
    duration: float
    speech_seconds: float
    digital_silence_seconds: float = 0.0
    flags: list[dict] = field(default_factory=list)


def to_wav(src: Path, dst: Path) -> None:
    """Any browser recording (webm / mp4 / ogg / wav) -> 16 kHz mono WAV, max 30 s."""
    cmd = [get_settings().ffmpeg_bin, "-nostdin", "-y", "-loglevel", "error", "-i", str(src),
           "-vn", "-ac", "1", "-ar", str(SAMPLE_RATE), "-t", str(MAX_SECONDS),
           "-c:a", "pcm_s16le", str(dst)]
    try:
        subprocess.run(cmd, check=True, capture_output=True, timeout=30)
    except subprocess.CalledProcessError as e:
        raise BadAudio(e.stderr.decode(errors="ignore")[-300:]) from e
    except subprocess.TimeoutExpired as e:
        raise BadAudio("ffmpeg timed out") from e


def frame_dbfs(samples: np.ndarray, sr: int = SAMPLE_RATE) -> np.ndarray:
    frame = int(sr * FRAME_MS / 1000)
    n = len(samples) // frame
    frames = samples[: n * frame].reshape(n, frame)
    rms = np.sqrt(np.mean(frames.astype(np.float64) ** 2, axis=1))
    return 20 * np.log10(np.maximum(rms, 1e-10))


def digital_silence_seconds(samples: np.ndarray, sr: int = SAMPLE_RATE) -> float:
    return float(np.sum(frame_dbfs(samples, sr) < DIGITAL_SILENCE_DBFS)) * FRAME_MS / 1000


def speech_seconds(samples: np.ndarray, sr: int = SAMPLE_RATE) -> float:
    dbfs = frame_dbfs(samples, sr)
    if len(dbfs) == 0:
        return 0.0
    # Mic levels vary by 40 dB between devices, so compare against this clip's quietest
    # frames (background) instead of a fixed level. Steady noise never rises above itself.
    background = np.percentile(dbfs, 10)
    threshold = max(SILENCE_DBFS, background + ABOVE_NOISE_DB)
    return float(np.sum(dbfs > threshold)) * FRAME_MS / 1000


def clean(src: Path, workdir: Path) -> CleanAudio:
    wav = workdir / "clean.wav"
    to_wav(src, wav)
    samples, sr = sf.read(wav, dtype="float32")
    duration = len(samples) / sr
    if duration == 0:
        raise BadAudio("empty audio")
    loud = speech_seconds(samples, sr)
    silent = digital_silence_seconds(samples, sr)
    flags = []
    if duration < MIN_SECONDS:
        flags.append(flag("too_short", f"{duration:.1f}s"))
    if loud < MIN_SPEECH_SECONDS:
        flags.append(flag("no_speech"))
    elif silent >= AI_SILENCE_MIN_SECONDS and silent / duration >= AI_SILENCE_MIN_FRACTION:
        flags.append(flag("possible_ai_voice", f"{silent / duration:.0%} digital silence"))
    return CleanAudio(wav, duration, loud, silent, flags)
