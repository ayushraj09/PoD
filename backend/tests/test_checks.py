from app.pipeline.checks import basic_checks, is_disposable


def codes(flags):
    return [f["code"] for f in flags]


def test_clean_signup(fake_db):
    s = fake_db.add_signup(waitlist_id="wl", email="ravi@gmail.com", device_id="d1", ip_hash="ip1")
    assert basic_checks(s) == []


def test_disposable_email(fake_db):
    s = fake_db.add_signup(waitlist_id="wl", email="x@mailinator.com")
    assert codes(basic_checks(s)) == ["disposable_email"]
    assert is_disposable("x@sub.mailinator.com")
    assert not is_disposable("x@gmail.com")


def test_repeat_device(fake_db):
    first = fake_db.add_signup(waitlist_id="wl", device_id="d1")
    s = fake_db.add_signup(waitlist_id="wl", device_id="d1")
    flags = basic_checks(s)
    assert codes(flags) == ["repeat_device"]
    assert flags[0]["detail"] == first["id"]


def test_same_device_other_waitlist_is_fine(fake_db):
    fake_db.add_signup(waitlist_id="other", device_id="d1")
    s = fake_db.add_signup(waitlist_id="wl", device_id="d1")
    assert basic_checks(s) == []


def test_repeat_ip_needs_three(fake_db):
    fake_db.add_signup(waitlist_id="wl", ip_hash="ip1")
    second = fake_db.add_signup(waitlist_id="wl", ip_hash="ip1")
    assert basic_checks(second) == []
    third = fake_db.add_signup(waitlist_id="wl", ip_hash="ip1")
    assert codes(basic_checks(third)) == ["repeat_ip"]
