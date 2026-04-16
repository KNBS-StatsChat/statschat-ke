"""End-to-end search UX flow tests against the local FastAPI app.

Starts the local API app in-process with mocked ML dependencies and validates
responses for both latest and all content types.
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

    module_name = "fast_api_main_api_local_e2e"
    sys.modules.pop(module_name, None)

    if "torch" not in sys.modules:
        torch_stub = ModuleType("torch")
        torch_stub.float16 = "float16"
        sys.modules["torch"] = torch_stub

    if "transformers" not in sys.modules:
        transformers_stub = ModuleType("transformers")

        class AutoTokenizer:
            @staticmethod
            def from_pretrained(*_a, **_k):
                return object()

        class AutoModelForCausalLM:
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
    monkeypatch.delenv("STATSCHAT_API_KEY", raising=False)
    monkeypatch.delenv("STATSCHAT_RATE_LIMIT_PER_MINUTE", raising=False)
    main_api_local = _load_main_api_local()

    main_api_local.MODEL = object()
    main_api_local.TOKENIZER = object()

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
async def test_search_latest_and_all_responses(monkeypatch):
    async with _build_client(monkeypatch) as client:
        latest_resp = await client.get(
            "/search", params={"q": "Population", "content_type": "latest"}
        )
        all_resp = await client.get(
            "/search", params={"q": "Population", "content_type": "all"}
        )
        debug_off_resp = await client.get(
            "/search",
            params={"q": "Population", "content_type": "all", "debug": False},
        )
        invalid_type_resp = await client.get(
            "/search", params={"q": "Population", "content_type": "unknown"}
        )

    assert latest_resp.status_code == 200
    latest_payload = latest_resp.json()
    assert latest_payload["content_type"] == "latest"
    assert latest_payload["question"] == "Population"
    assert latest_payload["answer"]
    assert latest_payload["references"] == "https://example.com/one"
    assert latest_payload["relevant_publication_one"] == "Publication One"
    assert latest_payload["relevant_publication_two"] == "Publication Two"
    assert "context_from" in latest_payload
    assert "context_reference" in latest_payload

    assert all_resp.status_code == 200
    all_payload = all_resp.json()
    assert all_payload["content_type"] == "all"
    assert all_payload["question"] == "Population"
    assert all_payload["answer"]
    assert all_payload["references"] == "https://example.com/one"
    assert "context_from" in all_payload
    assert "context_reference" in all_payload

    assert debug_off_resp.status_code == 200
    debug_off_payload = debug_off_resp.json()
    assert debug_off_payload["content_type"] == "all"
    assert debug_off_payload["question"] == "Population"
    assert debug_off_payload["answer"]

    assert invalid_type_resp.status_code == 200
    invalid_payload = invalid_type_resp.json()
    assert invalid_payload["content_type"] == "latest"
