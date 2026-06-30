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


def _resolve_mode_specific_search_config(search_config, mode):
    resolved = dict(search_config or {})
    if mode == "cloud":
        resolved["generative_model_name"] = (
            resolved.get("generative_model_name_cloud")
            or resolved.get("generative_model_name")
            or "stub-cloud-model"
        )
    elif mode == "local":
        resolved["generative_model_name"] = (
            resolved.get("generative_model_name_local")
            or resolved.get("generative_model_name")
            or "stub-local-model"
        )
    return resolved


def _load_app_with_dummy_inquirer(make_query_impl, temporal_constraint_impl=None):
    """
    Dynamically load main_api_cloud with a patched cloud_llm.Inquirer that
    uses the provided make_query implementation. Avoids FAISS/LLM downloads.
    """
    dummy_response_ns = types.SimpleNamespace()
    had_cloud_llm = "statschat.generative.cloud_llm" in sys.modules
    previous_cloud_llm = sys.modules.get("statschat.generative.cloud_llm")

    class DummyInquirer:
        def __init__(self, *args, **kwargs):
            pass

        def make_query(
            self, question, latest_filter=True, latest_weight=1, highlighting=True
        ):
            return make_query_impl(question, latest_filter, latest_weight, highlighting)

    fake_cloud_llm = types.SimpleNamespace(
        Inquirer=DummyInquirer,
        # main_api_cloud now imports has_temporal_constraint to safeguard
        # historical queries; tests can override the stub via the
        # temporal_constraint_impl argument.
        has_temporal_constraint=temporal_constraint_impl or (lambda question: False),
        resolve_mode_specific_search_config=_resolve_mode_specific_search_config,
    )
    sys.modules["statschat.generative.cloud_llm"] = fake_cloud_llm

    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, "../.."))
    spec = importlib.util.spec_from_file_location(
        "main_api_cloud", os.path.join(project_root, "fast-api", "main_api_cloud.py")
    )
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    finally:
        if had_cloud_llm:
            sys.modules["statschat.generative.cloud_llm"] = previous_cloud_llm
        else:
            sys.modules.pop("statschat.generative.cloud_llm", None)
    return module.app, dummy_response_ns


@pytest.fixture
def client_factory(monkeypatch):
    def _factory(make_query_impl, temporal_constraint_impl=None):
        monkeypatch.delenv("STATSCHAT_API_KEY", raising=False)
        monkeypatch.delenv("STATSCHAT_RATE_LIMIT_PER_MINUTE", raising=False)
        app, ns = _load_app_with_dummy_inquirer(
            make_query_impl, temporal_constraint_impl=temporal_constraint_impl
        )
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
async def test_temporal_query_overrides_latest_filter(client_factory):
    """A query with explicit year/month/quarter must force latest_filter=False
    even when the client requests content_type=latest, so historical reports
    in the full FAISS store remain searchable."""

    captured: dict[str, object] = {}

    def make_query_impl(question, latest_filter, latest_weight, highlighting):
        captured["latest_filter"] = latest_filter
        captured["question"] = question
        return (
            [{"page_url": "http://example.com/doc", "title": "Doc", "score": 0.1}],
            "Answer",
            types.SimpleNamespace(__dict__={"raw": True}),
        )

    # Stub has_temporal_constraint to behave like the real one for this case.
    async with client_factory(
        make_query_impl,
        temporal_constraint_impl=lambda question: "2023" in question,
    ) as client:
        resp = await client.get(
            "/search",
            params={
                "q": "What was Kenya's GDP growth rate in Quarter 3 of 2023?",
                "content_type": "latest",
            },
        )

    assert resp.status_code == 200
    # Override fired: even though content_type=latest, make_query saw False
    assert captured["latest_filter"] is False


@pytest.mark.anyio
async def test_non_temporal_query_preserves_latest_filter(client_factory):
    """A year-less query in content_type=latest must keep latest_filter=True."""

    captured: dict[str, object] = {}

    def make_query_impl(question, latest_filter, latest_weight, highlighting):
        captured["latest_filter"] = latest_filter
        return (
            [{"page_url": "http://example.com/doc", "title": "Doc", "score": 0.1}],
            "Answer",
            types.SimpleNamespace(__dict__={"raw": True}),
        )

    async with client_factory(
        make_query_impl,
        temporal_constraint_impl=lambda question: False,
    ) as client:
        resp = await client.get(
            "/search",
            params={"q": "What is the population of Kenya?", "content_type": "latest"},
        )

    assert resp.status_code == 200
    assert captured["latest_filter"] is True


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


@pytest.mark.anyio
async def test_search_requires_api_key_when_configured(monkeypatch):
    """When STATSCHAT_API_KEY is configured, /search rejects unauthenticated calls."""

    def make_query_impl(question, latest_filter, latest_weight, highlighting):
        return (
            [{"page_url": "http://example.com/doc", "title": "Doc", "score": 0.1}],
            "Answer",
            types.SimpleNamespace(__dict__={"raw": True}),
        )

    app, _ = _load_app_with_dummy_inquirer(make_query_impl)
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as client:
        monkeypatch.setenv("STATSCHAT_API_KEY", "secret")
        missing = await client.get("/search", params={"q": "Population"})
        wrong = await client.get(
            "/search", params={"q": "Population"}, headers={"X-API-Key": "bad"}
        )
        allowed = await client.get(
            "/search", params={"q": "Population"}, headers={"X-API-Key": "secret"}
        )

    assert missing.status_code == 401
    assert wrong.status_code == 401
    assert allowed.status_code == 200


@pytest.mark.anyio
async def test_cors_allows_configured_origin(monkeypatch):
    """CORS middleware reflects explicitly configured frontend origins."""

    monkeypatch.setenv("STATSCHAT_CORS_ORIGINS", "https://frontend.example")

    def make_query_impl(question, latest_filter, latest_weight, highlighting):
        return (
            [{"page_url": "http://example.com/doc", "title": "Doc", "score": 0.1}],
            "Answer",
            types.SimpleNamespace(__dict__={"raw": True}),
        )

    app, _ = _load_app_with_dummy_inquirer(make_query_impl)
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as client:
        response = await client.options(
            "/search",
            headers={
                "Origin": "https://frontend.example",
                "Access-Control-Request-Method": "GET",
            },
        )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://frontend.example"


@pytest.mark.anyio
async def test_rate_limit_rejects_excess_requests(monkeypatch):
    """Optional in-process rate limiting protects query-costing endpoints."""

    monkeypatch.setenv("STATSCHAT_RATE_LIMIT_PER_MINUTE", "1")

    def make_query_impl(question, latest_filter, latest_weight, highlighting):
        return (
            [{"page_url": "http://example.com/doc", "title": "Doc", "score": 0.1}],
            "Answer",
            types.SimpleNamespace(__dict__={"raw": True}),
        )

    app, _ = _load_app_with_dummy_inquirer(make_query_impl)
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as client:
        first = await client.get("/search", params={"q": "Population"})
        second = await client.get("/search", params={"q": "Population"})

    assert first.status_code == 200
    assert second.status_code == 429
