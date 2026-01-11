# Phase 2: API Stability & Error Handling

**Date**: January 9, 2026
**Status**: ✅ Complete

## Overview

Phase 2 focused on implementing the missing Integration Testing layer for the API backend (`fast-api/main_api_local.py`). Previously, the project lacked any automated verification that the server endpoints were reachable or functioned correctly.

## Changes Summary

### 1. Implemented Health Check Test
**File**: `tests/integration/test_api_health.py`

**What was done**:
- Created a test client using `fastapi.testclient`.
- Added a test for the root endpoint `/`.
- **Reasoning**: The root endpoint is the entry point. In `main_api_local.py`, this redirects to swagger docs. Testing this verifies the web server application initializes correctly without crashing on startup (which catches import errors, config errors, etc.).

### 2. Implemented Search Endpoint Test
**File**: `tests/integration/test_api_search.py`

**What was done**:
- Created a suite of tests for `GET /search`.
- **Mocking Strategy**: Used `unittest.mock.patch` to bypass the `local_llm` and FAISS logic.
    - *Why?* We want to test the *API Contract* (inputs/outputs), not the *LLM Performance* (which is slow and requires heavy models). Mocking ensures these tests run in milliseconds rather than seconds/minutes.
- **Coverage**:
    1.  **Happy Path**: Verifies that a valid `q` parameter returns a 200 OK and the expected JSON structure.
    2.  **Input Validation**: Verifies that missing `q` param returns 422 (FastAPI standard).
    3.  **Business Logic Error**:
        - The code has a custom check: `if question in [None, "None", ""]`.
        - Added `test_search_endpoint_empty_query_string` specifically to verify this raises HTTP 422 as coded.

## Justification of Strategy

- **Why separate integration tests?**
  Unit tests cover internal logic (PDF parsing). Integration tests cover "The Application" as a user sees it. Without these, we could have perfect PDF parsing but a broken web server.

- **Why mock the LLM?**
  Including the actual LLM in API tests would make the CI pipeline extremely heavy (requiring GBs of RAM and model downloads). By mocking, we ensure the *API code* is correct. The quality of answers is a separate concern (System Evaluation), not API Testing.
