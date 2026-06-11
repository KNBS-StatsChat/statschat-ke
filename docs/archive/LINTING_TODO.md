# Linting & Refactoring TODOs

This document tracks linting issues and refactoring tasks deferred during the initial pre-commit hook setup (Dec 2025).

## High Priority (Complexity)
- [ ] **Refactor `statschat/pdf_processing/pdf_downloader.py`**
    - **Issue:** `C901 'main' is too complex (18)`
    - **Action:** Break the `main` function into smaller helper functions to reduce cyclomatic complexity.

## Medium Priority (Line Lengths)
The following files have `E501 line too long` errors (> 88 characters). These need to be manually wrapped or refactored.

- [ ] `statschat/embedding/latest_updates.py`
- [ ] `statschat/generative/cloud_llm.py`
- [ ] `statschat/generative/local_llm.py`
- [ ] `statschat/generative/utils.py`
- [ ] `statschat/pdf_processing/pdf_to_json.py`
- [ ] `tests/unit/pdf_processing/evaluate_pdf_text_extraction.py` (Many instances)
- [ ] `tests/unit/pdf_processing/page_splitting_test_functions.py` (Many instances)
- [ ] `tests/unit/pdf_processing/test_pdf_downloader.py` (Many instances)
