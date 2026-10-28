import logging

from app import db

log = logging.getLogger("pod.pipeline")


def process_signup(signup_id: str) -> None:
    """Placeholder until A2-A6: marks the row scored with neutral values."""
    db.update_signup(signup_id, {"status": "processing"})
    db.update_signup(signup_id, {
        "status": "scored",
        "human_verdict": "unverified",
        "pain_score": 0,
        "flags": [],
    })
    log.info("signup %s scored (placeholder)", signup_id)
