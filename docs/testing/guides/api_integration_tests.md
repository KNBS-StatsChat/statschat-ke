# API Integration Tests

These tests validate the FastAPI service contract (request/response behavior) without loading heavyweight dependencies (FAISS indexes, embedding models, or LLMs).

## Where the Tests Live

- `tests/integration/test_api_health.py`
- `tests/integration/test_api_search.py`
- `tests/integration/test_api_cloud.py`

## What These Tests Protect

- Basic service availability ("does the StatsChat FastAPI service start and route requests?")
- Endpoint contract behavior (status codes, required params, default fallbacks)
- Error/fallback handling that should *not* require real vector stores or model downloads

## How the Tests Work (Maintainership Notes)

### Importing the App

The API code lives under `fast-api/` (hyphenated directory name), which cannot be imported as a normal Python package.
Integration tests therefore load the FastAPI app using dynamic import (`importlib.util.spec_from_file_location`).

If you move/rename API entrypoints, update the file-path imports in:
- `tests/integration/test_api_health.py`
- `tests/integration/test_api_cloud.py`

### Mocking Heavy Dependencies

- `tests/integration/test_api_cloud.py` patches the cloud inquirer (LLM + retrieval entrypoint) so requests exercise the route code but avoid FAISS/LLM downloads.
- Keep mocks focused on *inputs/outputs* (what the route expects) rather than implementation details.

## How to Run

```bash
# Run all API integration tests
pytest tests/integration/ -v

# Run a single file
pytest tests/integration/test_api_cloud.py -v

# Run a single test
pytest tests/integration/test_api_cloud.py::test_search_handles_empty_results -v
```

## When to Update These Tests

Update/add integration tests when:
- request/response schemas change (including defaults)
- endpoints change paths, query params, or status codes
- fallback behavior is added (e.g., unknown `content_type`)

Keep these tests “contract-first”: they should explain expected behavior clearly and avoid depending on local `data/` state.
