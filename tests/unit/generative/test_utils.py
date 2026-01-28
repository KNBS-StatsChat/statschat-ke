"""
Tests for lightweight helpers in statschat.generative.utils.
"""

from statschat.generative.utils import (
    deduplicator,
    highlighter,
    time_decay,
    trim_context,
)
from statschat.generative.response_model import LlmResponse
from unittest.mock import MagicMock


def test_deduplicator_removes_duplicates_preserving_first():
    """Deduplicates records by key, keeping the first occurrence."""
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


def test_highlighter_marks_most_likely_answer():
    """Bold-marks the model's most-likely answer phrase in matched docs."""
    docs = [
        {
            "page_content": "The economy grew rapidly.",
            "title": "T",
            "date": "2024-01-01",
        }
    ]
    response = LlmResponse(
        answer_provided=True,
        most_likely_answer="economy grew",
        highlighting1=[],
        highlighting2=[],
        highlighting3=[],
        reasoning=None,
    )
    highlighted = highlighter(docs, response, logger=MagicMock())
    assert "<b>economy grew</b>" in highlighted[0]["page_content"].lower()


def test_time_decay_downweights_older_dates():
    """Assigns larger decay multipliers to older dates."""
    newer = time_decay("2024-01-01")
    older = time_decay("2020-01-01")
    assert older > newer


def test_trim_context_strips_edges():
    """Trims a context string to the intended core span."""
    assert trim_context("hello there world") == "there"
