"""
Tests for lightweight helpers in statschat.generative.utils.
"""

from statschat.generative.utils import deduplicator


def test_deduplicator_removes_duplicates_preserving_first():
    records = [
        {"title": "A", "date": "2024-01-01", "other": 1},
        {"title": "A", "date": "2024-01-01", "other": 2},
        {"title": "B", "date": "2024-01-02", "other": 3},
    ]

    deduped = deduplicator(records, keys=["title", "date"])

    assert len(deduped) == 2
    # Keeps first occurrence of duplicate
    assert deduped[0]["other"] == 1
    assert deduped[1]["title"] == "B"
