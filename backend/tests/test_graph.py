import pytest

from app.config import get_settings
from app.pipeline import graph


class FakeConn:
    def __init__(self, result):
        self.vertices, self.edges, self.result = [], [], result

    def upsertVertex(self, vtype, vid, attrs):
        self.vertices.append((vtype, vid))

    def upsertEdge(self, st, sid, etype, tt, tid, attrs):
        self.edges.append((sid, etype, tid))

    def runInstalledQuery(self, name, params):
        return self.result


def test_write_signup_links_are_per_waitlist():
    conn = FakeConn([])
    graph.write_signup(conn, {"id": "s2", "waitlist_id": "wl", "email": "a@gmail.com",
                              "device_id": "d1", "ip_hash": "h1",
                              "flags": [{"code": "same_voice", "detail": "s1"}]})
    assert ("s2", "USED_DEVICE", "wl:d1") in conn.edges
    assert ("s2", "FROM_IP", "wl:h1") in conn.edges
    assert ("s2", "HAS_DOMAIN", "wl:gmail.com") in conn.edges
    assert ("s2", "SOUNDS_LIKE", "s1") in conn.edges


@pytest.mark.parametrize("members,voice_links,ring", [
    (["a", "b", "c"], 2, True),
    (["a", "b", "c"], 0, False),   # devices only (e.g. identical phones): not a ring
    (["a", "b"], 2, False),        # too small
])
def test_find_ring_rule(members, voice_links, ring):
    conn = FakeConn([{"members": members, "voice_links": voice_links}])
    assert bool(graph.find_ring(conn, "a")) is ring


def test_mark_ring_recomputes_verdict(fake_db):
    a = fake_db.add_signup(waitlist_id="wl", status="scored", audio_path="x", flags=[],
                           trust_score=100, human_verdict="verified")
    b = fake_db.add_signup(waitlist_id="wl", status="scored", audio_path="x",
                           flags=[{"code": "same_voice", "detail": a["id"]}])
    assert graph.mark_ring([a["id"], b["id"]]) == 2
    assert fake_db.signups[a["id"]]["human_verdict"] == "suspicious"   # 100 - 40
    assert fake_db.signups[b["id"]]["human_verdict"] == "fake"         # 100 - 50 - 40
    assert graph.mark_ring([a["id"], b["id"]]) == 0                    # idempotent


def test_check_ring_never_raises(monkeypatch):
    monkeypatch.setattr(get_settings(), "tg_host", "https://example.tgcloud.io")
    monkeypatch.setattr(graph, "RETRIES", 1)
    monkeypatch.setattr(graph, "_connect", lambda: (_ for _ in ()).throw(RuntimeError("asleep")))
    graph.check_ring({"id": "s1", "waitlist_id": "wl", "email": "a@b.com"})


def test_skipped_without_host(monkeypatch):
    monkeypatch.setattr(graph, "_connect", lambda: pytest.fail("should not connect"))
    graph.check_ring({"id": "s1", "waitlist_id": "wl", "email": "a@b.com"})
