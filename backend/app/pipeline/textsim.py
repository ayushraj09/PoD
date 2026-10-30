"""Meaning similarity of answers (OpenAI text-embedding-3-small), cached per signup id."""

import logging

import numpy as np

from app.config import get_settings

log = logging.getLogger("pod.textsim")
MODEL = "text-embedding-3-small"
_cache: dict[str, np.ndarray] = {}   # signup id -> unit vector; transcripts don't change


def embed(items: dict[str, str]) -> dict[str, np.ndarray]:
    """{key: text} -> {key: unit vector}. Missing keys are fetched in one batch."""
    todo = {k: t for k, t in items.items() if k not in _cache}
    if todo:
        from openai import OpenAI

        client = OpenAI(api_key=get_settings().openai_api_key, max_retries=1)
        resp = client.embeddings.create(model=MODEL, input=list(todo.values()), timeout=15)
        for key, item in zip(todo, resp.data):
            v = np.array(item.embedding)
            _cache[key] = v / np.linalg.norm(v)
    return {k: _cache[k] for k in items}
