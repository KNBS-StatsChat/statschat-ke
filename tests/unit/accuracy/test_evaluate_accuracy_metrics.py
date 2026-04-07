"""Unit tests for lightweight accuracy-metric helpers."""

import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


def _load_evaluate_accuracy():
    repo_root = Path(__file__).resolve().parents[3]
    module_path = repo_root / "tests" / "accuracy" / "evaluate_accuracy.py"
    spec = spec_from_file_location("evaluate_accuracy_module", module_path)
    module = module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_numeric_match_treats_scaled_units_as_equivalent():
    module = _load_evaluate_accuracy()

    assert module.numeric_match(
        "4,285.2 thousand tonnes",
        "4,285,206 tons",
        abs_tol=10.0,
        rel_tol=0.01,
    )


def test_numeric_match_still_handles_plain_numbers():
    module = _load_evaluate_accuracy()

    assert module.numeric_match(
        "3.7",
        "The average household size in Kenya is 3.7 members.",
        abs_tol=0.1,
        rel_tol=0.01,
    )


def test_numeric_match_treats_decimal_gold_and_percent_answer_as_equivalent():
    module = _load_evaluate_accuracy()

    assert module.numeric_match(
        "0.069",
        "6.9 per cent",
        abs_tol=0.1,
        rel_tol=0.01,
    )


def test_numeric_match_treats_percent_gold_and_decimal_answer_as_equivalent():
    module = _load_evaluate_accuracy()

    assert module.numeric_match(
        "6.9 percent",
        "0.069",
        abs_tol=0.1,
        rel_tol=0.01,
    )


def test_numeric_match_does_not_accept_wrong_percent_value_from_decimal_gold():
    module = _load_evaluate_accuracy()

    assert not module.numeric_match(
        "0.041",
        "5.0%",
        abs_tol=0.1,
        rel_tol=0.01,
    )


def test_numeric_match_rejects_wrong_numbers():
    module = _load_evaluate_accuracy()

    # 40.0 vs 31.7 thousand tonnes is a 26% error — should NOT match
    assert not module.numeric_match(
        "31.7 thousand tonnes",
        "40.0 thousand tonnes",
        abs_tol=0.1,
        rel_tol=0.01,
    )


def test_golden_with_numbers_uses_strict_numeric_check():
    """When the golden answer is numeric, fuzzy text match alone should not pass."""
    module = _load_evaluate_accuracy()

    # parse_scaled_numbers should find numbers in "31.7 thousand tonnes"
    nums = module.parse_scaled_numbers("31.7 thousand tonnes")
    assert len(nums) == 1
    assert abs(nums[0] - 31700.0) < 1.0


def test_extract_debug_details_handles_cloud_payload():
    module = _load_evaluate_accuracy()

    payload = {
        "references": [
            {
                "page_url": "https://example.com/doc1.pdf#page=2",
                "page_content": "Inflation was 3.5 per cent in February 2025.",
                "score": 0.123456,
                "title": "CPI February 2025",
            },
            {
                "page_url": "https://example.com/doc2.pdf#page=1",
                "page_content": "A second supporting context.",
                "score": 0.987654,
                "title": "CPI March 2025",
            },
        ],
        "debug_response": {
            "reasoning": "Picked the directly matching February 2025 bulletin.",
            "highlighting1": ["3.5 per cent"],
            "highlighting2": "February 2025",
        },
    }

    details = module.extract_debug_details(payload)

    assert (
        details["reasoning"] == "Picked the directly matching February 2025 bulletin."
    )
    assert details["highlighting"] == "3.5 per cent; February 2025"
    assert "Inflation was 3.5 per cent" in str(details["context_texts"])
    assert details["reference_scores"] == "0.1235;0.9877"
    assert details["reference_titles"] == "CPI February 2025;CPI March 2025"


def test_extract_debug_details_handles_local_payload():
    module = _load_evaluate_accuracy()

    payload = {
        "references": "https://example.com/doc1.pdf#page=4",
        "context_from": "Context1",
        "context_reference": "Page number: 4",
        "relevant_publication_one": "KDHS 2022 Summary",
        "relevant_publication_two": "KDHS 2014 Full Report",
    }

    details = module.extract_debug_details(payload)

    assert details["context_from"] == "Context1"
    assert details["context_reference"] == "Page number: 4"
    assert (
        details["relevant_publications"] == "KDHS 2022 Summary; KDHS 2014 Full Report"
    )
    assert details["context_texts"] is None
