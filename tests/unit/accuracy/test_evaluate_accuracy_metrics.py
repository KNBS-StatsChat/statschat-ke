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


def _evaluate_unanswerable_response(module, monkeypatch, answer: object):
    df = pd.DataFrame(
        [
            {
                "query_id": "QQ038",
                "query_text": "What was Tanzania's GDP growth rate in 2023?",
                "golden_answer": None,
                "relevant_doc_ids": None,
                "evidence_locations": None,
                "source_text": None,
                "should_answer": False,
                "Reviewers": None,
            }
        ]
    )

    class DummyResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "question": "What was Tanzania's GDP growth rate in 2023?",
                "content_type": "all",
                "answer": answer,
                "references": [],
                "debug_response": {},
            }

    def fake_get(url, params, timeout):
        return DummyResponse()

    monkeypatch.setattr(module.requests, "get", fake_get)

    return module.evaluate(
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
        retrieval_k=8,
        compute_retrieval=False,
        semantic_model=None,
        f1_threshold=0.80,
        semantic_threshold=0.90,
        skip_rows=0,
        request_api_debug=True,
    )[0]


def test_numeric_match_treats_scaled_units_as_equivalent():
    module = _load_evaluate_accuracy()

    assert module.numeric_match(
        "4,285.2 thousand tonnes",
        "4,285,206 tons",
        abs_tol=10.0,
        rel_tol=0.01,
    )


def test_numeric_match_treats_table_thousands_marker_as_equivalent():
    module = _load_evaluate_accuracy()

    assert module.numeric_match(
        "Turkana, with 8,625.2 thousand",
        "Turkana had the largest meat goat population in Kenya in 2024, "
        "with 8,625.2 ('000).",
        abs_tol=0.1,
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


def test_run_metadata_prefers_live_api_health_model(tmp_path, monkeypatch):
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
        similarity_threshold=85.0,
        f1_threshold=0.80,
        semantic_threshold=0.90,
    )
    summary = {
        "api_modes_observed": "cloud",
        "total_evaluated": 74,
        "answerable_count": 61,
        "unanswerable_count": 13,
        "overall_accuracy": 0.946,
        "answerable_accuracy": 0.934,
        "unanswerable_accuracy": 1.0,
        "error_count": 0,
    }
    api_health = {
        "status": "ok",
        "provider": "openrouter",
        "model": "mistralai/mistral-small-3.1-24b-instruct",
    }

    module.save_run_metadata(
        tmp_path,
        args,
        summary,
        datetime(2026, 4, 20, 14, 0, 0),
        datetime(2026, 4, 20, 14, 5, 0),
        api_health=api_health,
    )

    metadata = (tmp_path / "run_metadata.txt").read_text(encoding="utf-8")
    assert "Model:              mistralai/mistral-small-3.1-24b-instruct" in metadata
    assert "Model source:       api_health" in metadata
    assert "Config model:       openai/gpt-5.4-mini" in metadata


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


def test_extract_reference_details_prefers_full_page_url_over_base_url():
    module = _load_evaluate_accuracy()

    payload = {
        "references": [
            {
                "url": "https://example.com/doc1.pdf",
                "page_url": "https://example.com/doc1.pdf#page=7",
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

    assert reference_url == "https://example.com/doc1.pdf#page=7"
    assert reference_doc_id == "doc1"
    assert reference_page == 7
    assert reference_count == 1
    assert reference_urls == ["https://example.com/doc1.pdf#page=7"]


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
    assert result.pipeline_doc_hit_at_1 is True
    assert result.pipeline_doc_hit_at_k is True
    assert result.pipeline_precision_at_k == 0.2
    assert result.pipeline_recall_at_k == 1.0
    assert result.pipeline_mrr == 1.0
    assert result.pipeline_page_precision_at_k == 0.2
    assert result.pipeline_page_recall_at_k == 1.0
    assert result.pipeline_page_mrr == 1.0
    assert result.scoring_method == "numeric_match"
    assert result.is_correct is True


def test_validate_rows_allows_blank_unanswerable_fields():
    module = _load_evaluate_accuracy()

    df = pd.DataFrame(
        [
            {
                "query_id": "QQ038",
                "query_text": "What was Tanzania's GDP growth rate in 2023?",
                "golden_answer": None,
                "relevant_doc_ids": None,
                "evidence_locations": None,
                "source_text": None,
                "should_answer": False,
                "Reviewers": None,
            }
        ]
    )

    issues = module.validate_rows(
        df,
        require_reviewers=False,
        query_id_prefix="QQ",
    )

    assert issues == []


def test_evaluate_unanswerable_empty_answer_counts_as_correct_refusal(monkeypatch):
    module = _load_evaluate_accuracy()

    result = _evaluate_unanswerable_response(module, monkeypatch, "")

    assert result.is_refusal is True
    assert result.model_answered is False
    assert result.correct_refusal is True
    assert result.false_answer is False
    assert result.is_correct is True
    assert result.scoring_method == "correct_refusal"


def test_evaluate_unanswerable_substantive_answer_counts_as_false_answer(monkeypatch):
    module = _load_evaluate_accuracy()

    result = _evaluate_unanswerable_response(
        module,
        monkeypatch,
        "Tanzania's GDP grew by 5.2 per cent in 2023.",
    )

    assert result.is_refusal is False
    assert result.model_answered is True
    assert result.correct_refusal is False
    assert result.false_answer is True
    assert result.is_correct is False
    assert result.scoring_method == "false_answer"


def test_results_to_dataframe_renames_faiss_proxy_columns():
    module = _load_evaluate_accuracy()

    result = module.EvaluationResult(
        query_id="Q001",
        query_text="Question",
        should_answer=True,
        golden_answer="42",
        predicted_answer="42",
        predicted_relevant_doc_ids=None,
        predicted_evidence_locations=None,
        predicted_source_text=None,
        model_answered=True,
        correct_refusal=False,
        false_answer=False,
        answered_when_expected=True,
        answer_missing=False,
        api_mode="cloud",
        reference_count=1,
        reference_url="https://example.com/doc1.pdf#page=2",
        reference_doc_id="doc1",
        reference_page=2,
        reference_doc_ids_all="doc1",
        reference_pages_all="2",
        reference_doc_match=True,
        any_reference_doc_match=True,
        evidence_page_match=True,
        any_reference_page_match=True,
        doc_hit_at_1=True,
        doc_hit_at_k=True,
        exact_match=1,
        token_f1=1.0,
        semantic_similarity=1.0,
        is_refusal=False,
        is_correct=True,
        similarity_score=100.0,
        precision_at_k=1.0,
        recall_at_k=1.0,
        mrr=1.0,
        ndcg=1.0,
        retrieval_metric_source="local_similarity_search_proxy",
        retrieved_doc_ids="doc1",
        error=None,
    )

    df = module.results_to_dataframe([result])

    assert "precision_at_k" not in df.columns
    assert "faiss_proxy_precision_at_k" in df.columns
    assert "faiss_proxy_doc_hit_at_k" in df.columns
    assert "faiss_proxy_metric_source" in df.columns


def test_enrich_saved_results_dataframe_adds_pipeline_metrics_and_scoring_method():
    module = _load_evaluate_accuracy()

    results_df = pd.DataFrame(
        [
            {
                "query_id": "Q001",
                "query_text": "What is the inflation rate in February 2025?",
                "should_answer": True,
                "golden_answer": "0.035",
                "predicted_answer": "3.5 per cent",
                "predicted_evidence_locations": "doc1:p.2;doc2:p.1",
                "reference_doc_ids_all": "doc1;doc2",
                "reference_doc_id": "doc1",
                "reference_page": 2,
                "exact_match": 0,
                "token_f1": 0.0,
                "semantic_similarity": None,
                "similarity_score": 10.0,
                "is_refusal": False,
                "doc_hit_at_1": True,
                "doc_hit_at_k": True,
                "precision_at_k": 0.2,
                "recall_at_k": 1.0,
                "mrr": 1.0,
                "ndcg": 1.0,
                "retrieval_metric_source": "local_similarity_search_proxy",
                "retrieved_doc_ids": "doc1;doc2",
                "is_correct": False,
            }
        ]
    )
    qa_df = pd.DataFrame(
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

    enriched = module.enrich_saved_results_dataframe(
        results_df,
        qa_df,
        retrieval_k=5,
        similarity_threshold=85.0,
        abs_tol=0.1,
        rel_tol=0.01,
        f1_threshold=0.80,
        semantic_threshold=0.90,
    )

    assert "faiss_proxy_precision_at_k" in enriched.columns
    assert float(enriched.loc[0, "pipeline_precision_at_k"]) == 0.2
    assert float(enriched.loc[0, "pipeline_page_precision_at_k"]) == 0.2
    assert enriched.loc[0, "pipeline_doc_hit_at_1"] is True
    assert bool(enriched.loc[0, "is_correct"]) is True
    assert enriched.loc[0, "scoring_method"] == "numeric_match"


def test_enrich_saved_results_dataframe_raises_on_zero_query_id_matches():
    module = _load_evaluate_accuracy()

    results_df = pd.DataFrame(
        [
            {
                "query_id": "QQ001",
                "query_text": "Question",
                "should_answer": True,
                "golden_answer": "42",
                "predicted_answer": "42",
                "is_refusal": False,
                "is_correct": True,
            }
        ]
    )
    qa_df = pd.DataFrame(
        [
            {
                "query_id": "Q001",
                "query_text": "Question",
                "golden_answer": "42",
                "relevant_doc_ids": "doc1.pdf",
                "evidence_locations": "doc1.pdf p.2",
                "source_text": "Answer is 42.",
                "should_answer": True,
                "Reviewers": "AB;CD",
            }
        ]
    )

    try:
        module.enrich_saved_results_dataframe(
            results_df,
            qa_df,
            retrieval_k=8,
            similarity_threshold=85.0,
            abs_tol=0.1,
            rel_tol=0.01,
            f1_threshold=0.80,
            semantic_threshold=0.90,
        )
    except ValueError as exc:
        assert "matched zero rows" in str(exc)
        assert "QQ001" in str(exc)
    else:
        raise AssertionError("Expected enrich_saved_results_dataframe to fail loudly")


def test_enrich_saved_results_dataframe_uses_reference_doc_ids_all_for_doc_metrics():
    module = _load_evaluate_accuracy()

    results_df = pd.DataFrame(
        [
            {
                "query_id": "Q001",
                "query_text": "Question",
                "should_answer": True,
                "golden_answer": "42",
                "predicted_answer": "42",
                "predicted_evidence_locations": "doc1:p.2",
                "reference_doc_ids_all": "doc1;doc2",
                "exact_match": 1,
                "token_f1": 1.0,
                "semantic_similarity": 1.0,
                "similarity_score": 100.0,
                "is_refusal": False,
                "is_correct": True,
            }
        ]
    )
    qa_df = pd.DataFrame(
        [
            {
                "query_id": "Q001",
                "query_text": "Question",
                "golden_answer": "42",
                "relevant_doc_ids": "doc2.pdf",
                "evidence_locations": "doc2.pdf p.9",
                "source_text": "Answer is 42.",
                "should_answer": True,
                "Reviewers": "AB;CD",
            }
        ]
    )

    enriched = module.enrich_saved_results_dataframe(
        results_df,
        qa_df,
        retrieval_k=8,
        similarity_threshold=85.0,
        abs_tol=0.1,
        rel_tol=0.01,
        f1_threshold=0.80,
        semantic_threshold=0.90,
    )

    assert enriched.loc[0, "pipeline_doc_hit_at_k"] is True
    assert float(enriched.loc[0, "pipeline_recall_at_k"]) == 1.0
    assert float(enriched.loc[0, "pipeline_page_recall_at_k"]) == 0.0


def test_parse_args_defaults_to_verified_audited_and_retrieval_k_8(monkeypatch):
    module = _load_evaluate_accuracy()

    monkeypatch.setattr(sys, "argv", ["evaluate_accuracy.py"])
    args = module.parse_args()

    assert args.excel == Path("tests/accuracy/StatsChat_QA_Verified_Audited.xlsx")
    assert args.retrieval_k == 8
    assert args.query_id_prefix == "QQ"
