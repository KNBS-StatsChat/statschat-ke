"""Unit tests for cloud_llm Inquirer behavior.

Covers metadata flattening, similarity filtering, query parsing behavior,
reranking/context selection, and error handling for invalid provider config.
"""

from datetime import date
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from statschat.generative.cloud_llm import (
    Inquirer,
    _apply_recency_bias,
    _build_reranker_passage,
    _doc_period_tokens,
    _doc_report_families,
    _doc_matches_query_temporal,
    _doc_temporal_tokens,
    _extract_months,
    _extract_quarters,
    _extract_years,
    _guardrail_refusal_reason,
    _infer_exact_cited_source_from_selected_docs,
    _select_lagged_year_subset,
    _select_precise_temporal_subset,
    has_temporal_constraint,
    infer_query_report_families,
    parse_temporal_tokens,
)
from statschat.generative.response_model import LlmResponse


def test_flatten_meta_merges_and_removes_metadata():
    payload = {"a": 1, "metadata": {"title": "T", "date": "2024-01-01"}}
    # Use the staticmethod from the class
    out = Inquirer.flatten_meta(payload)
    assert out["a"] == 1
    assert out["title"] == "T"
    assert out["date"] == "2024-01-01"
    assert "metadata" not in out


def test_flatten_meta_normalizes_fragment_page_url():
    payload = {
        "page_content": "content",
        "metadata": {
            "title": "T",
            "date": "2024-01-01",
            "url": "https://example.com/test.pdf",
            "page_number": 7,
            "page_url": "#page=7",
        },
    }

    out = Inquirer.flatten_meta(payload)

    assert out["page_url"] == "https://example.com/test.pdf#page=7"


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


def test_inquirer_can_initialize_retrieval_without_llm(monkeypatch):
    loaded_roots: list[str] = []

    class DummyFAISS:
        @staticmethod
        def load_local(root, _embeddings, allow_dangerous_deserialization=False):
            loaded_roots.append(root)
            return SimpleNamespace(root=root)

    def fail_chat_openai(*_args, **_kwargs):
        raise AssertionError("ChatOpenAI should not be initialised")

    monkeypatch.setattr(
        "statschat.generative.cloud_llm.HuggingFaceEmbeddings",
        lambda model_name: SimpleNamespace(model_name=model_name),
    )
    monkeypatch.setattr("statschat.generative.cloud_llm.FAISS", DummyFAISS)
    monkeypatch.setattr("statschat.generative.cloud_llm.ChatOpenAI", fail_chat_openai)

    inq = Inquirer(
        faiss_db_root="data/db",
        faiss_db_root_latest="data/db_latest",
        embedding_model_name="dummy-embedding",
        provider="openrouter",
        logger=MagicMock(),
        initialize_llm=False,
    )

    assert inq.llm is None
    assert loaded_roots == ["data/db", "data/db_latest"]


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


def test_query_texts_accepts_false_answer_without_answer_text(monkeypatch):
    inq = Inquirer.__new__(Inquirer)
    inq.k_contexts = 3
    inq.extractive_prompt = "p"
    inq.stuff_document_prompt = "d"
    inq.llm = None
    inq.verbose = False
    inq.logger = MagicMock()

    docs = [
        {"page_content": "x", "date": "2024-01-01", "title": "T", "score": 0.1},
    ]
    fake_response_text = '{"answer_provided": false, "highlighting1": [], "highlighting2": [], "highlighting3": [], "reasoning": "No answer in context."}'
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
    assert parsed.answer_provided is False
    assert parsed.most_likely_answer is None


def test_query_texts_handles_empty_docs():
    inq = Inquirer.__new__(Inquirer)
    inq.k_contexts = 3
    inq.extractive_prompt = "p"
    inq.stuff_document_prompt = "d"
    inq.llm = None
    inq.verbose = False
    inq.logger = MagicMock()

    parsed = inq.query_texts("why", [])

    assert isinstance(parsed, LlmResponse)
    assert parsed.answer_provided is False
    assert parsed.most_likely_answer is None


def test_guardrail_refusal_reason_catches_out_of_scope_queries():
    assert _guardrail_refusal_reason(
        "What was Tanzania's GDP growth rate in 2023?",
        today=date(2026, 4, 14),
    )
    assert _guardrail_refusal_reason(
        "Compare Kenya's 2024 CPI inflation with Nigeria's 2024 CPI inflation.",
        today=date(2026, 4, 14),
    )
    assert _guardrail_refusal_reason(
        "Should Kenya reduce interest rates to control inflation?",
        today=date(2026, 4, 14),
    )
    assert _guardrail_refusal_reason(
        "What is the best county in Kenya?",
        today=date(2026, 4, 14),
    )
    assert _guardrail_refusal_reason(
        "What was Kenya's inflation rate in December 2026?",
        today=date(2026, 4, 14),
    )
    assert _guardrail_refusal_reason(
        "What is the salary of the KNBS Director General?",
        today=date(2026, 4, 14),
    )
    assert _guardrail_refusal_reason(
        "What is Kenya's military expenditure as a percentage of GDP in 2024?",
        today=date(2026, 4, 14),
    )


def test_guardrail_refusal_reason_allows_in_scope_statistical_queries():
    assert (
        _guardrail_refusal_reason(
            "What was Kenya's inflation rate in April 2025?",
            today=date(2026, 4, 14),
        )
        is None
    )
    assert (
        _guardrail_refusal_reason(
            "Which Kenyan county leads by formal financial inclusion?",
            today=date(2026, 4, 14),
        )
        is None
    )


def test_make_query_short_circuits_guardrail_refusals():
    inq = Inquirer.__new__(Inquirer)
    inq.logger = MagicMock()
    inq.similarity_search = MagicMock()

    docs, answer, response = inq.make_query(
        "What was Tanzania's GDP growth rate in 2023?",
        latest_filter=False,
    )

    assert docs == []
    assert answer == ""
    assert response.answer_provided is False
    assert "outside the Kenya/KNBS corpus" in (response.reasoning or "")
    inq.similarity_search.assert_not_called()


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


def test_inquirer_defaults_to_wider_reranker_candidate_pool(monkeypatch):
    monkeypatch.setattr(
        "statschat.generative.cloud_llm.HuggingFaceEmbeddings", lambda *a, **k: None
    )
    monkeypatch.setattr(
        "statschat.generative.cloud_llm.FAISS.load_local", lambda *a, **k: None
    )
    monkeypatch.setattr(
        "statschat.generative.cloud_llm.ChatOpenAI", lambda *a, **k: object()
    )

    inquirer = Inquirer(provider="openrouter", k_docs=8)

    assert inquirer.reranker_candidate_k == 48


def test_make_query_uses_similarity_and_formats_answer(monkeypatch):
    inq = Inquirer.__new__(Inquirer)
    inq.logger = MagicMock()
    inq.answer_threshold = 1
    inq.document_threshold = 1

    # Provide a stubbed similarity_search that returns two docs (dedup keeps both)
    def fake_similarity(q, latest_filter=True, return_dicts=True, candidate_k=None):
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
    def fake_query_texts(question, docs, **_kwargs):
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

    inq.similarity_search = (
        lambda q, latest_filter=True, return_dicts=True, candidate_k=None: [
            {
                "page_content": "one",
                "date": "2024-01-01",
                "title": "A",
                "score": 0.1,
                "page_url": "u1",
                "url": "u1",
            }
        ]
    )

    inq.query_texts = lambda question, docs, **_kwargs: LlmResponse(
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

    def fake_similarity(q, latest_filter=True, return_dicts=True, candidate_k=None):
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
    inq.query_texts = lambda question, docs, **_kwargs: LlmResponse(
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

    inq.similarity_search = (
        lambda q, latest_filter=True, return_dicts=True, candidate_k=None: [
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
    )

    captured_docs: dict[str, object] = {}

    def fake_query_texts(question, docs, **_kwargs):
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


def test_make_query_reranks_before_truncating(monkeypatch):
    inq = Inquirer.__new__(Inquirer)
    inq.logger = MagicMock()
    inq.answer_threshold = 10
    inq.document_threshold = 10
    inq.k_docs = 2
    inq.k_contexts = 2
    inq.reranker_model_name = "dummy-reranker"
    inq.recency_bias_weight = 0.0  # disable recency bias to isolate reranker order

    # All docs share the same year metadata so the temporal pre-filter keeps
    # them all and we exercise pure reranker tie-breaking.
    inq.similarity_search = (
        lambda q, latest_filter=True, return_dicts=True, candidate_k=None: [
            {
                "page_content": "older but less relevant",
                "date": "01 January 2022",
                "title": "Older Match 2022",
                "score": 0.10,
                "page_url": "u1#page=1",
                "url": "u1",
            },
            {
                "page_content": "exact answer evidence",
                "date": "01 January 2022",
                "title": "Correct Match 2022",
                "score": 0.20,
                "page_url": "u2#page=1",
                "url": "u2",
            },
            {
                "page_content": "other evidence",
                "date": "01 January 2022",
                "title": "Secondary Match 2022",
                "score": 0.30,
                "page_url": "u3#page=1",
                "url": "u3",
            },
        ]
    )

    monkeypatch.setattr(
        "statschat.generative.cloud_llm._get_reranker",
        lambda model_name: SimpleNamespace(predict=lambda pairs: [0.1, 0.95, 0.5]),
    )
    monkeypatch.setattr(
        "statschat.generative.cloud_llm.highlighter",
        lambda docs, validated_response, logger: docs,
    )

    captured_docs: dict[str, object] = {}

    def fake_query_texts(question, docs, **_kwargs):
        captured_docs["titles"] = [doc["title"] for doc in docs]
        return LlmResponse(
            answer_provided=True,
            most_likely_answer="SOME ANSWER",
            highlighting1=[],
            highlighting2=[],
            highlighting3=[],
            reasoning=None,
        )

    inq.query_texts = fake_query_texts

    docs_out, _, _ = inq.make_query(
        "What was the poverty rate in Kenya as of 2022?",
        latest_filter=False,
        highlighting=True,
        latest_weight=2,
    )

    assert captured_docs["titles"] == ["Correct Match 2022", "Secondary Match 2022"]
    assert [doc["title"] for doc in docs_out] == [
        "Correct Match 2022",
        "Secondary Match 2022",
    ]


def test_query_texts_uses_diversified_context_selection(monkeypatch):
    inq = Inquirer.__new__(Inquirer)
    inq.k_contexts = 2
    inq.max_chunks_per_doc = 1
    inq.per_doc_penalty = 0.2
    inq.extractive_prompt = "p"
    inq.stuff_document_prompt = "d"
    inq.llm = None
    inq.verbose = False
    inq.logger = MagicMock()

    docs = [
        {
            "page_content": "report A page 1",
            "date": "01 January 2024",
            "title": "Report A",
            "score": 0.1,
            "selection_score": 0.95,
            "page_url": "a#page=1",
        },
        {
            "page_content": "report A page 2",
            "date": "01 January 2024",
            "title": "Report A",
            "score": 0.11,
            "selection_score": 0.94,
            "page_url": "a#page=2",
        },
        {
            "page_content": "report B page 1",
            "date": "01 January 2023",
            "title": "Report B",
            "score": 0.12,
            "selection_score": 0.93,
            "page_url": "b#page=1",
        },
    ]

    captured: dict[str, object] = {}
    fake_response_text = '{"answer_provided": true, "most_likely_answer": "ANS", "highlighting1": [], "highlighting2": [], "highlighting3": [], "reasoning": "r"}'

    def fake_invoke(payload, return_only_outputs=True):
        captured["titles"] = [
            doc.metadata["title"] for doc in payload["input_documents"]
        ]
        return {"output_text": fake_response_text}

    fake_chain = SimpleNamespace(invoke=fake_invoke)

    monkeypatch.setattr(
        "statschat.generative.cloud_llm.load_qa_with_sources_chain",
        lambda *a, **k: fake_chain,
    )

    parsed = inq.query_texts("why", docs)

    assert isinstance(parsed, LlmResponse)
    assert captured["titles"] == ["Report A", "Report B"]


def test_query_texts_diversifies_fragment_page_urls_using_base_url(monkeypatch):
    inq = Inquirer.__new__(Inquirer)
    inq.k_contexts = 2
    inq.max_chunks_per_doc = 1
    inq.per_doc_penalty = 0.2
    inq.extractive_prompt = "p"
    inq.stuff_document_prompt = "d"
    inq.llm = None
    inq.verbose = False
    inq.logger = MagicMock()

    docs = [
        {
            "page_content": "report A page 1",
            "date": "01 January 2024",
            "title": "Report A",
            "url": "https://example.com/a.pdf",
            "score": 0.1,
            "selection_score": 0.95,
            "page_url": "#page=1",
        },
        {
            "page_content": "report A page 2",
            "date": "01 January 2024",
            "title": "Report A",
            "url": "https://example.com/a.pdf",
            "score": 0.11,
            "selection_score": 0.94,
            "page_url": "#page=2",
        },
        {
            "page_content": "report B page 1",
            "date": "01 January 2023",
            "title": "Report B",
            "url": "https://example.com/b.pdf",
            "score": 0.12,
            "selection_score": 0.93,
            "page_url": "#page=1",
        },
    ]

    captured: dict[str, object] = {}
    fake_response_text = '{"answer_provided": true, "most_likely_answer": "ANS", "highlighting1": [], "highlighting2": [], "highlighting3": [], "reasoning": "r"}'

    def fake_invoke(payload, return_only_outputs=True):
        captured["titles"] = [
            doc.metadata["title"] for doc in payload["input_documents"]
        ]
        return {"output_text": fake_response_text}

    fake_chain = SimpleNamespace(invoke=fake_invoke)

    monkeypatch.setattr(
        "statschat.generative.cloud_llm.load_qa_with_sources_chain",
        lambda *a, **k: fake_chain,
    )

    parsed = inq.query_texts("why", docs)

    assert isinstance(parsed, LlmResponse)
    assert captured["titles"] == ["Report A", "Report B"]


def test_query_texts_refines_pages_within_existing_doc_allocation(monkeypatch):
    inq = Inquirer.__new__(Inquirer)
    inq.k_contexts = 2
    inq.max_chunks_per_doc = 2
    inq.per_doc_penalty = 0.2
    inq.extractive_prompt = "p"
    inq.stuff_document_prompt = "d"
    inq.llm = None
    inq.verbose = False
    inq.logger = MagicMock()
    inq.reranker_model_name = "dummy-reranker"
    inq.generation_page_selection_enabled = True
    inq.generation_page_shortlist_k = 24

    agriculture_url = "https://example.com/agriculture.pdf"
    other_url = "https://example.com/other.pdf"
    docs = [
        {
            "page_content": "green grams section",
            "date": "01 January 2024",
            "title": "National Agriculture Production Report 2024",
            "url": agriculture_url,
            "score": 0.1,
            "selection_score": 0.95,
            "page_number": 39,
            "page_url": f"{agriculture_url}#page=39",
        },
        {
            "page_content": "other report evidence",
            "date": "01 January 2024",
            "title": "Other Report",
            "url": other_url,
            "score": 0.12,
            "selection_score": 0.94,
            "page_number": 1,
            "page_url": f"{other_url}#page=1",
        },
    ]

    inq.db = SimpleNamespace(
        docstore=SimpleNamespace(
            _dict={
                "agri14": SimpleNamespace(
                    model_dump=lambda: {
                        "page_content": "The area under food crops increased from 4,935.3 thousand hectares in 2022 to 5,371.7 thousand hectares in 2023.",
                        "metadata": {
                            "date": "01 January 2024",
                            "title": "National Agriculture Production Report 2024",
                            "page_number": 14,
                            "page_url": "#page=14",
                            "url": agriculture_url,
                        },
                    }
                ),
                "agri39": SimpleNamespace(
                    model_dump=lambda: {
                        "page_content": "green grams section",
                        "metadata": {
                            "date": "01 January 2024",
                            "title": "National Agriculture Production Report 2024",
                            "page_number": 39,
                            "page_url": "#page=39",
                            "url": agriculture_url,
                        },
                    }
                ),
                "other1": SimpleNamespace(
                    model_dump=lambda: {
                        "page_content": "other report evidence",
                        "metadata": {
                            "date": "01 January 2024",
                            "title": "Other Report",
                            "page_number": 1,
                            "page_url": "#page=1",
                            "url": other_url,
                        },
                    }
                ),
            }
        )
    )

    captured: dict[str, object] = {}
    fake_response_text = '{"answer_provided": true, "most_likely_answer": "5,371.7 thousand hectares", "highlighting1": [], "highlighting2": [], "highlighting3": [], "reasoning": "r"}'

    def fake_invoke(payload, return_only_outputs=True):
        captured["contents"] = [doc.page_content for doc in payload["input_documents"]]
        return {"output_text": fake_response_text}

    monkeypatch.setattr(
        "statschat.generative.cloud_llm._get_reranker",
        lambda model_name: SimpleNamespace(
            predict=lambda pairs: [
                (
                    0.95
                    if "5,371.7 thousand hectares" in passage
                    else 0.20 if "green grams section" in passage else 0.75
                )
                for _, passage in pairs
            ]
        ),
    )
    monkeypatch.setattr(
        "statschat.generative.cloud_llm.load_qa_with_sources_chain",
        lambda *a, **k: SimpleNamespace(invoke=fake_invoke),
    )

    parsed = inq.query_texts(
        "What was the area under food crops in 2023?",
        docs,
        latest_filter_enabled=False,
    )

    assert isinstance(parsed, LlmResponse)
    assert captured["contents"] == [
        "The area under food crops increased from 4,935.3 thousand hectares in 2022 to 5,371.7 thousand hectares in 2023.",
        "other report evidence",
    ]


def test_infer_exact_cited_source_prefers_answer_bearing_page_over_generic_highlight():
    agriculture_url = "https://example.com/agriculture.pdf"
    selected_docs = [
        {
            "page_content": (
                "The area under food crops increased in 2023 due to favourable rainfall "
                "and expanded cultivation."
            ),
            "title": "National Agriculture Production Report 2024",
            "page_number": 24,
            "page_url": f"{agriculture_url}#page=24",
            "url": agriculture_url,
        },
        {
            "page_content": (
                "The area under food crops increased from 4,935.3 thousand hectares "
                "in 2022 to 5,371.7 thousand hectares in 2023."
            ),
            "title": "National Agriculture Production Report 2024",
            "page_number": 14,
            "page_url": f"{agriculture_url}#page=14",
            "url": agriculture_url,
        },
    ]
    validated_response = LlmResponse(
        answer_provided=True,
        most_likely_answer="5,371.7 thousand hectares",
        highlighting1=["The area under food crops increased"],
        highlighting2=[],
        highlighting3=[],
        reasoning="r",
    )

    exact_source = _infer_exact_cited_source_from_selected_docs(
        selected_docs, validated_response
    )

    assert exact_source is not None
    assert exact_source["page_number"] == "14"
    assert exact_source["label"] == (
        "National Agriculture Production Report 2024, page 14"
    )
    assert exact_source["quote"] == "5,371.7 thousand hectares"


def test_apply_recency_bias_skips_explicit_year_queries():
    docs = [
        {"title": "Older", "date": "01 January 2021", "reranker_score": 0.5},
        {"title": "Newer", "date": "01 January 2024", "reranker_score": 0.5},
    ]

    biased = _apply_recency_bias(
        docs,
        "What was the poverty rate in Kenya as of 2022?",
        recency_bias_weight=1.0,
    )

    assert [doc["selection_score"] for doc in biased] == [0.5, 0.5]


def test_extract_years_handles_range_year_titles():
    # "2023-24" should expand into both 2023 and 2024
    assert _extract_years("2023-24 Kenya Housing Survey") == {2023, 2024}
    # "2023/2024" same idea
    assert _extract_years("FY 2023/2024 Economic Survey") == {2023, 2024}
    # Glued FY prefix without a space (digit-boundary lookbehind)
    assert _extract_years("FY2023/24 Budget Review") == {2023, 2024}
    assert _extract_years("FY2023") == {2023}
    # Plain single year still works
    assert _extract_years("Quarterly GDP, third quarter 2023") == {2023}
    # Century rollover
    assert _extract_years("KDHS 1999-00 results") == {1999, 2000}
    # Adjacent digits must NOT be misread as a year
    assert _extract_years("invoice 20235 ref") == set()


def test_extract_months_and_quarters():
    assert _extract_months("inflation in April 2025") == {4}
    assert _extract_months("CPI for Jan and December") == {1, 12}
    assert _extract_quarters("Q3 of 2023") == {3}
    assert _extract_quarters("third quarter results") == {3}
    assert _extract_quarters("quarter four bulletin") == {4}


def test_has_temporal_constraint_detects_year_month_quarter():
    assert has_temporal_constraint("Q3 2023 GDP")
    assert has_temporal_constraint("April 2025 inflation")
    assert has_temporal_constraint("2022 KDHS")
    assert not has_temporal_constraint("What is the population of Kenya?")
    assert not has_temporal_constraint("predominant dwelling unit")


def test_doc_temporal_tokens_reads_metadata_blob():
    doc = {
        "title": "Kenya quarterly gross domestic product third quarter 2023",
        "date": "01 December 2023",
        "url": "https://example/Kenya-quarterly-gross-domestic-product-third-quarter-2023.pdf",
        "page_url": "https://example/Kenya-quarterly-gross-domestic-product-third-quarter-2023.pdf#page=2",
    }
    tokens = _doc_temporal_tokens(doc)
    assert 2023 in tokens["years"]
    assert 3 in tokens["quarters"]
    assert 12 in tokens["months"]


def test_doc_period_tokens_prefers_title_period_over_publication_date():
    doc = {
        "title": "Construction Input Price Indices for Fourth Quarter 2023",
        "date": "01 February 2024",
        "url": "https://example/Construction-Input-Price-Indices-for-Fourth-Quarter-2023.pdf",
    }

    tokens = _doc_period_tokens(doc)

    assert tokens["years"] == {2023}
    assert tokens["quarters"] == {4}
    assert tokens["months"] == set()


def test_doc_matches_query_temporal_filters_neighbouring_years():
    query = parse_temporal_tokens(
        "What was Kenya's GDP growth rate in Quarter 3 of 2023?"
    )
    correct_doc = _doc_temporal_tokens(
        {
            "title": "Kenya quarterly gross domestic product third quarter 2023",
            "date": "01 December 2023",
        }
    )
    wrong_year_doc = _doc_temporal_tokens(
        {
            "title": "Kenya quarterly gross domestic product third quarter 2024",
            "date": "01 December 2024",
        }
    )
    wrong_quarter_doc = _doc_temporal_tokens(
        {
            "title": "Kenya quarterly gross domestic product first quarter 2023",
            "date": "01 May 2023",
        }
    )
    assert _doc_matches_query_temporal(query, correct_doc) is True
    assert _doc_matches_query_temporal(query, wrong_year_doc) is False
    assert _doc_matches_query_temporal(query, wrong_quarter_doc) is False


def test_doc_matches_query_temporal_accepts_range_year_titles():
    # QQ007 case: query says "as of 2024", gold doc is "2023-24-Kenya-Housing-Survey..."
    query = parse_temporal_tokens("predominant dwelling unit in Kenya as of 2024")
    doc = _doc_temporal_tokens(
        {
            "title": "2023-24 Kenya Housing Survey Basic Report",
            "date": "01 September 2024",
            "url": "https://example/2023-24-Kenya-Housing-Survey-Basic-Report1.pdf",
        }
    )
    assert _doc_matches_query_temporal(query, doc) is True


def test_select_precise_temporal_subset_uses_report_period_not_pub_date():
    query = parse_temporal_tokens(
        "What was the construction inflation rate in Kenya in Q4 2024?"
    )
    docs = [
        {
            "title": "Construction Input Price Indices for Fourth Quarter 2023",
            "date": "01 February 2024",
            "url": "https://example/Construction-Input-Price-Indices-for-Fourth-Quarter-2023.pdf",
        },
        {
            "title": "Construction Input Price Indices for Fourth Quarter 2024",
            "date": "01 February 2025",
            "url": "https://example/Construction-Input-Price-Indices-for-Fourth-Quarter-2024.pdf",
        },
    ]

    subset, reason = _select_precise_temporal_subset(
        docs, query, {"construction_input_price_indices"}
    )

    assert reason == "exact report period"
    assert [doc["title"] for doc in subset] == [
        "Construction Input Price Indices for Fourth Quarter 2024"
    ]


def test_select_precise_temporal_subset_prefers_lei_year_plus_one_edition():
    query = parse_temporal_tokens("What was Kenya's broad money supply in August 2023?")
    docs = [
        {
            "title": "Leading Economic Indicators August 2023",
            "date": "01 September 2023",
            "url": "https://example/Leading-Economic-Indicators-August-2023.pdf",
        },
        {
            "title": "Leading Economic Indicators August 2024",
            "date": "01 September 2024",
            "url": "https://example/Leading-Economic-Indicators-August-2024.pdf",
        },
    ]

    subset, reason = _select_precise_temporal_subset(
        docs, query, {"leading_economic_indicators"}
    )

    assert reason == "leading indicators year+1 edition"
    assert [doc["title"] for doc in subset] == [
        "Leading Economic Indicators August 2024"
    ]


def test_infer_query_report_families_from_metric_hints():
    assert "economic_survey" in infer_query_report_families(
        "By what percentage did petroleum product imports increase in 2024?"
    )
    assert "cpi_inflation" in infer_query_report_families(
        "What was Kenya's inflation rate in April 2025?"
    )
    assert "cpi_inflation" in infer_query_report_families(
        "What was the CPI for April 2025?"
    )
    assert "national_agriculture_production_report" in infer_query_report_families(
        "How much maize was produced in 2023?"
    )
    assert "gross_county_product" in infer_query_report_families(
        "What was Nairobi City’s five-year average share of national GVA (2019–2023)?"
    )
    assert "kenya_demographic_and_health_survey" in infer_query_report_families(
        "What percentage of children in Kenya have a birth certificate?"
    )
    assert "facts_and_figures" in infer_query_report_families(
        "What was the total wage employment in Kenya's modern sector in 2024?"
    )
    assert "statistical_abstract" in infer_query_report_families(
        "How many tonnes of unmilled wheat did Kenya import in 2024?"
    )
    assert infer_query_report_families(
        "What was the construction inflation rate in Kenya in Q4 2024?"
    ) == {"construction_input_price_indices"}
    assert "finaccess" in infer_query_report_families(
        "What was Kenya's formal financial access rate in 2024?"
    )
    assert "leading_economic_indicators" in infer_query_report_families(
        "What was Kenya's broad money supply (M3) in August 2023?"
    )


def test_doc_report_families_reads_title_and_url_metadata():
    economic_doc = {
        "title": "2025 Economic Survey",
        "url": "https://example/2025-Economic-Survey.pdf",
    }
    agriculture_doc = {
        "title": "National Agriculture Production Report 2024",
        "url": "https://example/National-Agriculture-Production-Report-2024.pdf",
    }

    assert _doc_report_families(economic_doc) == {"economic_survey"}
    assert _doc_report_families(agriculture_doc) == {
        "national_agriculture_production_report"
    }
    assert _doc_report_families(
        {
            "title": "",
            "url": "https://example/2023-Economic-Survey.pdf",
        }
    ) == {"economic_survey"}
    assert _doc_report_families(
        {
            "title": "Kenya Consumer Price Indices and Inflation Rates April 2025",
            "url": "https://example/Kenya-Consumer-Price-Indices-and-Inflation-Rates-April-2025.pdf",
        }
    ) == {"cpi_inflation"}
    assert _doc_report_families({"title": "2025 Facts and Figures"}) == {
        "facts_and_figures"
    }
    assert _doc_report_families({"title": "2025 Statistical Abstract"}) == {
        "statistical_abstract"
    }
    assert _doc_report_families(
        {"title": "Construction Input Price Indices for Fourth Quarter 2024"}
    ) == {"construction_input_price_indices"}
    assert _doc_report_families(
        {"title": "2024 FinAccess Household Survey Report"}
    ) == {"finaccess"}
    assert _doc_report_families(
        {"title": "Leading Economic Indicators August 2024"}
    ) == {"leading_economic_indicators"}
    assert _doc_report_families(
        {"title": "Kenya Demographic and Health Survey 2030"}
    ) == {"kenya_demographic_and_health_survey"}
    assert (
        _doc_report_families(
            {
                "title": "2015 2016 Kenya Integrated Household Budget Survey Basic Report",
                "url": "https://example/2015-2016-Kenya-Integrated-Household-Budget-Survey-Basic-Report.pdf",
            }
        )
        == set()
    )


def test_select_lagged_year_subset_prefers_year_plus_one():
    docs = [
        {
            "title": "2024 Economic Survey",
            "date": "01 May 2024",
            "url": "https://example/2024-Economic-Survey.pdf",
        },
        {
            "title": "2025 Economic Survey",
            "date": "01 May 2025",
            "url": "https://example/2025-Economic-Survey.pdf",
        },
    ]

    subset, label = _select_lagged_year_subset(
        docs,
        parse_temporal_tokens(
            "By what percentage did petroleum product imports increase in 2024?"
        ),
    )

    assert subset is not None
    assert [doc["title"] for doc in subset] == ["2025 Economic Survey"]
    assert label == "year+1 [2025]"


def test_select_lagged_year_subset_prefers_query_year_before_year_plus_two():
    docs = [
        {
            "title": "2019 Economic Survey",
            "date": "01 May 2019",
            "url": "https://example/2019-Economic-Survey.pdf",
        },
        {
            "title": "2021 Economic Survey",
            "date": "01 May 2021",
            "url": "https://example/2021-Economic-Survey.pdf",
        },
    ]

    subset, label = _select_lagged_year_subset(
        docs,
        parse_temporal_tokens(
            "How many people aged 5 years and above had a disability in Kenya "
            "according to the 2019 population census?"
        ),
    )

    assert subset is not None
    assert [doc["title"] for doc in subset] == ["2019 Economic Survey"]
    assert label == "query year [2019]"


def test_make_query_temporal_pre_filter_drops_neighbouring_years(monkeypatch):
    inq = Inquirer.__new__(Inquirer)
    inq.logger = MagicMock()
    inq.answer_threshold = 10
    inq.document_threshold = 10
    inq.k_docs = 3
    inq.k_contexts = 3
    inq.reranker_model_name = None  # use score-based fallback in _rerank_results
    inq.recency_bias_weight = 0.5
    inq.temporal_candidate_k = 96
    inq.reranker_candidate_k = 48

    captured_candidate_k: dict[str, object] = {}

    def fake_similarity(q, latest_filter=True, return_dicts=True, candidate_k=None):
        captured_candidate_k["value"] = candidate_k
        return [
            {
                "page_content": "Q3 2024 GDP grew 5.x% compared to 6.0% in Q3 2023",
                "date": "01 December 2024",
                "title": "Kenya quarterly gross domestic product third quarter 2024",
                "score": 0.10,
                "page_url": "u2024#page=2",
                "url": "https://example/Kenya-quarterly-gross-domestic-product-third-quarter-2024.pdf",
            },
            {
                "page_content": "Q3 2023 GDP grew by 5.9 per cent",
                "date": "01 December 2023",
                "title": "Kenya quarterly gross domestic product third quarter 2023",
                "score": 0.20,
                "page_url": "u2023#page=2",
                "url": "https://example/Kenya-quarterly-gross-domestic-product-third-quarter-2023.pdf",
            },
            {
                "page_content": "Q1 2023 GDP grew 5.x%",
                "date": "01 May 2023",
                "title": "Kenya quarterly gross domestic product first quarter 2023",
                "score": 0.30,
                "page_url": "u2023q1#page=2",
                "url": "https://example/Kenya-quarterly-gross-domestic-product-first-quarter-2023.pdf",
            },
        ]

    inq.similarity_search = fake_similarity

    captured_titles: dict[str, object] = {}

    def fake_query_texts(question, docs, **_kwargs):
        captured_titles["titles"] = [d["title"] for d in docs]
        return LlmResponse(
            answer_provided=True,
            most_likely_answer="5.9 per cent",
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

    inq.make_query(
        "What was Kenya's GDP growth rate in Quarter 3 of 2023?",
        latest_filter=False,
        highlighting=True,
        latest_weight=0,
    )

    # Temporal-query path enlarged the candidate pool
    assert captured_candidate_k["value"] == 96
    # Pre-filter dropped the 2024 and Q1 2023 reports; only the Q3 2023 doc survives
    assert captured_titles["titles"] == [
        "Kenya quarterly gross domestic product third quarter 2023"
    ]


def test_make_query_precise_temporal_retries_wider_pool(monkeypatch):
    inq = Inquirer.__new__(Inquirer)
    inq.logger = MagicMock()
    inq.answer_threshold = 10
    inq.document_threshold = 10
    inq.k_docs = 3
    inq.k_contexts = 3
    inq.reranker_model_name = None
    inq.recency_bias_weight = 0.5
    inq.temporal_candidate_k = 96
    inq.lagged_year_candidate_k = 320
    inq.reranker_candidate_k = 48

    captured_candidate_k: list[int | None] = []

    def fake_similarity(q, latest_filter=True, return_dicts=True, candidate_k=None):
        captured_candidate_k.append(candidate_k)
        base_docs = [
            {
                "page_content": "Inflation was 5.0 per cent in April 2024",
                "date": "01 April 2024",
                "title": "Kenya Consumer Price Indices and Inflation Rates April 2024",
                "score": 0.10,
                "page_url": "u2024#page=1",
                "url": "https://example/Kenya-Consumer-Price-Indices-and-Inflation-Rates-April-2024.pdf",
            },
            {
                "page_content": "Inflation was 7.9 per cent in April 2023",
                "date": "01 April 2023",
                "title": "Kenya Consumer Price Indices and Inflation Rates April 2023",
                "score": 0.20,
                "page_url": "u2023#page=1",
                "url": "https://example/Kenya-Consumer-Price-Indices-and-Inflation-Rates-April-2023.pdf",
            },
        ]
        if candidate_k and candidate_k >= 320:
            return [
                {
                    "page_content": "Inflation was 4.1 per cent in April 2025",
                    "date": "01 April 2025",
                    "title": "Kenya Consumer Price Indices and Inflation Rates April 2025",
                    "score": 0.05,
                    "page_url": "u2025#page=1",
                    "url": "https://example/Kenya-Consumer-Price-Indices-and-Inflation-Rates-April-2025.pdf",
                }
            ] + base_docs
        return base_docs

    inq.similarity_search = fake_similarity

    captured_titles: dict[str, object] = {}

    def fake_query_texts(question, docs, **_kwargs):
        captured_titles["titles"] = [d["title"] for d in docs]
        return LlmResponse(
            answer_provided=True,
            most_likely_answer="4.1 per cent",
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

    inq.make_query(
        "What was Kenya's inflation rate in April 2025?",
        latest_filter=False,
        highlighting=True,
        latest_weight=0,
    )

    assert captured_candidate_k == [96, 320]
    assert captured_titles["titles"] == [
        "Kenya Consumer Price Indices and Inflation Rates April 2025"
    ]


def test_make_query_family_pre_filter_prefers_lagged_annual_report(monkeypatch):
    inq = Inquirer.__new__(Inquirer)
    inq.logger = MagicMock()
    inq.answer_threshold = 10
    inq.document_threshold = 10
    inq.k_docs = 3
    inq.k_contexts = 3
    inq.reranker_model_name = None
    inq.recency_bias_weight = 0.5
    inq.temporal_candidate_k = 96
    inq.reranker_candidate_k = 48

    captured_candidate_k: list[int | None] = []

    def fake_similarity(q, latest_filter=True, return_dicts=True, candidate_k=None):
        captured_candidate_k.append(candidate_k)
        return [
            {
                "page_content": "2024 outcomes in the 2024 Economic Survey",
                "date": "01 May 2024",
                "title": "2024 Economic Survey",
                "score": 0.10,
                "page_url": "u2024#page=283",
                "url": "https://example/2024-Economic-Survey.pdf",
            },
            {
                "page_content": "2024 outcomes in the 2025 Economic Survey",
                "date": "01 May 2025",
                "title": "2025 Economic Survey",
                "score": 0.20,
                "page_url": "u2025#page=331",
                "url": "https://example/2025-Economic-Survey.pdf",
            },
            {
                "page_content": "2024 quarterly trade bulletin",
                "date": "01 June 2024",
                "title": "Quarterly Trade Bulletin 2024",
                "score": 0.30,
                "page_url": "uother#page=12",
                "url": "https://example/Quarterly-Trade-Bulletin-2024.pdf",
            },
        ]

    inq.similarity_search = fake_similarity

    captured_titles: dict[str, object] = {}

    def fake_query_texts(question, docs, **_kwargs):
        captured_titles["titles"] = [d["title"] for d in docs]
        return LlmResponse(
            answer_provided=True,
            most_likely_answer="20.9 per cent",
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

    inq.make_query(
        "By what percentage did petroleum product imports increase in 2024?",
        latest_filter=False,
        highlighting=True,
        latest_weight=0,
    )

    assert captured_candidate_k == [96]
    assert captured_titles["titles"] == ["2025 Economic Survey"]


def test_make_query_family_pre_filter_retries_when_lagged_year_missing(
    monkeypatch,
):
    inq = Inquirer.__new__(Inquirer)
    inq.logger = MagicMock()
    inq.answer_threshold = 10
    inq.document_threshold = 10
    inq.k_docs = 3
    inq.k_contexts = 3
    inq.reranker_model_name = None
    inq.recency_bias_weight = 0.5
    inq.temporal_candidate_k = 96
    inq.lagged_year_candidate_k = 320
    inq.reranker_candidate_k = 48

    captured_candidate_k: list[int | None] = []

    def fake_similarity(q, latest_filter=True, return_dicts=True, candidate_k=None):
        captured_candidate_k.append(candidate_k)
        base_docs = [
            {
                "page_content": "Older recorded employment table",
                "date": "01 May 2020",
                "title": "2020 Economic Survey",
                "score": 0.10,
                "page_url": "u2020#page=71",
                "url": "https://example/2020-Economic-Survey.pdf",
            },
            {
                "page_content": "Older recorded employment table",
                "date": "01 May 2016",
                "title": "2016 Economic Survey",
                "score": 0.20,
                "page_url": "u2016#page=72",
                "url": "https://example/2016-Economic-Survey.pdf",
            },
        ]
        if candidate_k and candidate_k >= 320:
            return [
                {
                    "page_content": "Total recorded employment in 2022 was 19,148.2 thousand",
                    "date": "01 May 2023",
                    "title": "2023 Economic Survey",
                    "score": 0.05,
                    "page_url": "u2023#page=93",
                    "url": "https://example/2023-Economic-Survey.pdf",
                }
            ] + base_docs
        return base_docs

    inq.similarity_search = fake_similarity

    captured_titles: dict[str, object] = {}

    def fake_query_texts(question, docs, **_kwargs):
        captured_titles["titles"] = [d["title"] for d in docs]
        return LlmResponse(
            answer_provided=True,
            most_likely_answer="19,148.2 thousand",
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

    inq.make_query(
        "What was the total recorded employment in Kenya in 2022, in thousands?",
        latest_filter=False,
        highlighting=True,
        latest_weight=0,
    )

    assert captured_candidate_k == [96, 320]
    assert captured_titles["titles"] == ["2023 Economic Survey"]


def test_make_query_family_pre_filter_retries_wider_pool_on_year_plus_two(
    monkeypatch,
):
    inq = Inquirer.__new__(Inquirer)
    inq.logger = MagicMock()
    inq.answer_threshold = 10
    inq.document_threshold = 10
    inq.k_docs = 3
    inq.k_contexts = 3
    inq.reranker_model_name = None
    inq.recency_bias_weight = 0.5
    inq.temporal_candidate_k = 96
    inq.lagged_year_candidate_k = 320
    inq.reranker_candidate_k = 48

    captured_candidate_k: list[int | None] = []

    def fake_similarity(q, latest_filter=True, return_dicts=True, candidate_k=None):
        captured_candidate_k.append(candidate_k)
        base_docs = [
            {
                "page_content": "historical disability note",
                "date": "01 May 2023",
                "title": "2023 Economic Survey",
                "score": 0.30,
                "page_url": "u2023#page=364",
                "url": "https://example/2023-Economic-Survey.pdf",
            },
            {
                "page_content": "2019 census disability note in 2021 survey",
                "date": "01 May 2021",
                "title": "2021 Economic Survey",
                "score": 0.20,
                "page_url": "u2021#page=379",
                "url": "https://example/2021-Economic-Survey.pdf",
            },
        ]
        if candidate_k and candidate_k >= 320:
            return [
                {
                    "page_content": "The proportion of persons with disability stood at 2.2 per cent (918,270 persons).",
                    "date": "01 May 2020",
                    "title": "2020 Economic Survey",
                    "score": 0.10,
                    "page_url": "u2020#page=413",
                    "url": "https://example/2020-Economic-Survey.pdf",
                }
            ] + base_docs
        return base_docs

    inq.similarity_search = fake_similarity

    captured_titles: dict[str, object] = {}

    def fake_query_texts(question, docs, **_kwargs):
        captured_titles["titles"] = [d["title"] for d in docs]
        return LlmResponse(
            answer_provided=True,
            most_likely_answer="918,270 persons",
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

    inq.make_query(
        "How many people aged 5 years and above had a disability in Kenya "
        "according to the 2019 population census?",
        latest_filter=False,
        highlighting=True,
        latest_weight=0,
    )

    assert captured_candidate_k == [96, 320]
    assert captured_titles["titles"] == ["2020 Economic Survey"]


def test_make_query_doc_local_page_expansion_promotes_neighbor_page(monkeypatch):
    inq = Inquirer.__new__(Inquirer)
    inq.logger = MagicMock()
    inq.answer_threshold = 10
    inq.document_threshold = 10
    inq.k_docs = 2
    inq.k_contexts = 2
    inq.reranker_model_name = "dummy-reranker"
    inq.recency_bias_weight = 0.0
    inq.reranker_candidate_k = 24
    inq.temporal_candidate_k = 24
    inq.page_expansion_doc_limit = 2
    inq.page_expansion_seed_pages_per_doc = 2
    inq.page_expansion_window = 1

    base_url = "https://example.com/housing.pdf"

    def fake_similarity(q, latest_filter=True, return_dicts=True, candidate_k=None):
        return [
            {
                "page_content": "housing chart overview",
                "date": "01 September 2024",
                "title": "2023-24 Kenya Housing Survey Basic Report",
                "score": 0.10,
                "page_number": 73,
                "page_url": f"{base_url}#page=73",
                "url": base_url,
            },
            {
                "page_content": "housing chart summary",
                "date": "01 September 2024",
                "title": "2023-24 Kenya Housing Survey Basic Report",
                "score": 0.12,
                "page_number": 75,
                "page_url": f"{base_url}#page=75",
                "url": base_url,
            },
            {
                "page_content": "other report content",
                "date": "01 January 2024",
                "title": "Other Report",
                "score": 0.20,
                "page_number": 1,
                "page_url": "https://example.com/other.pdf#page=1",
                "url": "https://example.com/other.pdf",
            },
        ]

    inq.similarity_search = fake_similarity

    captured: dict[str, object] = {}

    def fake_query_texts(question, docs, **_kwargs):
        captured["page_urls"] = [doc["page_url"] for doc in docs]
        return LlmResponse(
            answer_provided=True,
            most_likely_answer="Bungalow",
            highlighting1=[],
            highlighting2=[],
            highlighting3=[],
            reasoning=None,
        )

    inq.query_texts = fake_query_texts
    inq.db = SimpleNamespace(
        docstore=SimpleNamespace(
            _dict={
                "p73": SimpleNamespace(
                    model_dump=lambda: {
                        "page_content": "housing chart overview",
                        "metadata": {
                            "date": "01 September 2024",
                            "title": "2023-24 Kenya Housing Survey Basic Report",
                            "page_number": 73,
                            "page_url": "#page=73",
                            "url": base_url,
                        },
                    }
                ),
                "p74": SimpleNamespace(
                    model_dump=lambda: {
                        "page_content": "exact dwelling unit answer evidence",
                        "metadata": {
                            "date": "01 September 2024",
                            "title": "2023-24 Kenya Housing Survey Basic Report",
                            "page_number": 74,
                            "page_url": "#page=74",
                            "url": base_url,
                        },
                    }
                ),
                "p75": SimpleNamespace(
                    model_dump=lambda: {
                        "page_content": "housing chart summary",
                        "metadata": {
                            "date": "01 September 2024",
                            "title": "2023-24 Kenya Housing Survey Basic Report",
                            "page_number": 75,
                            "page_url": "#page=75",
                            "url": base_url,
                        },
                    }
                ),
            }
        )
    )

    monkeypatch.setattr(
        "statschat.generative.cloud_llm._get_reranker",
        lambda model_name: SimpleNamespace(
            predict=lambda pairs: [
                (
                    0.75
                    if "exact dwelling unit answer evidence" in passage
                    else (
                        0.65
                        if "housing chart overview" in passage
                        else 0.60 if "housing chart summary" in passage else 0.10
                    )
                )
                for _, passage in pairs
            ]
        ),
    )
    monkeypatch.setattr(
        "statschat.generative.cloud_llm.highlighter",
        lambda docs, validated_response, logger: docs,
    )

    docs_out, _, _ = inq.make_query(
        "What evidence is most relevant in the 2024 report?",
        latest_filter=False,
        highlighting=True,
        latest_weight=0,
    )

    assert any(page_url.endswith("#page=74") for page_url in captured["page_urls"])
    assert any(doc["page_url"].endswith("#page=74") for doc in docs_out)


def test_make_query_doc_local_page_expansion_preserves_top_k_membership(
    monkeypatch,
):
    inq = Inquirer.__new__(Inquirer)
    inq.logger = MagicMock()
    inq.answer_threshold = 10
    inq.document_threshold = 10
    inq.k_docs = 2
    inq.k_contexts = 2
    inq.reranker_model_name = "dummy-reranker"
    inq.recency_bias_weight = 0.0
    inq.reranker_candidate_k = 24
    inq.temporal_candidate_k = 24
    inq.page_expansion_doc_limit = 2
    inq.page_expansion_seed_pages_per_doc = 2
    inq.page_expansion_window = 1

    base_url = "https://example.com/housing.pdf"
    other_url = "https://example.com/other.pdf"

    def fake_similarity(q, latest_filter=True, return_dicts=True, candidate_k=None):
        return [
            {
                "page_content": "housing chart overview",
                "date": "01 September 2024",
                "title": "2023-24 Kenya Housing Survey Basic Report",
                "score": 0.10,
                "page_number": 73,
                "page_url": f"{base_url}#page=73",
                "url": base_url,
            },
            {
                "page_content": "other report gold evidence",
                "date": "01 January 2024",
                "title": "Other Report",
                "score": 0.11,
                "page_number": 1,
                "page_url": f"{other_url}#page=1",
                "url": other_url,
            },
            {
                "page_content": "housing chart summary",
                "date": "01 September 2024",
                "title": "2023-24 Kenya Housing Survey Basic Report",
                "score": 0.20,
                "page_number": 75,
                "page_url": f"{base_url}#page=75",
                "url": base_url,
            },
        ]

    inq.similarity_search = fake_similarity

    captured: dict[str, object] = {}

    def fake_query_texts(question, docs, **_kwargs):
        captured["page_urls"] = [doc["page_url"] for doc in docs]
        return LlmResponse(
            answer_provided=True,
            most_likely_answer="Some answer",
            highlighting1=[],
            highlighting2=[],
            highlighting3=[],
            reasoning=None,
        )

    inq.query_texts = fake_query_texts
    inq.db = SimpleNamespace(
        docstore=SimpleNamespace(
            _dict={
                "p73": SimpleNamespace(
                    model_dump=lambda: {
                        "page_content": "housing chart overview",
                        "metadata": {
                            "date": "01 September 2024",
                            "title": "2023-24 Kenya Housing Survey Basic Report",
                            "page_number": 73,
                            "page_url": "#page=73",
                            "url": base_url,
                        },
                    }
                ),
                "p74": SimpleNamespace(
                    model_dump=lambda: {
                        "page_content": "neighbor page but weaker evidence",
                        "metadata": {
                            "date": "01 September 2024",
                            "title": "2023-24 Kenya Housing Survey Basic Report",
                            "page_number": 74,
                            "page_url": "#page=74",
                            "url": base_url,
                        },
                    }
                ),
                "p75": SimpleNamespace(
                    model_dump=lambda: {
                        "page_content": "housing chart summary",
                        "metadata": {
                            "date": "01 September 2024",
                            "title": "2023-24 Kenya Housing Survey Basic Report",
                            "page_number": 75,
                            "page_url": "#page=75",
                            "url": base_url,
                        },
                    }
                ),
            }
        )
    )

    monkeypatch.setattr(
        "statschat.generative.cloud_llm._get_reranker",
        lambda model_name: SimpleNamespace(
            predict=lambda pairs: [
                (
                    0.90
                    if "housing chart overview" in passage
                    else (
                        0.80
                        if "other report gold evidence" in passage
                        else 0.60 if "housing chart summary" in passage else 0.50
                    )
                )
                for _, passage in pairs
            ]
        ),
    )
    monkeypatch.setattr(
        "statschat.generative.cloud_llm.highlighter",
        lambda docs, validated_response, logger: docs,
    )

    docs_out, _, _ = inq.make_query(
        "What evidence is most relevant in the 2024 report?",
        latest_filter=False,
        highlighting=True,
        latest_weight=0,
    )

    returned_urls = {doc["url"] for doc in docs_out}
    assert other_url in returned_urls
    assert base_url in returned_urls
    assert any(page_url.endswith("#page=1") for page_url in captured["page_urls"])


def test_make_query_doc_local_page_expansion_noops_with_empty_page_index(monkeypatch):
    inq = Inquirer.__new__(Inquirer)
    inq.logger = MagicMock()
    inq.answer_threshold = 10
    inq.document_threshold = 10
    inq.k_docs = 2
    inq.k_contexts = 2
    inq.reranker_model_name = "dummy-reranker"
    inq.recency_bias_weight = 0.0
    inq.reranker_candidate_k = 24
    inq.temporal_candidate_k = 24
    inq.page_expansion_doc_limit = 2
    inq.page_expansion_seed_pages_per_doc = 2
    inq.page_expansion_window = 1

    def fake_similarity(q, latest_filter=True, return_dicts=True, candidate_k=None):
        return [
            {
                "page_content": "best evidence",
                "date": "01 January 2024",
                "title": "Best Report",
                "score": 0.10,
                "page_number": 1,
                "page_url": "https://example.com/best.pdf#page=1",
                "url": "https://example.com/best.pdf",
            },
            {
                "page_content": "second evidence",
                "date": "01 January 2024",
                "title": "Second Report",
                "score": 0.11,
                "page_number": 1,
                "page_url": "https://example.com/second.pdf#page=1",
                "url": "https://example.com/second.pdf",
            },
        ]

    inq.similarity_search = fake_similarity

    captured: dict[str, object] = {}

    def fake_query_texts(question, docs, **_kwargs):
        captured["titles"] = [doc["title"] for doc in docs]
        return LlmResponse(
            answer_provided=True,
            most_likely_answer="Some answer",
            highlighting1=[],
            highlighting2=[],
            highlighting3=[],
            reasoning=None,
        )

    inq.query_texts = fake_query_texts
    inq.db = SimpleNamespace(docstore=SimpleNamespace(_dict={}))

    monkeypatch.setattr(
        "statschat.generative.cloud_llm._get_reranker",
        lambda model_name: SimpleNamespace(predict=lambda pairs: [0.9, 0.8]),
    )
    monkeypatch.setattr(
        "statschat.generative.cloud_llm.highlighter",
        lambda docs, validated_response, logger: docs,
    )

    docs_out, _, _ = inq.make_query(
        "What was the poverty rate in Kenya as of 2024?",
        latest_filter=False,
        highlighting=True,
        latest_weight=0,
    )

    assert [doc["title"] for doc in docs_out] == ["Best Report", "Second Report"]
    assert captured["titles"] == ["Best Report", "Second Report"]


def test_make_query_temporal_pre_filter_falls_back_to_full_pool(monkeypatch):
    inq = Inquirer.__new__(Inquirer)
    inq.logger = MagicMock()
    inq.answer_threshold = 10
    inq.document_threshold = 10
    inq.k_docs = 3
    inq.k_contexts = 3
    inq.reranker_model_name = None
    inq.recency_bias_weight = 0.5
    inq.temporal_candidate_k = 96
    inq.reranker_candidate_k = 48

    # No doc actually matches Q3 2023 — pre-filter must fall back, not return empty.
    # Future dates are handled by the guardrail before retrieval.
    inq.similarity_search = (
        lambda q, latest_filter=True, return_dicts=True, candidate_k=None: [
            {
                "page_content": "some content",
                "date": "01 December 2024",
                "title": "Kenya quarterly gross domestic product third quarter 2024",
                "score": 0.10,
                "page_url": "u#page=1",
                "url": "https://example/u.pdf",
            }
        ]
    )

    captured: dict[str, object] = {}

    def fake_query_texts(question, docs, **_kwargs):
        captured["count"] = len(docs)
        return LlmResponse(
            answer_provided=True,
            most_likely_answer="N/A",
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

    inq.make_query(
        "What was Kenya's GDP growth in Q3 2023?",
        latest_filter=False,
        highlighting=True,
        latest_weight=0,
    )

    # Empty pre-filter must fall back to full pool, not 0 docs
    assert captured["count"] == 1


def test_inquirer_temporal_candidate_k_default(monkeypatch):
    monkeypatch.setattr(
        "statschat.generative.cloud_llm.HuggingFaceEmbeddings", lambda *a, **k: None
    )
    monkeypatch.setattr(
        "statschat.generative.cloud_llm.FAISS.load_local", lambda *a, **k: None
    )
    monkeypatch.setattr(
        "statschat.generative.cloud_llm.ChatOpenAI", lambda *a, **k: object()
    )

    inquirer = Inquirer(provider="openrouter", k_docs=8)

    # k_docs=8 -> max(8*12, 96) = 96
    assert inquirer.temporal_candidate_k == 96
    assert inquirer.lagged_year_candidate_k == 320
    # And it must be at least as large as the standard reranker pool
    assert inquirer.temporal_candidate_k >= inquirer.reranker_candidate_k
    assert inquirer.lagged_year_candidate_k >= inquirer.temporal_candidate_k


def test_build_reranker_passage_includes_metadata_and_content():
    doc = {
        "title": "Facts Figures 2024",
        "date": "01 May 2024",
        "page_number": 29,
        "page_content": "Figure 2: Quarterly GDP growth rate, 2019 – 2023",
    }

    passage = _build_reranker_passage(doc)

    assert "Title: Facts Figures 2024" in passage
    assert "Date: 01 May 2024" in passage
    assert "Page: 29" in passage
    assert "Quarterly GDP growth rate, 2019" in passage
