"""Unit tests for local_llm helpers.

These tests validate metadata flattening, similarity filtering, and response
generation with lightweight fakes to avoid heavy model dependencies.
"""

from types import SimpleNamespace

import statschat.generative.local_llm as local_llm


def test_flatten_meta_local_merges_metadata():
    payload = {
        "x": 1,
        "metadata": {
            "title": "T",
            "date": "2024-01-01",
            "url": "https://example.com/test.pdf",
            "page_number": 7,
            "page_url": "#page=7",
        },
    }
    out = local_llm.flatten_meta(payload)
    assert out["x"] == 1
    assert out["title"] == "T"
    assert out["page_url"] == "https://example.com/test.pdf#page=7"
    assert "metadata" not in out


def test_similarity_search_local_filters(monkeypatch):
    local_llm._get_embeddings.cache_clear()
    local_llm._load_faiss_cached.cache_clear()
    local_llm._get_local_retrieval_config.cache_clear()

    # fake FAISS result: one under threshold, one above
    def fake_load_local(root, embeddings, allow_dangerous_deserialization=True):
        def sim(query, k):
            doc1 = SimpleNamespace(
                model_dump=lambda: {
                    "page_content": "d1",
                    "metadata": {
                        "title": "A",
                        "date": "2024-01-01",
                        "url": "https://example.com/a.pdf",
                        "page_number": 3,
                        "page_url": "#page=3",
                    },
                }
            )
            doc2 = SimpleNamespace(
                model_dump=lambda: {
                    "page_content": "d2",
                    "metadata": {
                        "title": "B",
                        "date": "2020-01-01",
                        "url": "https://example.com/b.pdf",
                        "page_number": 9,
                        "page_url": "#page=9",
                    },
                }
            )
            return [(doc1, 0.4), (doc2, 0.9)]

        return SimpleNamespace(similarity_search_with_score=sim)

    monkeypatch.setattr(
        "statschat.generative.local_llm.FAISS.load_local", fake_load_local
    )
    monkeypatch.setattr(
        "statschat.generative.local_llm.HuggingFaceEmbeddings", lambda *a, **k: None
    )
    monkeypatch.setattr(
        local_llm,
        "_get_local_retrieval_config",
        lambda: {
            "k_docs": 3,
            "similarity_threshold": 2.0,
            "embedding_model_name": "sentence-transformers/all-mpnet-base-v2",
            "faiss_db_root": "data/db_langchain",
            "reranker_model_name": "cross-encoder/ms-marco-MiniLM-L-6-v2",
            "reranker_candidate_k": 24,
            "recency_bias_weight": 0.5,
        },
    )
    monkeypatch.setattr(local_llm, "_get_reranker", lambda *_a, **_k: None)
    monkeypatch.setattr(
        local_llm,
        "_apply_recency_bias",
        lambda results, *_a, **_k: [
            doc | {"selection_score": float(doc["reranker_score"])} for doc in results
        ],
    )

    class FakeReranker:
        @staticmethod
        def predict(_pairs):
            return [0.8, 0.2]

    monkeypatch.setattr(local_llm, "_get_reranker", lambda *_a, **_k: FakeReranker())

    results = local_llm.similarity_search("q", latest_filter=False, return_dicts=True)
    # Both matches are below the default similarity threshold in the module (2.0)
    assert len(results) == 2
    assert results[0]["page_content"] == "d1"
    assert results[0]["page_url"] == "https://example.com/a.pdf#page=3"


def test_similarity_search_local_latest_filter_uses_latest_db(tmp_path, monkeypatch):
    local_llm._get_embeddings.cache_clear()
    local_llm._load_faiss_cached.cache_clear()
    local_llm._get_local_retrieval_config.cache_clear()

    monkeypatch.setattr("pathlib.Path.cwd", lambda *a, **k: tmp_path)
    (tmp_path / "data" / "db_langchain_update").mkdir(parents=True)
    (tmp_path / "data" / "db_langchain_latest").mkdir(parents=True)

    seen = {}

    def fake_load_local(root, embeddings, allow_dangerous_deserialization=True):
        seen["root"] = root

        def sim(query, k):
            doc = SimpleNamespace(
                model_dump=lambda: {
                    "page_content": "d_latest",
                    "metadata": {
                        "title": "A",
                        "date": "2024-01-01",
                        "url": "https://example.com/latest.pdf",
                        "page_number": 1,
                        "page_url": "#page=1",
                    },
                }
            )
            return [(doc, 0.4)]

        return SimpleNamespace(similarity_search_with_score=sim)

    monkeypatch.setattr(
        "statschat.generative.local_llm.HuggingFaceEmbeddings", lambda *a, **k: None
    )
    monkeypatch.setattr(
        "statschat.generative.local_llm.FAISS.load_local", fake_load_local
    )
    monkeypatch.setattr(
        local_llm,
        "_get_local_retrieval_config",
        lambda: {
            "k_docs": 3,
            "similarity_threshold": 2.0,
            "embedding_model_name": "sentence-transformers/all-mpnet-base-v2",
            "faiss_db_root": "data/db_langchain",
            "reranker_model_name": "cross-encoder/ms-marco-MiniLM-L-6-v2",
            "reranker_candidate_k": 24,
            "recency_bias_weight": 0.5,
        },
    )
    monkeypatch.setattr(
        local_llm,
        "_apply_recency_bias",
        lambda results, *_a, **_k: [
            doc | {"selection_score": float(doc["reranker_score"])} for doc in results
        ],
    )

    class FakeReranker:
        @staticmethod
        def predict(_pairs):
            return [0.8]

    monkeypatch.setattr(local_llm, "_get_reranker", lambda *_a, **_k: FakeReranker())

    results = local_llm.similarity_search("q", latest_filter=True, return_dicts=True)
    assert seen["root"] == "data/db_langchain_latest"
    assert len(results) == 1
    assert results[0]["page_content"] == "d_latest"
    assert results[0]["page_url"] == "https://example.com/latest.pdf#page=1"


def test_select_generation_contexts_allows_multiple_chunks_from_strong_doc():
    results = [
        {
            "title": "Doc A",
            "date": "2024-01-01",
            "page_url": "https://example.com/a.pdf#page=1",
            "selection_score": 2.0,
        },
        {
            "title": "Doc A",
            "date": "2024-01-01",
            "page_url": "https://example.com/a.pdf#page=2",
            "selection_score": 1.9,
        },
        {
            "title": "Doc A",
            "date": "2024-01-01",
            "page_url": "https://example.com/a.pdf#page=3",
            "selection_score": 1.85,
        },
        {
            "title": "Doc B",
            "date": "2023-01-01",
            "page_url": "https://example.com/b.pdf#page=1",
            "selection_score": 1.80,
        },
    ]

    selected = local_llm.select_generation_contexts(results, k_contexts=4)

    # With max_chunks_per_doc=3, Doc A can contribute up to 3 chunks
    # but the diversity penalty means Doc B will interleave
    urls = [doc["page_url"] for doc in selected]
    assert "https://example.com/a.pdf#page=1" == urls[0]
    assert "https://example.com/b.pdf#page=1" in urls
    assert len(urls) == 4


def test_apply_recency_bias_prefers_newer_docs_for_yearless_queries():
    results = [
        {"title": "Older report", "date": "15 January 2014", "reranker_score": 0.8},
        {"title": "Newer report", "date": "01 January 2022", "reranker_score": 0.8},
    ]

    reranked = local_llm._apply_recency_bias(
        results,
        query="What is the average household size in Kenya?",
        recency_bias_weight=0.35,
    )

    assert reranked[1]["selection_score"] > reranked[0]["selection_score"]


def test_generate_response_uses_tokenizer_and_model():
    # Fake tokenizer: returns object with input_ids/attention_mask that has .to()
    class FakeInputIDs:
        shape = (1, 2)

        def to(self, device):
            return self

    class FakeAttentionMask:
        def to(self, device):
            return self

    class FakeTokenizer:
        eos_token_id = 0

        def __call__(self, text, return_tensors=None):
            return SimpleNamespace(
                input_ids=FakeInputIDs(), attention_mask=FakeAttentionMask()
            )

        def decode(self, out, skip_special_tokens=True):
            return "RESPONSE TEXT"

    class FakeModel:
        def __init__(self):
            self.device = "cpu"

        def generate(self, input_ids, **_kwargs):
            # return an iterable whose first element decodes to some tokens
            return [[1, 2, 3]]

    tokenizer = FakeTokenizer()
    model = FakeModel()
    resp = local_llm.generate_response("hello", model, tokenizer)
    assert isinstance(resp, str)
    assert "RESPONSE TEXT" == resp
