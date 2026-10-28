import numpy as np
import pytest

from app.pipeline import voice


def unit(v):
    v = np.asarray(v, dtype=float)
    return (v / np.linalg.norm(v)).tolist()


def test_similarity_of_unit_vectors():
    a = unit(np.ones(192))
    assert voice.similarity(a, a) == pytest.approx(1.0)
    b = unit(np.r_[np.ones(96), -np.ones(96)])
    assert voice.similarity(a, b) == pytest.approx(0.0)


def test_same_voice_flag_points_to_match(fake_db):
    s = fake_db.add_signup(waitlist_id="wl")
    fake_db.voice_matches = [{"id": "s-earlier", "similarity": 0.81}]
    assert voice.same_voice_flags(s, unit(np.ones(192))) == [
        {"code": "same_voice", "detail": "s-earlier"}]


def test_no_match_no_flag(fake_db):
    s = fake_db.add_signup(waitlist_id="wl")
    assert voice.same_voice_flags(s, unit(np.ones(192))) == []
