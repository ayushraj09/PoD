"""process_signup(signup_id): runs every scoring step in order and writes the result back."""

import logging
import re
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path, PurePath

from app import db
from app.pipeline import audio as audio_step
from app.pipeline import pain, stt, voice
from app.pipeline.checks import basic_checks, flag, same_answer_flags
from app.pipeline.graph import check_ring
from app.pipeline.notify import send_scored
from app.pipeline.verdict import decide

log = logging.getLogger("pod.pipeline")
INTERRUPTED = "interrupted"


@contextmanager
def step(signup_id: str, name: str):
    t = time.perf_counter()
    try:
        yield
    finally:
        log.info("signup %s step=%s ms=%d", signup_id, name, (time.perf_counter() - t) * 1000)


def score(signup: dict, waitlist: dict, flags: list[dict]) -> dict:
    """Fills `flags` as it goes, so a crash part-way still keeps what was found."""
    sid = signup["id"]
    out: dict = {}
    with step(sid, "checks"):
        flags += basic_checks(signup)

    if signup.get("audio_path"):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / f"in{PurePath(signup['audio_path']).suffix}"
            with step(sid, "download"):
                src.write_bytes(db.download_audio(signup["audio_path"]))
            with step(sid, "audio"):
                clean = audio_step.clean(src, Path(tmp))
            flags += clean.flags
            has_speech = not any(f["code"] == "no_speech" for f in clean.flags)

            text, lang = "", None
            if has_speech:
                with step(sid, "stt"):
                    text, lang = stt.transcribe(clean.wav_path)
            out.update(transcript=text, language=lang)
            if has_speech and len(re.findall(r"\w+", text)) < 2:
                # loud but no words (beeps, music, noise bursts): not a person answering
                flags.append(flag("no_speech", "no words recognised"))
                has_speech = False
            with step(sid, "same_answer"):
                flags += same_answer_flags(signup, text)

            with step(sid, "pain"):
                out.update(pain.score_pain(text, waitlist.get("product_description") or "",
                                           waitlist.get("question") or ""))

            if has_speech and voice.available():  # model off (LOAD_MODELS=false): no matching
                with step(sid, "voice"):
                    embedding = voice.embed(clean.wav_path)
                    out["voice_embedding"] = embedding
                    flags += voice.same_voice_flags(signup, embedding)

    trust, verdict = decide(flags, has_audio=bool(signup.get("audio_path")))
    out.update(trust_score=trust, human_verdict=verdict)
    return out


def process_signup(signup_id: str) -> None:
    t0 = time.perf_counter()
    signup = db.get_signup(signup_id)
    if not signup:
        log.warning("signup %s not found", signup_id)
        return
    waitlist = db.get_waitlist(signup["waitlist_id"]) or {}
    db.update_signup(signup_id, {"status": "processing"})

    flags: list[dict] = []
    try:
        result = score(signup, waitlist, flags)
    except Exception as e:
        log.exception("signup %s scoring failed", signup_id)
        flags.append(flag("processing_error", type(e).__name__))
        result = {"trust_score": None, "human_verdict": "unverified"}

    result.update(status="scored", flags=flags)
    try:
        db.update_signup(signup_id, result)
    except Exception:
        # never leave a row stuck in processing, even if the full write fails
        log.exception("signup %s write-back failed", signup_id)
        db.update_signup(signup_id, {"status": "scored", "human_verdict": "unverified",
                                     "flags": flags + [flag("processing_error", "write")]})
        return

    log.info("signup %s scored verdict=%s trust=%s pain=%s flags=%s total_ms=%d", signup_id,
             result["human_verdict"], result["trust_score"], result.get("pain_score"),
             [f["code"] for f in flags], (time.perf_counter() - t0) * 1000)
    send_scored({**signup, **result}, waitlist.get("slug", ""))
    check_ring({**signup, **result})


def requeue_stuck() -> None:
    """Background tasks die with the process, so finish anything left from before a restart."""
    try:
        stuck = db.signups_with_status(["pending", "processing"])
    except Exception:
        log.exception("requeue lookup failed")
        return
    if stuck:
        log.info("re-queueing %d stuck signups", len(stuck))
    for row in stuck:
        if row["status"] == "processing":
            # The process died while scoring this row; maybe because of it (e.g. out of memory).
            # Retry once, leaving a marker that a successful run overwrites. If the marker is
            # still there, it already crashed once: finish it instead of crash-looping.
            if any(f.get("detail") == INTERRUPTED for f in row.get("flags") or []):
                log.warning("signup %s crashed twice, marking it unverified", row["id"])
                db.update_signup(row["id"], {"status": "scored", "human_verdict": "unverified",
                                             "trust_score": None})
                continue
            db.update_signup(row["id"], {"flags": [flag("processing_error", INTERRUPTED)]})
        process_signup(row["id"])
