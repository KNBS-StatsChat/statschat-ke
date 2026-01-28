"""Unit tests for local_llm helpers.

These tests validate metadata flattening, similarity filtering, and response
generation with lightweight fakes to avoid heavy model dependencies.
"""

from types import SimpleNamespace

import statschat.generative.local_llm as local_llm


def test_flatten_meta_local_merges_metadata():
    payload = {"x": 1, "metadata": {"title": "T", "date": "2024-01-01"}}
    out = local_llm.flatten_meta(payload)
    assert out["x"] == 1
    assert out["title"] == "T"
    assert "metadata" not in out


def test_similarity_search_local_filters(monkeypatch):
    # fake FAISS result: one under threshold, one above
    def fake_load_local(root, embeddings, allow_dangerous_deserialization=True):
        def sim(query, k):
            doc1 = SimpleNamespace(
                model_dump=lambda: {
                    "page_content": "d1",
                    "metadata": {"title": "A", "date": "2024-01-01"},
                }
            )
            doc2 = SimpleNamespace(
                model_dump=lambda: {
                    "page_content": "d2",
                    "metadata": {"title": "B", "date": "2020-01-01"},
                }
            )
            return [(doc1, 0.4), (doc2, 0.9)]

        return SimpleNamespace(similarity_search_with_score=sim)

    monkeypatch.setattr(
        "statschat.generative.local_llm.FAISS.load_local", fake_load_local
    )

    results = local_llm.similarity_search("q", latest_filter=False, return_dicts=True)
    # Both matches are below the default similarity threshold in the module (2.0)
    assert len(results) == 2
    assert results[0]["page_content"] == "d1"


def test_similarity_search_local_latest_filter_uses_latest_db(tmp_path, monkeypatch):
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
                    "metadata": {"title": "A", "date": "2024-01-01"},
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

    results = local_llm.similarity_search("q", latest_filter=True, return_dicts=True)
    assert seen["root"] == "data/db_langchain_latest"
    assert len(results) == 1
    assert results[0]["page_content"] == "d_latest"


def test_generate_response_uses_tokenizer_and_model():
    # Fake tokenizer: returns object with input_ids/attention_mask that has .to()
    class FakeInputIDs:
        def to(self, device):
            return "input_ids_on_" + str(device)

    class FakeAttentionMask:
        def to(self, device):
            return "attention_mask_on_" + str(device)

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
