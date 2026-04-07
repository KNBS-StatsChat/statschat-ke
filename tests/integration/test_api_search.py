"""
Integration tests for API Search Endpoint.

Purpose:
    Ensures the /search endpoint validates inputs and returns structured responses.
    Critically, it MOCKS the actual LLM/RAG engine to verify API logic
    without needing a real vector store or GPU.

Why:
    - Validates Request/Response schemas.
    - Checks error handling for missing/invalid queries.
    - Ensures integration with the `statschat` package logic without heavy dependencies.
"""

from unittest.mock import patch

import httpx
import pytest
import sys
import os
import importlib.util

# Path setup (same as health check)
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import app dynamically due to 'fast-api' hyphen
spec = importlib.util.spec_from_file_location(
    "main_api_local", os.path.join(project_root, "fast-api", "main_api_local.py")
)
main_api_local = importlib.util.module_from_spec(spec)  # noqa: E402
# Register in sys.modules so patch() can find 'main_api_local'
sys.modules["main_api_local"] = main_api_local
spec.loader.exec_module(main_api_local)
app = main_api_local.app


@pytest.fixture
async def client():
    main_api_local.MODEL = object()
    main_api_local.TOKENIZER = object()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as async_client:
        yield async_client


@pytest.fixture
def mock_llm_logic():
    """
    Mocks the `similarity_search` and `generate_response` functions from local_llm.py.
    This prevents the test from needing a real vector DB or LLM model.
    """
    # Note: We patch 'main_api_local' directly because that's where the functions are imported into
    # However, depending on import style, we might need to patch 'statschat.generative.local_llm'
    # The api imports: from statschat.generative.local_llm import similarity_search, ...
    # So we should patch where they are defined OR where they are used if imported via 'from x import y'.
    # Patching where they are USED (in main_api_local namespace) is safer if `from` import was used.

    # Since main_api_local is imported dynamically as a module named 'main_api_local', we patch that.

    with (
        patch("main_api_local.similarity_search") as mock_sim,
        patch("main_api_local.generate_response") as mock_gen,
        patch("main_api_local.format_response") as mock_fmt,
        patch("main_api_local.AutoTokenizer") as mock_tokenizer,
        patch("main_api_local.AutoModelForCausalLM") as mock_model,
    ):

        # Mock returns
        # App expects list of dicts with 'page_content', 'page_url', 'title'
        mock_sim.return_value = [
            {
                "page_content": "doc1 source text",
                "page_url": "http://knbs.or.ke/doc1.pdf",
                "title": "Economic Survey 2023",
            },
            {
                "page_content": "doc2 source text",
                "page_url": "http://knbs.or.ke/doc2.pdf",
                "title": "Economic Survey 2022",
            },
        ]
        mock_gen.return_value = "Inflation is high."
        mock_fmt.return_value = {
            "answer": "Inflation is high.",
            "references": ["doc1"],
            "most_likely_answer": "Inflation is high.",
            "where_context_from": "Section 1",
            "context_reference": "Page 1",
        }

        # Stub out heavy model/tokenizer loading to avoid downloads
        mock_tokenizer.from_pretrained.return_value = object()
        mock_model.from_pretrained.return_value = object()

        yield {"search": mock_sim, "generate": mock_gen, "format": mock_fmt}


@pytest.mark.anyio
async def test_search_endpoint_happy_path(client, mock_llm_logic):
    """
    Test GET /search with valid query.
    """
    response = await client.get("/search", params={"q": "What is inflation?"})

    assert response.status_code == 200
    data = response.json()
    # Based on main_api_local logic, it returns what format_response returns
    assert data["answer"] == "Inflation is high."


@pytest.mark.anyio
async def test_search_endpoint_uses_reference_from_selected_context(
    client, mock_llm_logic
):
    mock_llm_logic["format"].return_value = {
        "answer": "Inflation is high.",
        "references": ["doc2"],
        "most_likely_answer": "Inflation is high.",
        "where_context_from": "Context2",
        "context_reference": "Page 2",
    }

    response = await client.get("/search", params={"q": "What is inflation?"})

    assert response.status_code == 200
    data = response.json()
    assert data["references"] == "http://knbs.or.ke/doc2.pdf"


@pytest.mark.anyio
async def test_search_endpoint_missing_query(client):
    """
    Test GET /search without 'q' param.
    Why: FastAPI requires 'q', so this should fail validation.
    """
    response = await client.get("/search")
    assert response.status_code == 422


@pytest.mark.anyio
async def test_search_endpoint_empty_query_string(client):
    """
    Test GET /search with empty 'q' string.
    Why: The code explicitly checks if question in ["None", ""] -> raise HTTPException(422).
    """
    response = await client.get("/search", params={"q": ""})
    assert response.status_code == 422
    assert response.json()["detail"] == "Empty question"


@pytest.mark.anyio
async def test_search_endpoint_invalid_content_type_falls_back_to_latest(
    client, mock_llm_logic
):
    """
    Test GET /search with an invalid content_type; should fall back to 'latest'.
    """
    response = await client.get(
        "/search", params={"q": "What is GDP?", "content_type": "invalid"}
    )
    assert response.status_code == 200
    assert response.json()["content_type"] == "latest"


@pytest.mark.anyio
async def test_feedback_endpoint_accepts_payload(client):
    """
    Test POST /feedback accepts the documented payload and returns 202.
    """
    payload = {
        "rating": 1,
        "rating_comment": "Useful",
        "question": "Q?",
        "content_type": "latest",
        "answer": "A",
    }
    response = await client.post("/feedback", json=payload)
    assert response.status_code == 202
    assert response.json() == ""
