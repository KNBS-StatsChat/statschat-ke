"""Smoke tests for FastAPI endpoints with mocked model/search dependencies.

These tests load the local FastAPI app, stub heavyweight ML dependencies, and
exercise key endpoints to confirm basic routing and response schemas. They
validate redirects, OpenAPI exposure, search validation/fallback behavior, and
feedback handling without loading real models or hitting external services.
"""

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import httpx
import pytest


def _load_main_api_local():
    repo_root = Path(__file__).resolve().parents[2]
    api_path = repo_root / "fast-api" / "main_api_local.py"

    module_name = "fast_api_main_api_local"
    sys.modules.pop(module_name, None)

    if "torch" not in sys.modules:
        torch_stub = ModuleType("torch")
        torch_stub.float16 = "float16"
        sys.modules["torch"] = torch_stub

    if "transformers" not in sys.modules:
        transformers_stub = ModuleType("transformers")

        class AutoTokenizer:  # noqa: D401
            """Stub AutoTokenizer."""

            @staticmethod
            def from_pretrained(*_a, **_k):
                return object()

        class AutoModelForCausalLM:  # noqa: D401
            """Stub AutoModelForCausalLM."""

            @staticmethod
            def from_pretrained(*_a, **_k):
                return object()

        transformers_stub.AutoTokenizer = AutoTokenizer
        transformers_stub.AutoModelForCausalLM = AutoModelForCausalLM
        sys.modules["transformers"] = transformers_stub

    spec = importlib.util.spec_from_file_location(module_name, api_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _build_client(monkeypatch):
    main_api_local = _load_main_api_local()

    class DummyTokenizer:
        pass

    class DummyModel:
        pass

    monkeypatch.setattr(
        main_api_local.AutoTokenizer,
        "from_pretrained",
        lambda *a, **k: DummyTokenizer(),
    )
    monkeypatch.setattr(
        main_api_local.AutoModelForCausalLM,
        "from_pretrained",
        lambda *a, **k: DummyModel(),
    )

    monkeypatch.setattr(
        main_api_local,
        "similarity_search",
        lambda *_a, **_k: [
            {
                "page_content": "context one",
                "page_url": "https://example.com/one",
                "title": "Publication One",
            },
            {
                "page_content": "context two",
                "page_url": "https://example.com/two",
                "title": "Publication Two",
            },
        ],
    )
    monkeypatch.setattr(main_api_local, "generate_response", lambda *_a, **_k: {})
    monkeypatch.setattr(
        main_api_local,
        "format_response",
        lambda *_a, **_k: {
            "most_likely_answer": "Answer",
            "where_context_from": "context",
            "context_reference": "ref",
        },
    )

    transport = httpx.ASGITransport(app=main_api_local.app)
    return httpx.AsyncClient(transport=transport, base_url="http://testserver")


@pytest.mark.anyio
async def test_root_redirects_to_openapi(monkeypatch):
    async with _build_client(monkeypatch) as client:
        response = await client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/openapi.json"


@pytest.mark.anyio
async def test_openapi_contains_expected_paths(monkeypatch):
    async with _build_client(monkeypatch) as client:
        response = await client.get("/openapi.json")

    assert response.status_code == 200
    payload = response.json()
    assert "/search" in payload["paths"]
    assert "/feedback" in payload["paths"]


@pytest.mark.anyio
async def test_search_returns_minimal_schema(monkeypatch):
    async with _build_client(monkeypatch) as client:
        response = await client.get(
            "/search", params={"q": "Population", "content_type": "all"}
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["question"] == "Population"
    assert payload["content_type"] == "all"
    assert payload["answer"]
    assert payload["references"] == "https://example.com/one"
    assert payload["relevant_publication_one"] == "Publication One"
    assert payload["relevant_publication_two"] == "Publication Two"


@pytest.mark.anyio
async def test_search_empty_query_returns_422(monkeypatch):
    async with _build_client(monkeypatch) as client:
        response = await client.get("/search", params={"q": ""})

    assert response.status_code == 422
    payload = response.json()
    assert payload["detail"] == "Empty question"


@pytest.mark.anyio
async def test_search_fallbacks_to_latest_for_unknown_content_type(monkeypatch):
    async with _build_client(monkeypatch) as client:
        response = await client.get(
            "/search",
            params={"q": "Population", "content_type": "unknown"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["content_type"] == "latest"


@pytest.mark.anyio
async def test_search_debug_false_returns_core_fields(monkeypatch):
    async with _build_client(monkeypatch) as client:
        response = await client.get(
            "/search",
            params={"q": "Population", "content_type": "all", "debug": False},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["question"] == "Population"
    assert payload["answer"]
    assert payload["references"]


@pytest.mark.anyio
async def test_feedback_accepts_payload(monkeypatch):
    async with _build_client(monkeypatch) as client:
        response = await client.post(
            "/feedback",
            json={
                "rating": "1",
                "rating_comment": "Helpful",
                "question": "Population",
                "content_type": "all",
                "answer": "Answer",
            },
        )

    assert response.status_code == 202


@pytest.mark.anyio
async def test_feedback_accepts_minimal_payload(monkeypatch):
    async with _build_client(monkeypatch) as client:
        response = await client.post("/feedback", json={"rating": 1})

    assert response.status_code == 422
    payload = response.json()
    assert "detail" in payload
