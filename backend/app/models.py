"""Heavy models are loaded once at startup, never per request."""

import logging

log = logging.getLogger("pod.models")

encoder = None  # SpeechBrain ECAPA speaker encoder (stage A5)
loaded = False


def load() -> None:
    global encoder, loaded
    from app.config import get_settings

    if not get_settings().load_models:
        loaded = True
        return
    try:
        from speechbrain.inference.speaker import EncoderClassifier
    except ImportError:  # older SpeechBrain
        from speechbrain.pretrained import EncoderClassifier
    encoder = EncoderClassifier.from_hparams(
        source="speechbrain/spkrec-ecapa-voxceleb",
        savedir="models/ecapa",
        run_opts={"device": "cpu"},
    )
    loaded = True
    log.info("speaker encoder loaded")
