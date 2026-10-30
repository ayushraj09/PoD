import httpx
import pytest

from app import db


def test_retries_dropped_connection(monkeypatch):
    monkeypatch.setattr(db.time, "sleep", lambda s: None)
    calls = []

    @db.retry
    def flaky():
        calls.append(1)
        if len(calls) < 3:
            raise httpx.RemoteProtocolError("ConnectionTerminated")
        return "ok"

    assert flaky() == "ok" and len(calls) == 3


def test_gives_up_after_three_tries(monkeypatch):
    monkeypatch.setattr(db.time, "sleep", lambda s: None)

    @db.retry
    def down():
        raise httpx.ConnectError("down")

    with pytest.raises(httpx.ConnectError):
        down()


def test_other_errors_are_not_retried():
    calls = []

    @db.retry
    def bad():
        calls.append(1)
        raise ValueError("bug")

    with pytest.raises(ValueError):
        bad()
    assert len(calls) == 1
