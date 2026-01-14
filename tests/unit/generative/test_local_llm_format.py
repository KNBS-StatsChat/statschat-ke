"""
Tests for local_llm.format_response error handling.
"""

from statschat.generative.local_llm import format_response


def test_format_response_handles_invalid_json():
    """Returns an error payload when the response body is not valid JSON."""
    result = format_response("==ANSWER==not-json")
    assert "error" in result
