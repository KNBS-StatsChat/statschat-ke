"""Unit tests for cloud_llm Inquirer behavior.

Covers metadata flattening, similarity filtering, query parsing behavior,
and error handling for empty inputs or invalid provider configuration.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from statschat.generative.cloud_llm import Inquirer
from statschat.generative.response_model import LlmResponse


def test_flatten_meta_merges_and_removes_metadata():
    payload = {"a": 1, "metadata": {"title": "T", "date": "2024-01-01"}}
    # Use the staticmethod from the class
    out = Inquirer.flatten_meta(payload)
    assert out["a"] == 1
    assert out["title"] == "T"
    assert out["date"] == "2024-01-01"
    assert "metadata" not in out


def test_similarity_search_filters_and_flattens():
    # Create a bare instance without running __init__ (avoid heavy deps)
    inq = Inquirer.__new__(Inquirer)
    inq.k_docs = 5
    inq.similarity_threshold = 0.5
    inq.logger = MagicMock()

    # Fake FAISS DB that returns two matches; second is above threshold
    def fake_sim_with_score(query, k):
        doc1 = SimpleNamespace(
            dict=lambda: {
                "page_content": "c1",
                "metadata": {"title": "A", "date": "2024-01-01"},
            }
        )
        doc2 = SimpleNamespace(
            dict=lambda: {
                "page_content": "c2",
                "metadata": {"title": "B", "date": "2020-01-01"},
            }
        )
        return [(doc1, 0.4), (doc2, 0.6)]

    inq.db_latest = SimpleNamespace(similarity_search_with_score=fake_sim_with_score)
    # Request latest_filter True -> uses db_latest
    results = inq.similarity_search("q", latest_filter=True, return_dicts=True)
    # Only the first (0.4) should remain (0.6 > 0.5 threshold)
    assert len(results) == 1
    r = results[0]
    assert r["page_content"] == "c1"
    assert r["title"] == "A"
    assert isinstance(r["score"], float)


def test_query_texts_parses_chain_response(monkeypatch):
    inq = Inquirer.__new__(Inquirer)
    inq.k_contexts = 3
    inq.extractive_prompt = "p"
    inq.stuff_document_prompt = "d"
    inq.llm = None
    inq.verbose = False
    inq.logger = MagicMock()

    # Make docs: first doc score low so others pass the 1.5*docs[0]['score'] gate
    docs = [
        {"page_content": "x", "date": "2024-01-01", "title": "T", "score": 0.1},
        {"page_content": "y", "date": "2024-01-02", "title": "U", "score": 0.1},
    ]

    # Monkeypatch the chain loader to return an object whose invoke returns 'properties'
    # Return a parser-friendly JSON string under 'output_text' so Pydantic parser succeeds
    fake_response_text = '{"answer_provided": true, "most_likely_answer": "ANS", "highlighting1": [], "highlighting2": [], "highlighting3": [], "reasoning": "r"}'
    fake_chain = SimpleNamespace(
        invoke=lambda payload, return_only_outputs=True: {
            "output_text": fake_response_text
        }
    )

    monkeypatch.setattr(
        "statschat.generative.cloud_llm.load_qa_with_sources_chain",
        lambda *a, **k: fake_chain,
    )

    parsed = inq.query_texts("why", docs)
    assert isinstance(parsed, LlmResponse)
    assert parsed.most_likely_answer == "ANS"


def test_query_texts_handles_empty_docs():
    inq = Inquirer.__new__(Inquirer)
    inq.k_contexts = 3
    inq.extractive_prompt = "p"
    inq.stuff_document_prompt = "d"
    inq.llm = None
    inq.verbose = False
    inq.logger = MagicMock()

    with pytest.raises(Exception):
        inq.query_texts("why", [])


def test_inquirer_init_invalid_provider_raises(monkeypatch):
    monkeypatch.setattr(
        "statschat.generative.cloud_llm.HuggingFaceEmbeddings", lambda *a, **k: None
    )
    monkeypatch.setattr(
        "statschat.generative.cloud_llm.FAISS.load_local", lambda *a, **k: None
    )

    with pytest.raises(ValueError):
        Inquirer(provider="invalid")


def test_inquirer_accepts_extra_shared_search_config(monkeypatch):
    monkeypatch.setattr(
        "statschat.generative.cloud_llm.HuggingFaceEmbeddings", lambda *a, **k: None
    )
    monkeypatch.setattr(
        "statschat.generative.cloud_llm.FAISS.load_local", lambda *a, **k: None
    )
    monkeypatch.setattr(
        "statschat.generative.cloud_llm.ChatOpenAI", lambda *a, **k: object()
    )

    inquirer = Inquirer(
        provider="openrouter",
        reranker_model_name="cross-encoder/ms-marco-MiniLM-L-6-v2",
    )

    assert inquirer.reranker_model_name == "cross-encoder/ms-marco-MiniLM-L-6-v2"


def test_make_query_uses_similarity_and_formats_answer(monkeypatch):
    inq = Inquirer.__new__(Inquirer)
    inq.logger = MagicMock()
    inq.answer_threshold = 1
    inq.document_threshold = 1

    # Provide a stubbed similarity_search that returns two docs (dedup keeps both)
    def fake_similarity(q, latest_filter=True, return_dicts=True):
        return [
            {
                "page_content": "one",
                "date": "2024-01-01",
                "title": "A",
                "score": 0.1,
                "page_url": "u1",
                "url": "u1",
            },
            {
                "page_content": "two",
                "date": "2024-01-02",
                "title": "B",
                "score": 0.2,
                "page_url": "u2",
                "url": "u2",
            },
        ]

    inq.similarity_search = fake_similarity

    # Query_texts should be called and return a populated LlmResponse
    def fake_query_texts(question, docs):
        return LlmResponse(
            answer_provided=True,
            most_likely_answer="SOME ANSWER",
            highlighting1=[],
            highlighting2=[],
            highlighting3=[],
            reasoning=None,
        )

    inq.query_texts = fake_query_texts

    # Patch highlighter used inside make_query to simply return the docs unchanged
    monkeypatch.setattr(
        "statschat.generative.cloud_llm.highlighter",
        lambda docs, validated_response, logger: docs,
    )
    # Patch time_decay to avoid depending on external date format parsing
    monkeypatch.setattr(
        "statschat.generative.cloud_llm.time_decay", lambda date, latest=1: 1
    )

    docs_out, answer_str, validated = inq.make_query(
        "ask", latest_filter="on", highlighting=True, latest_weight=1
    )
    assert isinstance(validated, LlmResponse)
    assert "SOME ANSWER" in answer_str
    assert isinstance(docs_out, list)


def test_make_query_prefers_most_likely_answer_over_highlight(monkeypatch):
    inq = Inquirer.__new__(Inquirer)
    inq.logger = MagicMock()
    inq.answer_threshold = 10
    inq.document_threshold = 10

    inq.similarity_search = lambda q, latest_filter=True, return_dicts=True: [
        {
            "page_content": "one",
            "date": "2024-01-01",
            "title": "A",
            "score": 0.1,
            "page_url": "u1",
            "url": "u1",
        }
    ]

    inq.query_texts = lambda question, docs: LlmResponse(
        answer_provided=True,
        most_likely_answer="Kenya's overall year on year inflation rate was 6.9 per cent in January 2024.",
        highlighting1=["Consumer Prices and Inflation"],
        highlighting2=[],
        highlighting3=[],
        reasoning=None,
    )

    monkeypatch.setattr(
        "statschat.generative.cloud_llm.highlighter",
        lambda docs, validated_response, logger: docs,
    )

    _, answer_str, _ = inq.make_query(
        "ask", latest_filter="on", highlighting=True, latest_weight=0
    )

    assert answer_str == (
        "Kenya's overall year on year inflation rate was 6.9 per cent in January 2024."
    )


def test_make_query_respects_boolean_latest_filter_flag(monkeypatch):
    inq = Inquirer.__new__(Inquirer)
    inq.logger = MagicMock()
    inq.answer_threshold = 10
    inq.document_threshold = 10

    captured: dict[str, object] = {}

    def fake_similarity(q, latest_filter=True, return_dicts=True):
        captured["latest_filter"] = latest_filter
        return [
            {
                "page_content": "one",
                "date": "2024-01-01",
                "title": "A",
                "score": 0.1,
                "page_url": "u1",
                "url": "u1",
            }
        ]

    inq.similarity_search = fake_similarity
    inq.query_texts = lambda question, docs: LlmResponse(
        answer_provided=True,
        most_likely_answer="SOME ANSWER",
        highlighting1=[],
        highlighting2=[],
        highlighting3=[],
        reasoning=None,
    )

    monkeypatch.setattr(
        "statschat.generative.cloud_llm.highlighter",
        lambda docs, validated_response, logger: docs,
    )

    inq.make_query("ask", latest_filter=False, highlighting=True, latest_weight=0)

    assert captured["latest_filter"] is False


def test_make_query_preserves_distinct_pages_from_same_report(monkeypatch):
    inq = Inquirer.__new__(Inquirer)
    inq.logger = MagicMock()
    inq.answer_threshold = 10
    inq.document_threshold = 10

    inq.similarity_search = lambda q, latest_filter=True, return_dicts=True: [
        {
            "page_content": "page one content",
            "date": "2024-01-01",
            "title": "Same Report",
            "score": 0.1,
            "page_url": "u1#page=1",
            "url": "u1",
        },
        {
            "page_content": "page two content",
            "date": "2024-01-01",
            "title": "Same Report",
            "score": 0.11,
            "page_url": "u1#page=2",
            "url": "u1",
        },
    ]

    captured_docs: dict[str, object] = {}

    def fake_query_texts(question, docs):
        captured_docs["count"] = len(docs)
        captured_docs["page_urls"] = [doc["page_url"] for doc in docs]
        return LlmResponse(
            answer_provided=True,
            most_likely_answer="SOME ANSWER",
            highlighting1=[],
            highlighting2=[],
            highlighting3=[],
            reasoning=None,
        )

    inq.query_texts = fake_query_texts

    monkeypatch.setattr(
        "statschat.generative.cloud_llm.highlighter",
        lambda docs, validated_response, logger: docs,
    )

    inq.make_query("ask", latest_filter="off", highlighting=True, latest_weight=0)

    assert captured_docs["count"] == 2
    assert captured_docs["page_urls"] == ["u1#page=1", "u1#page=2"]
