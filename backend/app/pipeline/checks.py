from datetime import datetime, timedelta, timezone

from disposable_email_domains import blocklist
from email_validator import EmailNotValidError, caching_resolver, validate_email

from app import db

REPEAT_IP_MIN = 3          # this many signups (including this one) from one network...
REPEAT_IP_WINDOW = timedelta(hours=24)  # ...within this window

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
