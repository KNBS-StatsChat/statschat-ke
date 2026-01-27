"""End-to-end smoke tests for the cloud FastAPI app.

Loads the cloud API in-process with a stubbed provider to avoid network/API
credentials and verifies /search and /feedback responses. It also checks
OpenAPI exposure, root redirects, debug behavior, and content-type fallback.
"""

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import httpx
import pytest


def _load_main_api_cloud(monkeypatch):
    repo_root = Path(__file__).resolve().parents[2]
    api_path = repo_root / "fast-api" / "main_api_cloud.py"

    module_name = "fast_api_main_api_cloud_e2e"
    sys.modules.pop(module_name, None)

    class DummyInquirer:
        def __init__(self, **_kwargs):
            pass

        def make_query(self, question, latest_filter, latest_weight):
            class DummyResponse:
                def __init__(self):
                    self.raw = "debug"

            return ["doc1", "doc2"], "Answer", DummyResponse()

    sys.modules.pop("statschat.generative.cloud_llm", None)
    cloud_llm_stub = ModuleType("statschat.generative.cloud_llm")
    cloud_llm_stub.Inquirer = DummyInquirer
    sys.modules["statschat.generative.cloud_llm"] = cloud_llm_stub

    import statschat

    monkeypatch.setattr(
        statschat,
        "load_config",
        lambda name="main": {
            "db": {},
            "search": {"provider": "stub"},
            "app": {"latest_max": 1},
        },
    )

    spec = importlib.util.spec_from_file_location(module_name, api_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _build_cloud_client(monkeypatch):
    main_api_cloud = _load_main_api_cloud(monkeypatch)
    transport = httpx.ASGITransport(app=main_api_cloud.app)
    return httpx.AsyncClient(transport=transport, base_url="http://testserver")


@pytest.mark.anyio
async def test_cloud_search_and_feedback(monkeypatch):
    async with _build_cloud_client(monkeypatch) as client:
        root_resp = await client.get("/", follow_redirects=False)
        openapi_resp = await client.get("/openapi.json")
        search_resp = await client.get("/search", params={"q": "Population"})
        debug_off_resp = await client.get(
            "/search", params={"q": "Population", "debug": False}
        )
        invalid_type_resp = await client.get(
            "/search", params={"q": "Population", "content_type": "unknown"}
        )
        feedback_resp = await client.post(
            "/feedback",
            json={
                "rating": "1",
                "rating_comment": "Helpful",
                "question": "Population",
                "content_type": "latest",
                "answer": "Answer",
            },
        )

    assert root_resp.status_code == 307
    assert root_resp.headers["location"] == "/openapi.json"

    assert openapi_resp.status_code == 200
    openapi_payload = openapi_resp.json()
    assert "/search" in openapi_payload["paths"]
    assert "/feedback" in openapi_payload["paths"]

    assert search_resp.status_code == 200
    payload = search_resp.json()
    assert payload["question"] == "Population"
    assert payload["content_type"] == "latest"
    assert payload["answer"] == "Answer"
    assert payload["references"] == ["doc1", "doc2"]
    assert "debug_response" in payload

    assert debug_off_resp.status_code == 200
    debug_payload = debug_off_resp.json()
    assert "debug_response" not in debug_payload

    assert invalid_type_resp.status_code == 200
    invalid_payload = invalid_type_resp.json()
    assert invalid_payload["content_type"] == "latest"

    assert feedback_resp.status_code == 202
