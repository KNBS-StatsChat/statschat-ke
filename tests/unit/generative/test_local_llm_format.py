"""
Tests for local_llm.format_response error handling.
"""

from statschat.generative.local_llm import format_response


def test_format_response_handles_invalid_json():
    result = format_response("==ANSWER==not-json")
    assert "error" in result
