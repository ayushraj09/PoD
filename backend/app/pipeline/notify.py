"""Sends signup.scored to NOTIFY_WEBHOOK_URL (any webhook receiver), per contracts/events.md."""

import logging

import httpx

from app.config import get_settings

log = logging.getLogger("pod.notify")


def mask_email(email: str) -> str:
    local, _, domain = email.partition("@")
    return f"{local[:2]}***@{domain}"


def build_event(signup: dict, waitlist_slug: str) -> dict:
    return {
        "type": "signup.scored",
        "waitlist_slug": waitlist_slug,
        "signup_id": signup["id"],
        "email_masked": mask_email(signup["email"]),
        "human_verdict": signup.get("human_verdict"),
        "pain_score": signup.get("pain_score"),
        "pain_quote": signup.get("pain_quote") or "",
        "trust_score": signup.get("trust_score"),
        "created_at": signup.get("created_at"),
    }


def send_scored(signup: dict, waitlist_slug: str) -> None:
    url = get_settings().notify_webhook_url
    if not url:
        return
    try:
        httpx.post(url, json=build_event(signup, waitlist_slug), timeout=5).raise_for_status()
    except Exception as e:  # alerts must never break scoring
        log.warning("notify failed for %s: %s", signup["id"], e)
