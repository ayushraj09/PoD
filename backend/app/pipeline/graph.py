"""Fake-ring detection on TigerGraph Savanna (stage A8). Optional: skipped when TG_HOST is empty.

A ring is 3+ signups joined by shared devices or matching voices, with at least one voice
match among them. Every member gets `ring_member` and its verdict is recomputed.
"""

import logging
import time

from app import db
from app.config import get_settings
from app.pipeline.checks import flag
from app.pipeline.verdict import decide

log = logging.getLogger("pod.graph")
RING_MIN = 3
RETRIES = 6  # free workspaces auto-stop; waking takes ~15-30 s and that request isn't queued (~60 s total)

_conn = None


def _connect():
    global _conn
    if _conn is None:
        from pyTigerGraph import TigerGraphConnection

        s = get_settings()
        conn = TigerGraphConnection(host=s.tg_host, graphname=s.tg_graph, gsqlSecret=s.tg_secret)
        conn.getToken(s.tg_secret)
        _conn = conn
    return _conn


def _with_retry(fn):
    global _conn
    for attempt in range(RETRIES):
        try:
            return fn(_connect())
        except Exception as e:
            _conn = None  # reconnect (and re-auth) on the next try
            if attempt == RETRIES - 1:
                raise
            wait = 2 ** (attempt + 1)
            log.info("tigergraph busy/asleep (%s), retry in %ss", type(e).__name__, wait)
            time.sleep(wait)


def write_signup(conn, signup: dict) -> None:
    sid, wl = signup["id"], signup["waitlist_id"]
    conn.upsertVertex("Signup", sid, {"waitlist": wl, "verdict": signup.get("human_verdict") or "",
                                      "trust": signup.get("trust_score") or 0})
    links = [("Device", signup.get("device_id"), "USED_DEVICE"),
             ("IpHash", signup.get("ip_hash"), "FROM_IP"),
             ("EmailDomain", signup["email"].rsplit("@", 1)[-1], "HAS_DOMAIN")]
    for vtype, value, etype in links:
        if value:
            vid = f"{wl}:{value}"
            conn.upsertVertex(vtype, vid, {})
            conn.upsertEdge("Signup", sid, etype, vtype, vid, {})
    for f in signup.get("flags") or []:
        if f["code"] == "same_voice" and f.get("detail"):
            conn.upsertEdge("Signup", sid, "SOUNDS_LIKE", "Signup", f["detail"], {})


def find_ring(conn, signup_id: str) -> list[str]:
    res = conn.runInstalledQuery("ring_of", {"seed": (signup_id,)})  # 1-tuple = vertex param
    out = {k: v for part in res for k, v in part.items()}
    members, voice_links = out.get("members", []), out.get("voice_links", 0)
    return sorted(members) if len(members) >= RING_MIN and voice_links > 0 else []


def _set_flags(row: dict, flags: list[dict]) -> None:
    trust, verdict = decide(flags, has_audio=bool(row.get("audio_path")))
    db.update_signup(row["id"], {"flags": flags, "trust_score": trust, "human_verdict": verdict})


def mark_ring(member_ids: list[str]) -> int:
    """Flags ring members and recomputes their verdicts. Returns rows changed.

    A ring is usually one real person behind many accounts, so its earliest member keeps its
    verdict if its own checks were clean: "1 real human, 8 accounts", not 0. A member that
    tripped any check itself (AI audio, copied script, throwaway email, ...) is never exempt.
    """
    rows = [r for r in (db.get_signup(m) for m in member_ids) if r and r.get("status") == "scored"]
    rows.sort(key=lambda r: r["created_at"])
    own = lambda r: [f for f in r.get("flags") or [] if f["code"] != "ring_member"]
    original = rows[0]["id"] if rows and not own(rows[0]) else None
    changed = 0
    for row in rows:
        flags = row.get("flags") or []
        in_ring = any(f["code"] == "ring_member" for f in flags)
        if row["id"] == original:
            if in_ring:   # flagged by an earlier version of this rule
                _set_flags(row, own(row))
                changed += 1
            continue
        if not in_ring:
            _set_flags(row, flags + [flag("ring_member", f"group of {len(member_ids)}")])
            changed += 1
    return changed


def linked_signup_ids(signup: dict) -> list[str]:
    return sorted({f["detail"] for f in signup.get("flags") or []
                   if f["code"] in ("same_voice", "repeat_device") and f.get("detail")})


def check_ring(signup: dict) -> None:
    """Runs after scoring. Never raises: signups must not fail because of the graph."""
    if not get_settings().tg_host:
        return
    try:
        _with_retry(lambda c: write_signup(c, signup))
        # Self-repair: re-write the earlier signups this one points at. If TigerGraph was asleep
        # when they were scored, their writes were lost and the ring would miss them.
        for linked_id in linked_signup_ids(signup):
            linked = db.get_signup(linked_id)
            if linked and linked.get("status") == "scored":
                _with_retry(lambda c, row=linked: write_signup(c, row))
        members = _with_retry(lambda c: find_ring(c, signup["id"]))
        if members:
            n = mark_ring(members)
            log.info("signup %s ring of %d, %d newly flagged", signup["id"], len(members), n)
    except Exception:
        log.exception("ring check skipped for %s", signup["id"])
