"""Unit tests for statschat.embedding.latest_flag_helpers."""

from datetime import datetime

import pytest

from statschat.embedding import latest_flag_helpers


def test_time_decay_no_decay_returns_one(monkeypatch):
    """latest=0 currently raises due to division by zero in formula."""

    class _FixedDateTime:
        @classmethod
        def now(cls):
            return datetime(2026, 1, 14)

        @classmethod
        def strptime(cls, date_str, fmt):
            return datetime.strptime(date_str, fmt)

    monkeypatch.setattr(latest_flag_helpers, "datetime", _FixedDateTime)
    with pytest.raises(ZeroDivisionError):
        latest_flag_helpers.time_decay("01 January 2026", latest=0)


def test_time_decay_recent_is_higher_than_old(monkeypatch):
    """More recent dates should have higher weight than older ones."""

    class _FixedDateTime:
        @classmethod
        def now(cls):
            return datetime(2026, 1, 14)

        @classmethod
        def strptime(cls, date_str, fmt):
            return datetime.strptime(date_str, fmt)

    monkeypatch.setattr(latest_flag_helpers, "datetime", _FixedDateTime)
    recent = latest_flag_helpers.time_decay("01 January 2026", latest=1)
    old = latest_flag_helpers.time_decay("01 January 2000", latest=1)
    assert recent > old


def test_get_latest_flag_explicit_latest_weight_true():
    request_args = {"latest_weight": "On"}
    assert latest_flag_helpers.get_latest_flag(request_args, latest_max=2) == 2


def test_get_latest_flag_explicit_latest_weight_false():
    request_args = {"latest_weight": "off"}
    assert latest_flag_helpers.get_latest_flag(request_args, latest_max=2) == 0


def test_get_latest_flag_query_contains_latest():
    request_args = {"q": "latest economic survey"}
    assert latest_flag_helpers.get_latest_flag(request_args, latest_max=2) == 2


def test_get_latest_flag_default_half():
    request_args = {"q": "economic survey"}
    assert latest_flag_helpers.get_latest_flag(request_args, latest_max=2) == 1
