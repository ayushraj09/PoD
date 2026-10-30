import logging
import re
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher

from disposable_email_domains import blocklist
from email_validator import EmailNotValidError, caching_resolver, validate_email

from app import db
from app.config import get_settings
from app.pipeline import textsim

log = logging.getLogger("pod.checks")
REPEAT_IP_MIN = 3          # this many signups (including this one) from one network...
REPEAT_IP_WINDOW = timedelta(hours=24)  # ...within this window
SAME_ANSWER_MIN_WORDS = 8     # shorter answers ("sounds cool") collide by chance
SAME_ANSWER_RATIO = 0.8       # word-level: copies 0.88+, different genuine stories <= 0.13
SAME_MEANING_MIN_WORDS = 15   # meaning check only on real stories; short generic ones are alike
SAME_MEANING_COSINE = 0.9     # paraphrases 0.92-0.94, different genuine stories <= 0.56
GMAIL = {"gmail.com", "googlemail.com"}

_resolver = None


class InvalidEmail(ValueError):
    pass


def normalize_email(email: str, check_dns: bool = True) -> str:
    global _resolver
    if check_dns and _resolver is None:
        _resolver = caching_resolver(timeout=5)
    try:
        info = validate_email(email.strip(), check_deliverability=check_dns,
                              dns_resolver=_resolver if check_dns else None)
    except EmailNotValidError as e:
        raise InvalidEmail(str(e)) from e
    return info.normalized.lower()


def canonical_email(email: str) -> str:
    """The inbox an address really reaches: drops +tags everywhere and dots for Gmail."""
    local, _, domain = email.lower().partition("@")
    local = local.split("+", 1)[0]
    if domain in GMAIL:
        local, domain = local.replace(".", ""), "gmail.com"
    return f"{local}@{domain}"


def alias_of_existing(waitlist_id: str, email: str) -> dict | None:
    """An earlier signup on this waitlist that reaches the same inbox under another spelling."""
    domain = email.rsplit("@", 1)[-1]
    domains = sorted(GMAIL) if domain in GMAIL else [domain]
    target = canonical_email(email)
    return next((r for r in db.signups_on_domains(waitlist_id, domains)
                 if r["email"] != email and canonical_email(r["email"]) == target), None)


def _words(text: str) -> list[str]:
    return re.findall(r"\w+", text.lower())


def same_answer_flags(signup: dict, transcript: str) -> list[dict]:
    """Real people describe their problem in their own words; a near-identical transcript to an
    earlier signup on the same waitlist means a shared script (click farm, coordinated signups)."""
    words = _words(transcript)
    if len(words) < SAME_ANSWER_MIN_WORDS:
        return []
    earlier = db.earlier_transcripts(signup["waitlist_id"], signup["id"], signup["created_at"])
    for other in earlier:
        if SequenceMatcher(None, words, _words(other["transcript"] or "")).ratio() >= SAME_ANSWER_RATIO:
            return [flag("same_answer", other["id"])]
    # Paraphrased scripts (an LLM rewording one answer for a click farm) keep the meaning.
    long_ones = {o["id"]: o["transcript"] for o in earlier
                 if len(_words(o["transcript"] or "")) >= SAME_MEANING_MIN_WORDS}
    if len(words) < SAME_MEANING_MIN_WORDS or not long_ones or not get_settings().openai_api_key:
        return []
    try:
        vecs = textsim.embed({signup["id"]: transcript, **long_ones})
    except Exception as e:   # the word check above still stands
        log.warning("meaning check skipped: %s", e)
        return []
    mine = vecs[signup["id"]]
    best = max(long_ones, key=lambda oid: float(mine @ vecs[oid]))
    if float(mine @ vecs[best]) >= SAME_MEANING_COSINE:
        return [flag("same_answer", best)]
    return []


def is_disposable(email: str) -> bool:
    domain = email.rsplit("@", 1)[-1].lower()
    # the list holds second-level domains only: mail.xyz.com is checked as xyz.com
    return domain in blocklist or ".".join(domain.split(".")[-2:]) in blocklist


def flag(code: str, detail: str = "") -> dict:
    return {"code": code, "detail": detail}


def basic_checks(signup: dict) -> list[dict]:
    flags = []
    if is_disposable(signup["email"]):
        flags.append(flag("disposable_email", signup["email"].rsplit("@", 1)[-1]))

    if signup.get("device_id"):
        # only earlier signups: re-scoring the first one must not blame it for a later one
        other = db.earlier_signup_with(signup["waitlist_id"], "device_id", signup["device_id"],
                                       signup["id"], signup["created_at"])
        if other:
            flags.append(flag("repeat_device", other["id"]))

    if signup.get("ip_hash"):
        since = datetime.now(timezone.utc) - REPEAT_IP_WINDOW
        others = db.count_signups_since(signup["waitlist_id"], "ip_hash", signup["ip_hash"],
                                        since, exclude_id=signup["id"])
        if others + 1 >= REPEAT_IP_MIN:
            flags.append(flag("repeat_ip", f"{others + 1} signups in 24h"))
    return flags
