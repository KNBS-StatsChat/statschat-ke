"""Unit tests for cloud_llm Inquirer behavior.

Covers metadata flattening, similarity filtering, query parsing behavior,
reranking/context selection, and error handling for invalid provider config.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from statschat.generative.cloud_llm import (
    Inquirer,
    _apply_recency_bias,
    _build_reranker_passage,
    _doc_report_families,
    _doc_matches_query_temporal,
    _doc_temporal_tokens,
    _extract_months,
    _extract_quarters,
    _extract_years,
    _select_lagged_year_subset,
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

    def fake_query_texts(question, docs):
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


def test_infer_query_report_families_from_metric_hints():
    assert "economic_survey" in infer_query_report_families(
        "By what percentage did petroleum product imports increase in 2024?"
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

    def fake_query_texts(question, docs):
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

    captured_candidate_k: dict[str, object] = {}

    def fake_similarity(q, latest_filter=True, return_dicts=True, candidate_k=None):
        captured_candidate_k["value"] = candidate_k
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

    def fake_query_texts(question, docs):
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

    assert captured_candidate_k["value"] == 96
    assert captured_titles["titles"] == ["2025 Economic Survey"]


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

    # No doc actually matches Q3 2099 — pre-filter must fall back, not return empty
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

    def fake_query_texts(question, docs):
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
        "What was Kenya's GDP growth in Q3 2099?",
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
    # And it must be at least as large as the standard reranker pool
    assert inquirer.temporal_candidate_k >= inquirer.reranker_candidate_k


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
