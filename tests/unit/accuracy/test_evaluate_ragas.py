"""Unit tests for standalone span-evaluation helpers."""

import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pandas as pd
import pytest


def _load_evaluate_ragas():
    repo_root = Path(__file__).resolve().parents[3]
    module_path = repo_root / "tests" / "accuracy" / "evaluate_ragas.py"
    spec = spec_from_file_location("evaluate_ragas_module", module_path)
    module = module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_split_context_texts_uses_expected_delimiter():
    module = _load_evaluate_ragas()

    contexts = module.split_context_texts(
        "First chunk.\n---\nSecond chunk.\n---\nThird chunk."
    )

    assert contexts == ["First chunk.", "Second chunk.", "Third chunk."]


def test_prepare_rows_filters_missing_answer_and_source_text():
    module = _load_evaluate_ragas()

    df = pd.DataFrame(
        [
            {
                "query_id": "QQ001",
                "query_text": "Question 1",
                "golden_answer": "0.069",
                "predicted_answer": "6.9 per cent",
                "source_text": "Inflation was 6.9 per cent.",
                "should_answer": True,
                "context_texts": "Inflation was 6.9 per cent.\n---\nSecond chunk.",
            },
            {
                "query_id": "QQ002",
                "query_text": "Question 2",
                "golden_answer": "0.059",
                "predicted_answer": "",
                "source_text": "GDP grew by 5.9 per cent.",
                "should_answer": True,
                "context_texts": "GDP grew by 5.9 per cent.",
            },
            {
                "query_id": "QQ003",
                "query_text": "Question 3",
                "golden_answer": "34 percent",
                "predicted_answer": "24 percent",
                "source_text": "",
                "should_answer": True,
                "context_texts": "Only about one-quarter have a certificate.",
            },
        ]
    )

    rows, skip_counts = module.prepare_rows(df)

    assert len(rows) == 3
    assert rows[0].span_eval_eligible is True
    assert rows[0].retrieved_contexts == [
        "Inflation was 6.9 per cent.",
        "Second chunk.",
    ]
    assert rows[1].span_eval_eligible is False
    assert rows[1].span_skip_reason == "missing_predicted_answer"
    assert rows[2].span_eval_eligible is False
    assert rows[2].span_skip_reason == "missing_source_text"
    assert skip_counts == {
        "missing_predicted_answer": 1,
        "missing_source_text": 1,
    }


def test_join_inputs_raises_when_query_ids_do_not_match():
    module = _load_evaluate_ragas()

    qa_df = pd.DataFrame(
        [
            {
                "query_id": "QQ001",
                "query_text": "Question 1",
                "golden_answer": "0.069",
                "source_text": "Inflation was 6.9 per cent.",
                "should_answer": True,
            }
        ]
    )
    results_df = pd.DataFrame(
        [
            {
                "query_id": "QQ999",
                "query_text": "Wrong question",
                "golden_answer": "x",
                "predicted_answer": "answer",
                "context_texts": "context",
            }
        ]
    )

    try:
        module.join_inputs(qa_df, results_df)
    except ValueError as exc:
        message = str(exc)
    else:  # pragma: no cover - explicit failure path
        raise AssertionError("Expected ValueError for zero-match join")

    assert "matched zero rows" in message
    assert "QQ999" in message


def test_parse_args_requires_results_input(monkeypatch):
    module = _load_evaluate_ragas()

    monkeypatch.setattr(sys, "argv", ["evaluate_ragas.py"])

    with pytest.raises(SystemExit):
        module.parse_args()
