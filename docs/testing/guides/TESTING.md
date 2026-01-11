# Testing Guide

This document outlines the strategy, scope, and execution of tests for `StatsChat-KE`.

## 1. Quick Start

**Prerequisites**: Ensure you have installed the test dependencies.
```bash
pip install -e .[test]
```

**Run All Tests**:
```bash
pytest tests/
```

**Run Specific Categories**:
```bash
pytest tests/unit/        # Fast, isolated tests
pytest tests/integration/ # Slower, tests component interaction
```

## 2. Test Strategy

### Philosophy
Given the experimental nature of this project, testing focuses on **Data Integrity** and **System Stability** rather than 100% code coverage. We verify that data enters the system correctly (Ingestion) and that the system stays up (API).

### Key Test Areas

#### A. Data Ingestion (PDF Processing)
*   **Goal**: Ensure we accurately extract text and metadata from government reports.
*   **Why**: Garbage in, garbage out. If text extraction fails, the LLM has no context.
*   **Key Tests**:
    *   `tests/unit/pdf_processing/`: Verifies `pdf_downloader.py` handles 404s, corrupt files, and correct URL schemas.
    *   `tests/unit/pdf_processing/test_page_splitting.py`: Verifies documents are split correctly by page.

#### B. API & Backend
*   **Goal**: Ensure the FastAPI application handles requests and errors gracefully.
*   **Why**: Users (and frontend apps) need a reliable interface.
*   **Key Tests**:
    *   `tests/integration/test_api_health.py`: checks `/health` endpoint.
    *   `tests/integration/test_api_search.py`: checks `/search` endpoint validations.

#### C. Embeddings (Integration)
*   **Goal**: Ensure the pipeline connects from JSON -> Text Chunks -> Vector Store.
*   **Strategy**: We mock the actual Embedding Model (which is slow/heavy) to test the *flow* of data without incurring the cost of model inference during CI.
*   **Location**: `tests/unit/embedding/test_preprocess_integration.py`.

## 3. Writing New Tests

**Documentation Standard**:
Every new test file or significant test function must include a docstring explaining:
1.  **What** is being tested.
2.  **Why** it is being tested.

**Example**:
```python
def test_search_missing_query():
    """
    Test: POST /search with missing 'query' field.
    Why: Ensures the API returns a helpful 422 error instead of crashing,
         guiding the developer/user to fix their request.
    """
    ...
```

## 4. Troubleshooting Tests
*   **"File not found"**: Ensure you are running `pytest` from the root of the repo (`statschat-ke/`).
*   **"FAISS index missing"**: Integration tests may require a dummy FAISS index. Check `tests/test_data/` fixtures.
