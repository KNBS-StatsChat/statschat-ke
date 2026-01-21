from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

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
            doc1 = SimpleNamespace(model_dump=lambda: {"page_content": "d1", "metadata": {"title": "A", "date": "2024-01-01"}})
            doc2 = SimpleNamespace(model_dump=lambda: {"page_content": "d2", "metadata": {"title": "B", "date": "2020-01-01"}})
            return [(doc1, 0.4), (doc2, 0.9)]

        return SimpleNamespace(similarity_search_with_score=sim)

    monkeypatch.setattr("statschat.generative.local_llm.FAISS.load_local", fake_load_local)

    results = local_llm.similarity_search("q", latest_filter=False, return_dicts=True)
    # Both matches are below the default similarity threshold in the module (2.0)
    assert len(results) == 2
    assert results[0]["page_content"] == "d1"


def test_generate_response_uses_tokenizer_and_model():
    # Fake tokenizer: returns object with input_ids that has .to() and provides decode()
    class FakeInputIDs:
        def to(self, device):
            return "input_ids_on_" + str(device)

    class FakeTokenizer:
        def __call__(self, text, return_tensors=None):
            return SimpleNamespace(input_ids=FakeInputIDs())

        def decode(self, out, skip_special_tokens=True):
            return "RESPONSE TEXT"

    class FakeModel:
        def __init__(self):
            self.device = "cpu"

        def generate(self, input_ids, max_new_tokens=1000):
            # return an iterable whose first element decodes to some tokens
            return [[1, 2, 3]]

    tokenizer = FakeTokenizer()
    model = FakeModel()
    resp = local_llm.generate_response("hello", model, tokenizer)
    assert isinstance(resp, str)
    assert "RESPONSE TEXT" == resp
