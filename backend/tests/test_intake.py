import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.routes import signups as route


@pytest.fixture
def client(fake_db, monkeypatch):
    monkeypatch.setattr(route, "process_signup", lambda signup_id: None)
    fake_db.add_waitlist("demo")
    with TestClient(app) as c:
        yield c


def form(**over):
    data = {"waitlist_slug": "demo", "email": "Ravi@Example.com", "consent": "true",
            "device_id": "dev1"}
    data.update(over)
    return data


def test_health(client):
    assert client.get("/health").json() == {"ok": True, "models_loaded": True}


def test_signup_with_audio(client, fake_db):
    r = client.post("/v1/signups", data=form(),
                    files={"audio": ("answer.webm", b"\x1aE\xdf\xa3fake", "audio/webm;codecs=opus")})
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "pending"
    row = fake_db.signups[body["signup_id"]]
    assert row["email"] == "ravi@example.com"
    assert row["audio_path"] == f"wl-demo/{body['signup_id']}.webm"
    assert row["audio_path"] in fake_db.files
    assert row["ip_hash"] and len(row["ip_hash"]) == 64


def test_signup_without_audio(client, fake_db):
    r = client.post("/v1/signups", data=form())
    assert r.status_code == 201
    assert fake_db.signups[r.json()["signup_id"]]["audio_path"] is None


@pytest.mark.parametrize("over,code", [
    ({"email": "not-an-email"}, "invalid_email"),
    ({"email": ""}, "invalid_email"),
    ({"consent": "false"}, "no_consent"),
])
def test_bad_fields(client, over, code):
    r = client.post("/v1/signups", data=form(**over))
    assert r.status_code == 400 and r.json() == {"error": code}


def test_bad_audio_type_and_size(client):
    r = client.post("/v1/signups", data=form(), files={"audio": ("x.txt", b"hi", "text/plain")})
    assert r.json() == {"error": "bad_audio"}
    big = b"0" * (3 * 1024 * 1024 + 1)
    r = client.post("/v1/signups", data=form(), files={"audio": ("x.webm", big, "audio/webm")})
    assert r.status_code == 400 and r.json() == {"error": "bad_audio"}


def test_safari_mp4_by_mime(client, fake_db):
    r = client.post("/v1/signups", data=form(), files={"audio": ("blob", b"mp4data", "audio/mp4")})
    assert r.status_code == 201
    assert fake_db.signups[r.json()["signup_id"]]["audio_path"].endswith(".mp4")


def test_unknown_waitlist(client):
    r = client.post("/v1/signups", data=form(waitlist_slug="nope"))
    assert r.status_code == 404 and r.json() == {"error": "waitlist_not_found"}


def test_duplicate_email(client):
    first = client.post("/v1/signups", data=form()).json()["signup_id"]
    r = client.post("/v1/signups", data=form(email="ravi@example.COM"))
    assert r.status_code == 409
    assert r.json() == {"error": "already_signed_up", "signup_id": first}


def test_rate_limit(client):
    for i in range(10):
        assert client.post("/v1/signups", data=form(email=f"u{i}@example.com")).status_code == 201
    r = client.post("/v1/signups", data=form(email="u11@example.com"))
    assert r.status_code == 429 and r.json() == {"error": "rate_limited"}


def test_client_ip_prefers_true_client_ip(client, fake_db):
    h = {"True-Client-IP": "1.1.1.1", "X-Forwarded-For": "6.6.6.6, 1.1.1.1"}
    a = client.post("/v1/signups", data=form(email="a@example.com"), headers=h).json()["signup_id"]
    h2 = {"True-Client-IP": "1.1.1.1", "X-Forwarded-For": "7.7.7.7"}
    b = client.post("/v1/signups", data=form(email="b@example.com"), headers=h2).json()["signup_id"]
    assert fake_db.signups[a]["ip_hash"] == fake_db.signups[b]["ip_hash"]


def test_status(client, fake_db):
    sid = client.post("/v1/signups", data=form()).json()["signup_id"]
    fake_db.update_signup(sid, {"status": "scored", "human_verdict": "verified", "pain_score": 80})
    assert client.get(f"/v1/signups/{sid}/status").json() == {
        "status": "scored", "human_verdict": "verified", "pain_score": 80}
    assert client.get("/v1/signups/not-a-uuid/status").status_code == 404


def test_cors_only_web_origin(client):
    ok = client.options("/v1/signups", headers={"Origin": "http://localhost:3000",
                                                 "Access-Control-Request-Method": "POST"})
    assert ok.headers.get("access-control-allow-origin") == "http://localhost:3000"
    bad = client.options("/v1/signups", headers={"Origin": "https://evil.com",
                                                  "Access-Control-Request-Method": "POST"})
    assert "access-control-allow-origin" not in bad.headers
