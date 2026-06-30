"""Smoke tests for FastAPI endpoints with mocked model/search dependencies.

These tests load the local and cloud FastAPI apps, stub heavyweight ML and
cloud dependencies, and exercise key endpoints to confirm basic routing and
response schemas. They validate redirects, OpenAPI exposure, search
validation/fallback behavior, and feedback handling without loading real
models or hitting external services. Cloud tests replace the Inquirer and
latest-flag helpers to avoid network or credential requirements.
"""

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

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


def _load_main_api_local():
    repo_root = Path(__file__).resolve().parents[2]
    api_path = repo_root / "fast-api" / "main_api_local.py"

    module_name = "fast_api_main_api_local"
    sys.modules.pop(module_name, None)
    module_names_to_restore = (
        "torch",
        "transformers",
        "statschat.generative.cloud_llm",
        "statschat.generative.local_llm",
    )
    previous_modules = {
        name: (name in sys.modules, sys.modules.get(name))
        for name in module_names_to_restore
    }

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

    sys.modules.pop("statschat.generative.cloud_llm", None)
    cloud_llm_stub = ModuleType("statschat.generative.cloud_llm")

    class DummySharedRetrievalInquirer:
        pass

    cloud_llm_stub.Inquirer = DummySharedRetrievalInquirer
    cloud_llm_stub.resolve_mode_specific_search_config = (
        _resolve_mode_specific_search_config
    )
    sys.modules["statschat.generative.cloud_llm"] = cloud_llm_stub

    sys.modules.pop("statschat.generative.local_llm", None)
    local_llm_stub = ModuleType("statschat.generative.local_llm")
    local_llm_stub.generate_response = lambda *_a, **_k: {}
    local_llm_stub.format_response = lambda *_a, **_k: {
        "most_likely_answer": "Answer",
        "where_context_from": "context",
        "context_reference": "ref",
    }
    sys.modules["statschat.generative.local_llm"] = local_llm_stub

    spec = importlib.util.spec_from_file_location(module_name, api_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        for name, (had_module, previous_module) in previous_modules.items():
            if had_module:
                sys.modules[name] = previous_module
            else:
                sys.modules.pop(name, None)
    return module


def _build_client(monkeypatch):
    monkeypatch.delenv("STATSCHAT_API_KEY", raising=False)
    monkeypatch.delenv("STATSCHAT_RATE_LIMIT_PER_MINUTE", raising=False)
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

    main_api_local.MODEL = DummyModel()
    main_api_local.TOKENIZER = DummyTokenizer()

    class DummyRetriever:
        def retrieve_documents(self, *_a, **_k):
            return (
                [
                    {
                        "page_content": "context one",
                        "page_url": "https://example.com/one",
                        "title": "Publication One",
                        "score": 0.1,
                    },
                    {
                        "page_content": "context two",
                        "page_url": "https://example.com/two",
                        "title": "Publication Two",
                        "score": 0.2,
                    },
                ],
                False,
                0.1,
            )

        def select_generation_documents(self, _query, docs, **_kwargs):
            return docs[:2]

    monkeypatch.setattr(main_api_local, "get_retriever", lambda: DummyRetriever())
    monkeypatch.setattr(main_api_local, "get_latest_flag", lambda *_a, **_k: 1)
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


def _load_main_api_cloud():
    repo_root = Path(__file__).resolve().parents[2]
    api_path = repo_root / "fast-api" / "main_api_cloud.py"

    module_name = "fast_api_main_api_cloud"
    sys.modules.pop(module_name, None)
    had_cloud_llm = "statschat.generative.cloud_llm" in sys.modules
    previous_cloud_llm = sys.modules.get("statschat.generative.cloud_llm")

    class DummyInquirer:
        def __init__(self, **_kwargs):
            pass

        def make_query(self, question, latest_filter, latest_weight):
            class DummyResponse:
                def __init__(self):
                    self.raw = "debug"

            return (
                [
                    {
                        "page_url": "https://example.com/doc1.pdf#page=2",
                        "page_content": "Population context",
                        "title": "Doc 1",
                        "score": 0.12,
                    },
                    {
                        "page_url": "https://example.com/doc2.pdf#page=3",
                        "page_content": "Second context",
                        "title": "Doc 2",
                        "score": 0.34,
                    },
                ],
                "Answer",
                DummyResponse(),
            )

    sys.modules.pop("statschat.generative.cloud_llm", None)
    cloud_llm_stub = ModuleType("statschat.generative.cloud_llm")
    cloud_llm_stub.Inquirer = DummyInquirer
    cloud_llm_stub.has_temporal_constraint = lambda question: False
    cloud_llm_stub.resolve_mode_specific_search_config = (
        _resolve_mode_specific_search_config
    )
    sys.modules["statschat.generative.cloud_llm"] = cloud_llm_stub

    spec = importlib.util.spec_from_file_location(module_name, api_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        if had_cloud_llm:
            sys.modules["statschat.generative.cloud_llm"] = previous_cloud_llm
        else:
            sys.modules.pop("statschat.generative.cloud_llm", None)
    return module


def _build_cloud_client(monkeypatch):
    monkeypatch.delenv("STATSCHAT_API_KEY", raising=False)
    monkeypatch.delenv("STATSCHAT_RATE_LIMIT_PER_MINUTE", raising=False)
    main_api_cloud = _load_main_api_cloud()

    monkeypatch.setattr(main_api_cloud, "inquirer", main_api_cloud.inquirer)
    monkeypatch.setattr(main_api_cloud, "get_latest_flag", lambda *_a, **_k: 0.7)

    transport = httpx.ASGITransport(app=main_api_cloud.app)
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
    assert "/health" in payload["paths"]


@pytest.mark.anyio
async def test_local_health_returns_runtime_status(monkeypatch):
    async with _build_client(monkeypatch) as client:
        response = await client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["api_mode"] == "local"
    assert payload["model_loaded"] is True
    assert "faiss" in payload


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

    assert response.status_code == 202


@pytest.mark.anyio
async def test_local_search_requires_api_key_when_configured(monkeypatch):
    async with _build_client(monkeypatch) as client:
        monkeypatch.setenv("STATSCHAT_API_KEY", "secret")
        missing = await client.get("/search", params={"q": "Population"})
        allowed = await client.get(
            "/search", params={"q": "Population"}, headers={"X-API-Key": "secret"}
        )

    assert missing.status_code == 401
    assert allowed.status_code == 200


@pytest.mark.anyio
async def test_local_temporal_query_overrides_latest_filter(monkeypatch):
    main_api_local = _load_main_api_local()

    class DummyTokenizer:
        pass

    class DummyModel:
        pass

    main_api_local.MODEL = DummyModel()
    main_api_local.TOKENIZER = DummyTokenizer()
    captured: dict[str, object] = {}

    class DummyRetriever:
        def retrieve_documents(self, _question, *, latest_filter=True, **_kwargs):
            captured["latest_filter"] = latest_filter
            return (
                [
                    {
                        "page_content": "context one",
                        "page_url": "https://example.com/one",
                        "title": "Publication One",
                        "score": 0.1,
                    }
                ],
                bool(latest_filter),
                0.1,
            )

        def select_generation_documents(self, _query, docs, **_kwargs):
            return docs[:1]

    monkeypatch.setattr(main_api_local, "get_retriever", lambda: DummyRetriever())
    monkeypatch.setattr(main_api_local, "get_latest_flag", lambda *_a, **_k: 1)
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
    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as client:
        response = await client.get(
            "/search",
            params={
                "q": "What was Kenya's GDP growth rate in Quarter 3 of 2023?",
                "content_type": "latest",
            },
        )

    assert response.status_code == 200
    assert captured["latest_filter"] is False


@pytest.mark.anyio
async def test_cloud_search_returns_schema(monkeypatch):
    async with _build_cloud_client(monkeypatch) as client:
        response = await client.get("/search", params={"q": "Population"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["question"] == "Population"
    assert payload["answer"] == "Answer"
    assert isinstance(payload["references"], list)
    assert payload["references"][0]["page_url"] == "https://example.com/doc1.pdf#page=2"
    assert payload["references"][0]["title"] == "Doc 1"
    assert payload["content_type"] == "latest"
    assert "debug_response" in payload


@pytest.mark.anyio
async def test_cloud_health_returns_runtime_status(monkeypatch):
    async with _build_cloud_client(monkeypatch) as client:
        response = await client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["api_mode"] == "cloud"
    assert payload["model_loaded"] is True
    assert "faiss" in payload


@pytest.mark.anyio
async def test_cloud_search_debug_false_excludes_debug(monkeypatch):
    async with _build_cloud_client(monkeypatch) as client:
        response = await client.get(
            "/search", params={"q": "Population", "debug": False}
        )

    assert response.status_code == 200
    payload = response.json()
    assert "debug_response" not in payload
