"""Voice fingerprint (SpeechBrain ECAPA, 192 numbers) + same-person matching via pgvector."""

from pathlib import Path

import numpy as np
import soundfile as sf

from app import db, models
from app.config import get_settings
from app.pipeline.checks import flag

# Memory for the speaker model grows with clip length (~15 MB per second); 10 s is plenty to
# recognise a voice and keeps one embedding well under 200 MB.
MAX_EMBED_SECONDS = 10


def embed(wav_path: Path) -> list[float]:
    """16 kHz mono WAV -> unit-length 192-number voice fingerprint."""
    import torch

    samples, sr = sf.read(wav_path, dtype="float32")
    if sr != 16000:
        raise ValueError(f"expected 16 kHz audio, got {sr}")
    samples = samples[: MAX_EMBED_SECONDS * sr]
    with torch.inference_mode():
        emb = models.encoder.encode_batch(torch.from_numpy(samples)[None, :])
    vec = emb.squeeze().cpu().numpy().astype(np.float64)
    return (vec / np.linalg.norm(vec)).tolist()


def available() -> bool:
    return models.encoder is not None


def similarity(a: list[float], b: list[float]) -> float:
    return float(np.dot(a, b))  # both are unit length -> cosine similarity


def same_voice_flags(signup: dict, embedding: list[float]) -> list[dict]:
    matches = db.match_voices(signup["waitlist_id"], embedding, signup["id"],
                              get_settings().voice_match_threshold)
    return [flag("same_voice", m["id"]) for m in matches[:1]]
