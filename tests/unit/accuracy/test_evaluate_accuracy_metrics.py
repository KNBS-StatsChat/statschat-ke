"""Unit tests for lightweight accuracy-metric helpers."""

from argparse import Namespace
from datetime import datetime
import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pandas as pd


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


def test_primary_context_text_returns_first_chunk():
    module = _load_evaluate_accuracy()

    text = "First context chunk.\n---\nSecond context chunk."

    assert module.primary_context_text(text) == "First context chunk."


def test_append_run_history_appends_rows(tmp_path, monkeypatch):
    module = _load_evaluate_accuracy()

    monkeypatch.setattr(
        module,
        "load_runtime_search_config",
        lambda _api_mode=None: {
            "provider": "openrouter",
            "model": "openai/gpt-5.4-mini",
            "k_docs": "8",
            "k_contexts": "5",
            "answer_threshold": "1.1",
            "document_threshold": "0.9",
        },
    )

    args = Namespace(
        api_mode="cloud",
        host="http://127.0.0.1:8001",
        excel=Path("tests/accuracy/sample.xlsx"),
        content_type="all",
        timeout=420.0,
        max_rows=None,
        skip_rows=0,
        retrieval_k=8,
        no_api_debug=False,
        similarity_threshold=85.0,
        f1_threshold=0.80,
        semantic_threshold=0.90,
        abs_tol=0.1,
        rel_tol=0.01,
    )
    summary = {
        "api_modes_observed": "cloud",
        "total_evaluated": 37,
        "answerable_count": 37,
        "unanswerable_count": 0,
        "overall_accuracy": 0.595,
    }

    first_run_dir = tmp_path / "tests" / "accuracy" / "runs" / "cloud" / "run-1"
    first_run_dir.mkdir(parents=True)
    first_start = datetime(2026, 4, 7, 10, 0, 0)
    first_end = datetime(2026, 4, 7, 10, 5, 0)

    history_path = module.append_run_history(
        first_run_dir, args, summary, first_start, first_end
    )

    first_df = pd.read_csv(history_path)
    assert len(first_df) == 1
    assert first_df.loc[0, "provider"] == "openrouter"
    assert first_df.loc[0, "model"] == "openai/gpt-5.4-mini"
    assert first_df.loc[0, "api_modes_observed"] == "cloud"
    assert float(first_df.loc[0, "overall_accuracy"]) == 0.595

    second_run_dir = tmp_path / "tests" / "accuracy" / "runs" / "cloud" / "run-2"
    second_run_dir.mkdir(parents=True)
    second_start = datetime(2026, 4, 7, 11, 0, 0)
    second_end = datetime(2026, 4, 7, 11, 2, 30)

    module.append_run_history(second_run_dir, args, summary, second_start, second_end)

    second_df = pd.read_csv(history_path)
    assert len(second_df) == 2
    assert second_df.loc[1, "run_dir"].endswith("run-2")
    assert bool(second_df.loc[1, "api_debug_requested"]) is True


def test_load_runtime_search_config_reads_cloud_model_from_main_config(monkeypatch):
    module = _load_evaluate_accuracy()

    class DummyStatschat:
        @staticmethod
        def load_config(name="main"):
            return {
                "search": {
                    "provider": "openrouter",
                    "generative_model_name": "mistralai/Mistral-7B-Instruct-v0.3",
                    "generative_model_name_local": "mistralai/Mistral-7B-Instruct-v0.3",
                    "generative_model_name_cloud": "openai/gpt-5.4-mini",
                    "k_docs": 8,
                    "k_contexts": 5,
                    "answer_threshold": 1.1,
                    "document_threshold": 0.9,
                }
            }

    monkeypatch.setitem(sys.modules, "statschat", DummyStatschat)

    runtime_config = module.load_runtime_search_config("cloud")

    assert runtime_config["provider"] == "openrouter"
    assert runtime_config["model"] == "openai/gpt-5.4-mini"


def test_load_runtime_search_config_reads_local_model_from_main_config(monkeypatch):
    module = _load_evaluate_accuracy()

    class DummyStatschat:
        @staticmethod
        def load_config(name="main"):
            return {
                "search": {
                    "provider": "openrouter",
                    "generative_model_name": "mistralai/Mistral-7B-Instruct-v0.3",
                    "generative_model_name_local": "mistralai/Mistral-7B-Instruct-v0.3",
                    "generative_model_name_cloud": "openai/gpt-5.4-mini",
                    "k_docs": 8,
                    "k_contexts": 5,
                    "answer_threshold": 1.1,
                    "document_threshold": 0.9,
                }
            }

    monkeypatch.setitem(sys.modules, "statschat", DummyStatschat)

    runtime_config = module.load_runtime_search_config("local")

    assert runtime_config["provider"] == "openrouter"
    assert runtime_config["model"] == "mistralai/Mistral-7B-Instruct-v0.3"


def test_extract_reference_details_combines_base_url_and_page_fragment():
    module = _load_evaluate_accuracy()

    payload = {
        "references": [
            {
                "url": "https://example.com/doc1.pdf",
                "page_url": "#page=2",
            }
        ]
    }

    (
        reference_url,
        reference_doc_id,
        reference_page,
        reference_count,
        reference_urls,
    ) = module.extract_reference_details(payload)

    assert reference_url == "https://example.com/doc1.pdf#page=2"
    assert reference_doc_id == "doc1"
    assert reference_page == 2
    assert reference_count == 1
    assert reference_urls == ["https://example.com/doc1.pdf#page=2"]


def test_evaluate_cloud_requests_debug_and_populates_context(monkeypatch):
    module = _load_evaluate_accuracy()

    df = pd.DataFrame(
        [
            {
                "query_id": "Q001",
                "query_text": "What is the inflation rate in February 2025?",
                "golden_answer": "0.035",
                "relevant_doc_ids": "doc1.pdf",
                "evidence_locations": "doc1.pdf p.2",
                "source_text": "Inflation was 3.5 per cent in February 2025.",
                "should_answer": True,
                "Reviewers": "AB;CD",
            }
        ]
    )

    captured: dict[str, object] = {}

    class DummyResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "question": "What is the inflation rate in February 2025?",
                "content_type": "all",
                "answer": "3.5 per cent",
                "references": [
                    {
                        "page_url": "https://example.com/doc1.pdf#page=2",
                        "page_content": "Inflation was 3.5 per cent in February 2025.",
                        "score": 0.123456,
                        "title": "CPI February 2025",
                    },
                    {
                        "page_url": "https://example.com/doc2.pdf#page=1",
                        "page_content": "A secondary chunk.",
                        "score": 0.987654,
                        "title": "CPI March 2025",
                    },
                ],
                "debug_response": {
                    "reasoning": "Picked the February 2025 bulletin.",
                    "highlighting1": ["3.5 per cent"],
                },
            }

    def fake_get(url, params, timeout):
        captured["url"] = url
        captured["params"] = params
        captured["timeout"] = timeout
        return DummyResponse()

    monkeypatch.setattr(module.requests, "get", fake_get)

    results = module.evaluate(
        df=df,
        base_url="http://example.test",
        content_type="all",
        api_mode="cloud",
        timeout=12.0,
        max_rows=None,
        sleep_seconds=0.0,
        refusal_phrases=module.DEFAULT_REFUSAL_PHRASES,
        similarity_threshold=85.0,
        abs_tol=0.1,
        rel_tol=0.01,
        retrieval_k=5,
        compute_retrieval=False,
        semantic_model=None,
        f1_threshold=0.80,
        semantic_threshold=0.90,
        skip_rows=0,
        request_api_debug=True,
    )

    assert captured["params"]["debug"] == "true"
    assert len(results) == 1
    result = results[0]
    assert result.api_mode == "cloud"
    assert result.reasoning == "Picked the February 2025 bulletin."
    assert result.context_texts is not None
    assert "Inflation was 3.5 per cent" in result.context_texts
    assert (
        result.predicted_source_text == "Inflation was 3.5 per cent in February 2025."
    )
    assert result.reference_doc_ids_all == "doc1;doc2"
    assert result.reference_pages_all == "2;1"
    assert result.any_reference_doc_match is True
    assert result.any_reference_page_match is True
    assert result.is_correct is True
