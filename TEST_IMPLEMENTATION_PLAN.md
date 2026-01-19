# Test Implementation Plan

This document outlines the roadmap for verifying the `StatsChat-KE` application. It details the restructuring of documentation and the implementation of critical missing tests.

## Phase 1: Documentation Restructuring

The goal is to separate "How to operate the system" from "How to test the system".

### 1. Create `docs/OPERATING_MANUAL.md`
*   **Source**: Migrated content from `docs/testing/development_and_testing.md`.
*   **Content**:
    *   Instructions for `SETUP` vs `UPDATE` modes in `main.toml`.
    *   Guide to scraping specific page ranges.
    *   Explanation of the "Merge-and-Move" update strategy.
*   **Action**: Create new file, migrate relevant sections, delete `development_and_testing.md`.

### 2. Create `docs/TESTING.md`
*   **Source**: Authentrated content from `docs/testing/testing_guide.md` + new execution instructions.
*   **Content**:
    *   **Test Strategy**: High-level goals (Data Integrity, API Stability).
    *   **Quick Start**: Commands to run the suite (`pytest tests/`).
    *   **Inventory**: Description of where tests live (`tests/unit`, `tests/integration`).
    *   **Troubleshooting**: Common issues (missing FAISS index, etc.).
*   **Action**: Create new file, migrate "Strategy" sections from `testing_guide.md`, add technical run instructions, delete `testing_guide.md`.

## Phase 2: Test Suite Remediation

The analysis identified that the API tests are defined but empty.

**Documentation Standard**: Every new test file or major test function must include a detailed docstring explaining:
1.  **What** is being tested (specific feature/scenario).
2.  **Why** it is being tested (risk mitigation/user requirement).

### 1. Implement API Health Check
*   **Target**: `tests/integration/test_api_health.py`
*   **Current State**: Empty file.
*   **Requirement**:
    *   Test `GET /health` (or equivalent root endpoint).
    *   Assert status code 200.
    *   Assert JSON response `{"status": "ok"}` (or similar).

### 2. Implement Search Endpoint Tests
*   **Target**: `tests/integration/test_api_search.py` (New File)
*   **Requirement**:
    *   Test `POST /search` (or `/ask`).
    *   **Happy Path**: A valid query returns a 200 OK and a structure containing `answer` and `sources`.
    *   **Error Handling (User Input)**:
        *   Missing `query` field.
        *   Empty string query.
        *   Validates the API returns 400 or 422 errors gracefully.
    *   **Dependencies**: These tests likely require mocking the `Inquirer` class to avoid hitting the real LLM or FAISS index during CI.

### 3. Fix Documentation Paths
*   **Issue**: `testing_guide.md` references `tests/e2e/test_page_splitting.py` which does not exist.
*   **Fix**: Update reference to the actual location: `tests/unit/pdf_processing/test_page_splitting.py`.

## Phase 3: Verification
1.  Run `pytest tests/` to ensure all tests (legacy + new) pass.
2.  Verify `docs/` folder is clean and organized.
