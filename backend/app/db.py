"""All Supabase access lives here, so tests can swap these functions out."""

import functools
import logging
import time
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from typing import Any

import httpx
from supabase import Client, create_client

from app.config import get_settings

AUDIO_BUCKET = "audio"
log = logging.getLogger("pod.db")


def retry(fn):
    """Supabase closes long-lived HTTP/2 connections now and then (GOAWAY); httpx raises instead of
    retrying. Seen in production as a 500 that lost a signup. Retry transport errors twice."""
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        for attempt in range(3):
            try:
                return fn(*args, **kwargs)
            except httpx.TransportError as e:
                if attempt == 2:
                    raise
                log.warning("db %s: %s, retrying", fn.__name__, type(e).__name__)
                time.sleep(0.3 * (attempt + 1))
    return wrapper


class DuplicateSignup(Exception):
    pass


@lru_cache
def client() -> Client:
    s = get_settings()
    return create_client(s.supabase_url, s.supabase_service_role_key)


@retry
def get_waitlist_by_slug(slug: str) -> dict | None:
    rows = client().table("waitlists").select("*").eq("slug", slug).limit(1).execute().data
    return rows[0] if rows else None


@retry
def get_waitlist(waitlist_id: str) -> dict | None:
    rows = client().table("waitlists").select("*").eq("id", waitlist_id).limit(1).execute().data
    return rows[0] if rows else None


@retry
def find_signup_by_email(waitlist_id: str, email: str) -> dict | None:
    rows = (
        client().table("signups").select("id")
        .eq("waitlist_id", waitlist_id).eq("email", email).limit(1).execute().data
    )
    return rows[0] if rows else None


@retry
def count_signups_since(waitlist_id: str, column: str, value: str, since: datetime,
                        exclude_id: str | None = None) -> int:
    q = (
        client().table("signups").select("id", count="exact")
        .eq("waitlist_id", waitlist_id).eq(column, value).gte("created_at", since.isoformat())
    )
    if exclude_id:
        q = q.neq("id", exclude_id)
    return q.execute().count or 0


@retry
def count_recent_by_ip(waitlist_id: str, ip_hash: str, hours: int = 1) -> int:
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    return count_signups_since(waitlist_id, "ip_hash", ip_hash, since)


@retry
def earlier_signup_with(waitlist_id: str, column: str, value: str, exclude_id: str,
                        before: str) -> dict | None:
    """The first signup on this waitlist with the same value, made before `before`."""
    rows = (
        client().table("signups").select("id")
        .eq("waitlist_id", waitlist_id).eq(column, value).neq("id", exclude_id)
        .lt("created_at", before).order("created_at").limit(1).execute().data
    )
    return rows[0] if rows else None


@retry
def earlier_transcripts(waitlist_id: str, exclude_id: str, before: str,
                        limit: int = 500) -> list[dict]:
    return (
        client().table("signups").select("id,transcript")
        .eq("waitlist_id", waitlist_id).neq("id", exclude_id).lt("created_at", before)
        .not_.is_("transcript", "null").order("created_at", desc=True).limit(limit)
        .execute().data
    )


@retry
def signups_on_domains(waitlist_id: str, domains: list[str]) -> list[dict]:
    rows = []
    for domain in domains:
        rows += (
            client().table("signups").select("id,email")
            .eq("waitlist_id", waitlist_id).ilike("email", f"%@{domain}").execute().data
        )
    return rows


@retry
def created_before(ids: list[str], before: str) -> set[str]:
    if not ids:
        return set()
    rows = client().table("signups").select("id").in_("id", ids).lt("created_at", before) \
        .execute().data
    return {r["id"] for r in rows}


@retry
def insert_signup(row: dict) -> dict:
    try:
        return client().table("signups").insert(row).execute().data[0]
    except Exception as e:  # postgrest APIError; 23505 = unique_violation
        if "23505" in str(e):
            # a retry after a dropped connection can collide with our own first attempt
            mine = client().table("signups").select("*").eq("id", row["id"]).execute().data
            if mine:
                return mine[0]
            raise DuplicateSignup from e
        raise


@retry
def get_signup(signup_id: str) -> dict | None:
    rows = client().table("signups").select("*").eq("id", signup_id).limit(1).execute().data
    return rows[0] if rows else None


@retry
def update_signup(signup_id: str, fields: dict[str, Any]) -> None:
    client().table("signups").update(fields).eq("id", signup_id).execute()


@retry
def signups_with_status(statuses: list[str]) -> list[dict]:
    return client().table("signups").select("id,status,flags").in_("status", statuses) \
        .execute().data


@retry
def upload_audio(path: str, data: bytes, content_type: str) -> None:
    # upsert: a retried upload must not fail on the file its first attempt already wrote
    client().storage.from_(AUDIO_BUCKET).upload(path, data, {"content-type": content_type,
                                                            "upsert": "true"})


@retry
def download_audio(path: str) -> bytes:
    return client().storage.from_(AUDIO_BUCKET).download(path)


@retry
def match_voices(waitlist_id: str, embedding: list[float], exclude_id: str,
                 threshold: float) -> list[dict]:
    return client().rpc("match_voices", {
        "p_waitlist_id": waitlist_id,
        "p_embedding": embedding,
        "p_exclude": exclude_id,
        "p_threshold": threshold,
    }).execute().data or []
