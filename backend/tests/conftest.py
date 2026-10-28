import os
from datetime import datetime, timezone

os.environ.setdefault("LOAD_MODELS", "false")
os.environ.setdefault("CHECK_EMAIL_DNS", "false")
os.environ.setdefault("WEB_ORIGIN", "http://localhost:3000")
try:  # optional static ffmpeg for laptops whose system ffmpeg is broken
    import imageio_ffmpeg
    os.environ.setdefault("FFMPEG_BIN", imageio_ffmpeg.get_ffmpeg_exe())
except ImportError:
    pass

import pytest

from app import db


class FakeDB:
    """In-memory stand-in for app.db, enough for intake and pipeline tests."""

    def __init__(self):
        self.waitlists = {}
        self.signups = {}
        self.files = {}
        self.voice_matches = []

    def add_waitlist(self, slug="demo", **kw):
        wl = {"id": f"wl-{slug}", "slug": slug, "product_name": slug.title(),
              "product_description": "", "question": "When did this last cost you?", **kw}
        self.waitlists[wl["id"]] = wl
        return wl

    def add_signup(self, **kw):
        row = {"id": kw.pop("id", f"s{len(self.signups) + 1}"), "status": "pending",
               "flags": [], "human_verdict": None, "pain_score": None,
               "created_at": datetime.now(timezone.utc).isoformat(), "audio_path": None,
               "device_id": None, "ip_hash": None, "email": f"u{len(self.signups)}@x.com", **kw}
        self.signups[row["id"]] = row
        return row

    # --- app.db interface ---
    def get_waitlist_by_slug(self, slug):
        return next((w for w in self.waitlists.values() if w["slug"] == slug), None)

    def get_waitlist(self, waitlist_id):
        return self.waitlists.get(waitlist_id)

    def find_signup_by_email(self, waitlist_id, email):
        return next((s for s in self.signups.values()
                     if s["waitlist_id"] == waitlist_id and s["email"] == email), None)

    def count_signups_since(self, waitlist_id, column, value, since, exclude_id=None):
        return sum(1 for s in self.signups.values()
                   if s["waitlist_id"] == waitlist_id and s.get(column) == value
                   and s["id"] != exclude_id
                   and datetime.fromisoformat(s["created_at"]) >= since)

    def count_recent_by_ip(self, waitlist_id, ip_hash, hours=1):
        return sum(1 for s in self.signups.values()
                   if s["waitlist_id"] == waitlist_id and s["ip_hash"] == ip_hash)

    def other_signup_with(self, waitlist_id, column, value, exclude_id):
        return next((s for s in self.signups.values()
                     if s["waitlist_id"] == waitlist_id and s.get(column) == value
                     and s["id"] != exclude_id), None)

    def insert_signup(self, row):
        if self.find_signup_by_email(row["waitlist_id"], row["email"]):
            raise db.DuplicateSignup
        return self.add_signup(**row)

    def get_signup(self, signup_id):
        return self.signups.get(signup_id)

    def update_signup(self, signup_id, fields):
        self.signups[signup_id].update(fields)

    def signups_with_status(self, statuses):
        return [{"id": s["id"]} for s in self.signups.values() if s["status"] in statuses]

    def upload_audio(self, path, data, content_type):
        self.files[path] = (data, content_type)

    def download_audio(self, path):
        return self.files[path][0]

    def match_voices(self, waitlist_id, embedding, exclude_id, threshold):
        return self.voice_matches


@pytest.fixture
def fake_db(monkeypatch):
    fake = FakeDB()
    for name in ("get_waitlist_by_slug", "get_waitlist", "find_signup_by_email",
                 "count_signups_since", "count_recent_by_ip", "other_signup_with",
                 "insert_signup", "get_signup", "update_signup", "signups_with_status",
                 "upload_audio", "download_audio", "match_voices"):
        monkeypatch.setattr(db, name, getattr(fake, name))
    return fake
