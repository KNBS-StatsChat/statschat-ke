"""
Integration-style tests for the cloud FastAPI app with heavy deps mocked out.

Focus on contract behavior (status codes, fallbacks) without loading real FAISS/LLMs.
"""

import importlib.util
import os
import sys
import types

import httpx
import pytest


def _load_app_with_dummy_inquirer(make_query_impl):
    """
    Dynamically load main_api_cloud with a patched cloud_llm.Inquirer that
    uses the provided make_query implementation. Avoids FAISS/LLM downloads.
    """
    dummy_response_ns = types.SimpleNamespace()

    class DummyInquirer:
        def __init__(self, *args, **kwargs):
            pass

        def make_query(
            self, question, latest_filter=True, latest_weight=1, highlighting=True
        ):
            return make_query_impl(question, latest_filter, latest_weight, highlighting)

    fake_cloud_llm = types.SimpleNamespace(Inquirer=DummyInquirer)
    sys.modules["statschat.generative.cloud_llm"] = fake_cloud_llm

    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, "../.."))
    spec = importlib.util.spec_from_file_location(
        "main_api_cloud", os.path.join(project_root, "fast-api", "main_api_cloud.py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.app, dummy_response_ns


@pytest.fixture
def client_factory():
    def _factory(make_query_impl):
        app, ns = _load_app_with_dummy_inquirer(make_query_impl)
        transport = httpx.ASGITransport(app=app)
        return httpx.AsyncClient(transport=transport, base_url="http://testserver")

    return _factory


@pytest.mark.anyio
async def test_search_invalid_content_type_falls_back(client_factory):
    """Falls back to the default content_type when an invalid value is provided."""

    def make_query_impl(question, latest_filter, latest_weight, highlighting):
        return (
            [{"page_url": "http://example.com/doc", "title": "Doc", "score": 0.1}],
            "Answer",
            types.SimpleNamespace(__dict__={"raw": True}),
        )

    async with client_factory(make_query_impl) as client:
        resp = await client.get(
            "/search", params={"q": "What is GDP?", "content_type": "bad"}
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["content_type"] == "latest"
    assert data["answer"] == "Answer"


@pytest.mark.anyio
async def test_search_handles_empty_results(client_factory):
    """Returns 200 with empty references/answer when retrieval yields no hits."""

    def make_query_impl(question, latest_filter, latest_weight, highlighting):
        return ([], "", types.SimpleNamespace(__dict__={}))

    async with client_factory(make_query_impl) as client:
        resp = await client.get("/search", params={"q": "No docs?"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["references"] == []
    assert data["answer"] == ""
