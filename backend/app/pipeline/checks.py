from email_validator import EmailNotValidError, caching_resolver, validate_email

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
