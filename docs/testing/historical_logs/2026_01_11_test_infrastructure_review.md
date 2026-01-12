# Test Infrastructure Overhaul & API Coverage Report
**Updated**: 12 January 2026 (targeted coverage additions)
**Scope**: Documentation Restructuring & Integration Test Implementation

## 1. Executive Summary
This report details the work undertaken to modernize the project's testing infrastructure. The primary goals were to:
1.  **Clarify Documentation**: Separate "how to run the app" from "how to test the app".
2.  **Close Coverage Gaps**: Implement the first set of Integration Tests for the FastAPI backend, ensuring the web server and search logic are verifiable.
3.  **Fix Regressions**: Repair existing integration tests for the Embedding Pipeline.
4.  **(Update)** Add minimal, high-ROI tests for API fallbacks, ingestion utilities, and generative helpers while keeping runtime and dependencies light.

All tests are now passing (`pytest tests/`).

---

## 2. Documentation Architecture Changes

### Rationale
Previous documentation mixed operational instructions (page ranges, config settings) with testing commands, making it hard for new developers to find what they needed.

### Changes Implemented
| Old File | New Location | Description |
| :--- | :--- | :--- |
| `development_and_testing.md` | `docs/OPERATING_MANUAL.md` | Dedicated guide for **Running the App**. Covers `main.toml` settings, SETUP vs UPDATE modes, and manual scraping workflows. |
| `testing_guide.md` | `docs/testing/guides/TESTING.md` | Dedicated guide for **Verifying the App**. Covers test strategy, commands, and troubleshooting. |
| `phaseX_....md` | `docs/testing/historical_logs/` | Moved all historical phase reports to a subdirectory to de-clutter the main folder. |

---

## 3. Test Implementation Details

### A. API Health Check
**File**: `tests/integration/test_api_health.py`

*   **Objective**: Verify the FastAPI application starts correctly and routing is functional.
*   **Logic Tested**:
    *   `GET /`: The application is configured to redirect root requests to the OpenAPI docs. The test validates a **307 Redirect** to `/openapi.json`.
*   **Why**: This serves as a "Smoke Test". If the app fails to import (e.g., missing dependencies, syntax errors in `main_api_local.py`), this test will fail immediately.

### B. API Search Logic
**File**: `tests/integration/test_api_search.py`

*   **Objective**: Verify the `/search` endpoint validates inputs and correctly structures the complex JSON response.
*   **Mocking Strategy**: Since the app uses large LLM models (Mistral-7B) and Vector DBs (FAISS), testing with real components is too slow and resource-heavy for CI.
    *   **Solution**: We use `unittest.mock.patch` to mock `statschat.generative.local_llm` functions.
    *   **Mocked Components**: `similarity_search` (Retriever), `generate_response` (LLM), and (Update) `AutoTokenizer`/`AutoModelForCausalLM` to prevent model downloads during tests.

*   **Scenarios Covered**:
    1.  **Happy Path (Full RAG)**: Simulates a successful retrieval and generation.
        *   *Test Data*: Mocked documents with title, content, and URL.
        *   *Validation*: Ensures the API response contains `answer`, `references`, and `context_from` keys.
    2.  **Input Validation**:
        *   Missing `q` parameter $\to$ **422 Unprocessable Entity**.
        *   Empty string `q=""` $\to$ **422 Unprocessable Entity** (verifies custom business logic).
    3.  **(Update) Error Paths**:
        *   Invalid `content_type` gracefully falls back to `"latest"`.
        *   `/feedback` endpoint accepts documented payload and returns **202**.

### C. Embedding Pipeline Maintenance
**File**: `tests/unit/embedding/test_preprocess_integration.py`

*   **Issue**: The existing test `test_update_mode_uses_latest_directories` was failing due to a mismatch between how the test created dummy directories (`latest_/json`) and how the app expected them (`latest_json`).
*   **Fix**: Updated the test setup to mirror the production directory structure perfectly. This ensures our "UPDATE" mode logic is correctly verified.

### D. Generative Logic
**File**: `tests/unit/generative/test_prompts.py`

*   **Objective**: Verify that LLM prompt templates (`prompts_local.py` and `prompts_cloud.py`) maintain structural integrity.
*   **Why**: Prompts are code. A mismatch between the template variables (e.g., `{question}` vs `{QuestionPlaceholder}`) and the formatting logic can cause silent runtime failures or hallucinations.
*   **Logic Tested**:
    *   Verifies that Local and Cloud prompts expect the correct input variables.
    *   Validates variable injection (formatting).
    *   Checks RAG document tag structure (`<Doc1>...`).

### E. Ingestion Utility Hardening (Update)
**Files**: `tests/unit/pdf_processing/test_merge_database_files.py`, `tests/unit/pdf_processing/test_pdf_to_json.py`

*   **Objective**: Cover lightweight but high-risk behaviors in ingestion glue code without touching real data.
*   **Logic Tested**:
    *   `merge_database_files.py`: Moves from `latest_*` directories into canonical locations and merges `url_dict.json` entries without leaving artifacts.
    *   `pdf_to_json.extract_pdf_creation_date`: Prefers metadata dates, falls back to filename years, and only uses the current date as a last resort (with a counter increment).

### F. Generative Helper Regression (Update)
**Files**: `statschat/generative/utils.py`, `tests/unit/generative/test_utils.py`

*   **Objective**: Ensure deduplication logic actually removes duplicates before downstream scoring/highlighting.
*   **Change**: Fixed `deduplicator` to record seen signatures and added a regression test to confirm first-occurrence preservation.

---

## 4. Verification

The full test suite was executed to confirm stability.

**Command**:
```bash
pytest tests/
```

**Result**:
- **PASSED**: 37 tests
- **SKIPPED**: 2 tests
- **FAILED**: 0

**Update (targeted additions)**:
```bash
pytest tests/unit/generative/test_utils.py \
       tests/unit/pdf_processing/test_pdf_to_json.py \
       tests/unit/pdf_processing/test_merge_database_files.py \
       tests/integration/test_api_search.py -q
```
Result: **10 passed** in ~5s (warnings only from upstream swig deps); confirms new coverage without heavy dependencies or model downloads.

## 5. Future Considerations

### End-to-End (E2E) Ingestion
Full pipeline tests (running `pdf_runner.py` from download to vectorization) are **excluded** from this test suite.
*   **Reason**: These processes require downloading GBs of PDFs and loading heavy ML models (FAISS indices, Mistral weights).
*   **Strategy**: E2E testing should be performed on a dedicated build server or via manual periodic runs, rather than on every commit.

### Model Quality Evaluation
This test suite validates code correctness, not AI intelligence.
*   **Scope**: Tests verify the *plumbing* (data flows, API responses, prompt formatting).
*   **Quality**: Qualitative evaluation (e.g., "Is the answer accurate and helpful?") is handled by the separate `statschat/model_evaluation` pipeline using "LLM-as-a-judge" techniques.

The codebase is now stable with documented test coverage for the API layer and critical logic.
